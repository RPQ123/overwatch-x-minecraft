"""Bounded startup telemetry. Never starts, stops or attaches a game."""
from __future__ import annotations

from contextlib import contextmanager
import json
import os
from pathlib import Path
import re
import sys
import threading
import time
import uuid

REQUEST_ENV = 'OWMC_STARTUP_REQUEST'
LOG_HEADER = b'OWMC startup '
LOG_HEADER_BYTES = 4096


def guest_summary(guest):
    summary = {key: guest.get(key) for key in (
        'sourcePid', 'generation', 'published', 'failed', 'hostPoseConnected', 'hostGeneration', 'hostPoseFlags')}
    return dict(summary, playerAlive=(guest.get('player') or {}).get('alive'))


def compositor_summary(report):
    return {key: report.get(key) for key in (
        'pid', 'probeVersion', 'enabled', 'failures', 'presentOk', 'presentOccluded', 'presentTests',
        'lastPresentHresult', 'frames', 'poses', 'renderThread', 'viewMode', 'cameraCandidateStage',
        'sourceFrames', 'blended', 'colorUploads', 'lastMcFrame', 'lastMcGeneration',
        'coverageRejected', 'heldFrames', 'originalFramesBeforeComposition', 'presentationFps', 'startupInputBlocked')}


def startup_environment(root):
    info = {'root': str(root), 'windowsBuild': None, 'primaryDisplay': None, 'scalePercent': None}
    if os.name != 'nt':
        return info
    import ctypes
    from ctypes import wintypes as w
    from native_display_mode import CURRENT, WinDisplay

    version = sys.getwindowsversion()
    info['windowsBuild'] = f'{version.major}.{version.minor}.{version.build}'
    try:
        mode = WinDisplay().read(CURRENT)
        if mode:
            info['primaryDisplay'] = {'width': mode.width, 'height': mode.height, 'refreshHz': mode.hz}
        user = ctypes.WinDLL('user32')
        user.MonitorFromPoint.argtypes = [w.POINT, w.DWORD]
        user.MonitorFromPoint.restype = w.HANDLE
        monitor = user.MonitorFromPoint(w.POINT(0, 0), 1)
        scaling = ctypes.WinDLL('shcore').GetScaleFactorForMonitor
        scaling.argtypes = [w.HANDLE, ctypes.POINTER(ctypes.c_int)]
        scaling.restype = ctypes.c_long
        percent = ctypes.c_int()
        if monitor and scaling(monitor, ctypes.byref(percent)) == 0:
            info['scalePercent'] = percent.value
    except (OSError, AttributeError, ValueError, RuntimeError):
        pass
    return info


def _header_line(data):
    encoded = LOG_HEADER + json.dumps(data, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
    if len(encoded) >= LOG_HEADER_BYTES:
        base = {key: data.get(key) for key in ('windowsBuild', 'primaryDisplay', 'scalePercent')}
        base.update(root=str(data.get('root', ''))[:384], details='startup-timeline JSON')
        encoded = LOG_HEADER + json.dumps(base, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
    return encoded.ljust(LOG_HEADER_BYTES-1) + b'\n'


def reserve_log_header(path, root):
    try:
        stat = path.stat()
        if stat.st_size:
            return None
        base = startup_environment(root)
        header = _header_line(base)
        try:
            stdout_is_log = os.path.samestat(stat, os.fstat(sys.stdout.fileno()))
        except (AttributeError, OSError, ValueError):
            stdout_is_log = False
        if stdout_is_log:
            sys.stdout.buffer.write(header)
            sys.stdout.flush()
        else:
            with path.open('r+b') as stream:
                stream.write(header)
        return base
    except (OSError, ValueError):
        return None


def update_log_header(path, base, timeline):
    if base is None:
        return
    events = {event.get('name'): event for event in timeline.get('events', ()) if isinstance(event, dict)}
    samples = [events[name] for name in ('compositor_ready', 'loading_presentation_ready', 'loading_presentation_skipped')
               if name in events]
    summary = dict(base, stagesMs=timeline.get('stagesMs', {}), status=timeline.get('status'),
                   totalMs=timeline.get('totalMs'))
    summary['mc'] = events.get('mc_world_ready', {}).get('guest')
    if samples:
        summary.update(mc=samples[-1].get('guest') or summary['mc'], worldLive=samples[-1].get('report'))
    try:
        with path.open('r+b') as stream:
            if stream.read(len(LOG_HEADER)) == LOG_HEADER:
                stream.seek(0)
                stream.write(_header_line(summary))
    except OSError:
        pass  # A viewer can still read the original header and the timeline file.


@contextmanager
def startup_request(root, *, loading=None):
    """Pass the launcher's monotonic origin to its one supervised child."""
    previous = os.environ.get(REQUEST_ENV)
    request = dict(root=str(Path(root).resolve()), requestedNs=time.perf_counter_ns(),
                   requestId=loading.request_id if loading else uuid.uuid4().hex, launcherPid=os.getpid())
    if loading:
        request['covered'] = True
    os.environ[REQUEST_ENV] = json.dumps(request)
    try:
        yield request
    finally:
        if previous is None:
            os.environ.pop(REQUEST_ENV, None)
        else:
            os.environ[REQUEST_ENV] = previous


class StartupTimeline:
    STAGES = {
        'python_spawn': ('startup_requested', 'python_entered'),
        'python_imports': ('python_entered', 'python_imports_ready'),
        'guest_prepare': ('guest_prepare_started', 'guest_prepare_finished'),
        'mc_jvm_boot': ('mc_jvm_spawn_requested', 'fabric_loading'),
        'fabric_mod_loading': ('fabric_loading', 'mc_client_initialized'),
        'mc_resources': ('mc_client_initialized', 'mc_world_load_requested'),
        'mc_world_loading': ('mc_world_load_requested', 'mc_world_ready'),
        'native_process_plugin': ('native_spawn_requested', 'native_client_ready'),
        'native_bootstrap': ('native_bootstrap_started', 'native_bootstrap_finished'),
        'native_hero_spawn': ('native_hero_spawn_started', 'native_hero_spawn_complete'),
        'native_weapon_graph_wait': ('native_weapon_graph_wait_started', 'native_weapon_graph_ready'),
        'compositor_attach': ('compositor_attach_started', 'compositor_ready'),
        'native_observers': ('compositor_ready', 'native_observers_checked'),
    }

    def __init__(self, root, settings, python_entered_ns, imports_ready_ns):
        self.lock = threading.RLock()
        root = Path(root).resolve()
        now = time.perf_counter_ns()
        try:
            request = json.loads(os.environ.get(REQUEST_ENV, '{}'))
            origin = int(request['requestedNs'])
            if (Path(request['root']).resolve() != root
                    or not 0 <= now - origin < 600_000_000_000
                    or origin > python_entered_ns):
                raise ValueError('Unrelated/stale startup request')
        except (ValueError, KeyError, TypeError):
            request = {}
            origin = python_entered_ns
        self.origin = origin
        self.path = root / 'research/launcher' / (
            'startup-timeline-' + time.strftime('%Y%m%d-%H%M%S') + f'-{time.time_ns() % 1_000_000_000:09d}.json')
        if request.get('covered') is True:
            from startup_cover import covered_timeline_path
            self.path = covered_timeline_path(root, request['requestId'])
        self.document = dict(schemaVersion=1, clock='Python perf_counter_ns',
                             originNs=origin, request=request, supervisorPid=os.getpid(),
                             status='starting', events=[],
                             settings={k: settings.get(k) for k in (
                                 'worldName', 'width', 'height', 'shaders', 'renderDistance',
                                 'showMinecraft', 'captureFps', 'hostFps')},
                             logTiming='First observation on monotonic clock; bounded by startup polling and log flushing.')
        self.mark('startup_requested', at_ns=origin)
        self.mark('python_entered', at_ns=python_entered_ns)
        self.mark('python_imports_ready', at_ns=imports_ready_ns)

    def mark(self, name, *, at_ns=None, **evidence):
        with self.lock:
            if any(row['name'] == name for row in self.document['events']):
                return
            stamp = time.perf_counter_ns() if at_ns is None else at_ns
            self.document['events'].append(dict(name=name, elapsedMs=round((stamp-self.origin)/1e6, 3),
                                                monotonicNs=stamp, **evidence))
            self.save()

    def stages(self):
        events = {row['name']: row['elapsedMs'] for row in self.document['events']}
        return {name: round(events[end]-events[start], 3)
                for name, (start, end) in self.STAGES.items() if start in events and end in events}

    def save(self):
        with self.lock:
            self.document['stagesMs'] = self.stages()
            self.path.parent.mkdir(parents=True, exist_ok=True)
            temporary = self.path.with_suffix('.tmp')
            temporary.write_text(json.dumps(self.document, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')
            for attempt in range(12):
                try:
                    temporary.replace(self.path)
                    break
                except PermissionError:
                    if attempt == 11:
                        raise
                    time.sleep(.005)

    def finish(self, status, **evidence):
        with self.lock:
            if self.document['status'] != 'starting':
                return
            self.mark('hero_selection' if status == 'hero-selection' else 'startup_failed', **evidence)
            self.document.update(status=status, totalMs=self.document['events'][-1]['elapsedMs'])
            self.save()

    def summary(self):
        with self.lock:
            return dict(path=str(self.path), status=self.document['status'],
                        elapsedMs=self.document['events'][-1]['elapsedMs'],
                        totalMs=self.document.get('totalMs'), stagesMs=self.stages(),
                        milestonesMs={row['name']:row['elapsedMs'] for row in self.document['events']})


class GuestStartupLog:
    """Read only new launch-log bytes while the existing ready check waits."""
    MARKERS = (
        ('fabric_loading', re.compile(r'Loading Minecraft .*Fabric Loader')),
        ('fabric_mod_inventory', re.compile(r'Loading \d+ mods:')),
        ('mc_client_initialized', re.compile(r'\[OWMCStartup\] client_initialized')),
        ('mc_world_load_requested', re.compile(r'\[OWMCStartup\] world_load_requested')),
        ('mc_spawn_region_preparing', re.compile(r'Preparing start region for dimension')),
        ('mc_first_world_render', re.compile(r'\[OWMCFrames\] Actual world/depth exporter connected')),
    )

    def __init__(self, path, timeline):
        self.path, self.timeline, self.offset, self.pending = Path(path), timeline, 0, b''

    def poll(self):
        if self.timeline is None:
            return
        try:
            with self.path.open('rb') as stream:
                stream.seek(self.offset)
                data = stream.read()
                self.offset = stream.tell()
        except FileNotFoundError:
            return
        lines = (self.pending + data).split(b'\n')
        self.pending = lines.pop()
        for line in lines:
            line = line.decode('utf-8', errors='replace')
            for name, pattern in self.MARKERS:
                if pattern.search(line):
                    self.timeline.mark(name, source='guest launch.log', observed=True)
