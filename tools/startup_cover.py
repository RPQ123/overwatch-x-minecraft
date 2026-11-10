"""Request identity, progress and presentation evidence for a covered cold start."""
from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
import re
import time

import psutil

from modpack.config import local_path, read_json, write_json

LOAD_SECONDS = 360
FRAME_MAX_AGE_MS = 1500
START_ACTIONS = ('start', 'toggle', 'reboot', 'restart')
COVER_STALL_NS = 3_000_000_000


class LoadingCancelled(RuntimeError):
    pass


def covered_timeline_path(root, request_id):
    if not re.fullmatch(r'[0-9a-f]{32}', request_id):
        raise ValueError('加载请求标识无效。')
    return local_path(root, f'research/launcher/startup-timeline-{request_id}.json')


@dataclass(frozen=True)
class LoadingTicket:
    path: Path
    request_id: str
    owner_pid: int
    owner_created: float
    deadline_ns: int

    @staticmethod
    def request_path(root, request_id):
        if not re.fullmatch(r'[0-9a-f]{32}', request_id):
            raise ValueError('加载请求标识无效。')
        return local_path(root, f'research/launcher/loading-{request_id}.json')

    @classmethod
    def create(cls, root, request_id, deadline_ns):
        owner = psutil.Process()
        path = cls.request_path(root, request_id)
        if path.exists():
            raise FileExistsError(path)
        write_json(path, dict(requestId=request_id, ownerPid=owner.pid,
                              ownerCreated=owner.create_time(), deadlineNs=deadline_ns))
        return cls.open(root, request_id)

    @classmethod
    def open(cls, root, request_id):
        path = cls.request_path(root, request_id)
        row = read_json(path)
        if row.get('requestId') != request_id:
            raise ValueError('加载请求身份不匹配。')
        ticket = cls(path, request_id, int(row['ownerPid']), float(row['ownerCreated']), int(row['deadlineNs']))
        if ticket.owner_pid <= 0 or ticket.deadline_ns > time.perf_counter_ns() + LOAD_SECONDS * 10**9:
            raise ValueError('加载请求时限或拥有者无效。')
        return ticket

    @property
    def decision_path(self):
        return self.path.with_suffix('.decision')

    def state(self):
        try:
            decision = self.decision_path.read_text(encoding='ascii')
        except FileNotFoundError:
            decision = ''
        if decision in ('released', 'cancelled'):
            return decision
        if time.perf_counter_ns() >= self.deadline_ns:
            return 'timeout'
        try:
            owner = psutil.Process(self.owner_pid)
            if owner.create_time() == self.owner_created and owner.is_running():
                return 'pending'
        except psutil.Error:
            pass
        return 'cancelled'

    def checkpoint(self):
        state = self.state()
        if state != 'pending':
            raise LoadingCancelled(f'启动等待超过 {LOAD_SECONDS} 秒。' if state == 'timeout' else '启动加载已取消。')

    def finish(self, decision):
        if decision not in ('released', 'cancelled'):
            raise ValueError(decision)
        if decision == 'released':
            self.checkpoint()
        with self.decision_path.open('x', encoding='ascii') as stream:
            stream.write(decision)


def milestones(timeline):
    return {row.get('name') for row in timeline.get('events', ())}


def loading_progress(preflight_ok, timeline):
    events = milestones(timeline)
    checkpoints = (
        'guest_prepare_finished', 'mc_jvm_spawned', 'mc_world_ready',
        'native_spawned', 'native_client_ready', 'native_bootstrap_finished',
        'native_weapon_graph_ready', 'native_observers_ready', 'loading_windows_arranged',
        'loading_presentation_ready',
    )
    total = len(checkpoints) + 1
    done = int(preflight_ok) + sum(name in events for name in checkpoints)
    if not preflight_ok:
        step = '正在检查本地文件'
    elif 'loading_presentation_ready' in events:
        step = '合成画面已连通'
    elif 'loading_presentation_skipped' in events:
        step = '游戏窗口已打开，画面仍在连接'
    elif 'mc_world_ready' in events and 'native_weapon_graph_ready' in events:
        step = '正在连接画面'
    elif 'mc_world_ready' not in events:
        step = '正在启动 Minecraft'
        if 'native_spawned' in events and 'native_weapon_graph_ready' not in events:
            step += '  ·  正在载入英雄'
    else:
        step = '正在载入英雄'
    return done, total, step


def startup_failure_text(detail):
    """Keep diagnostics in the log and show an actionable description in the UI."""
    value = str(detail)
    lower = value.casefold()
    if any(code in lower for code in ('winerror 126', '0xc0000135', 'winerror 14001')):
        return 'Windows 无法加载所需运行库。请重新解压完整包，确认包内 VC++ 运行库未被安全软件隔离。'
    if any(code in lower for code in ('winerror 5]', 'winerror 32', 'permission denied', 'winerror 362', 'winerror 206')):
        return 'Windows 拒绝读取或写入整合包。请检查安全软件记录，把完整包解压到本地可写的较短路径后重试。'
    if any(code in lower for code in ('dxgi_error_device', '0x887a0005', '0x887a0006', '0x887a0007')):
        return '显卡停止响应或驱动重置。请正常结束游戏，确认显卡驱动可用后重试。'
    if 'no completed observation' in lower or 'verifying world-live' in lower:
        return 'OW 未能及时输出画面。请先用启动器正常结束游戏，再重试。若再次出现，请附本次日志。'
    if any('\u4e00' <= char <= '\u9fff' for char in value):
        return value.splitlines()[0]
    if 'waiting for the real saved minecraft world' in lower:
        return 'Minecraft 未在本阶段时限内载入世界。请查看日志并在磁盘空闲后重试。'
    if 'waiting for' in lower:
        return '当前启动阶段等待超时。请正常结束游戏后重试，并保留本次日志。'
    return '游戏启动未完成。请正常结束游戏后重试。详细原因见本次日志。'


def matching_timeline(snapshot, request_id):
    timeline = snapshot.get('loadingTimeline') or {}
    return timeline if (timeline.get('request') or {}).get('requestId') == request_id else {}


def loading_render_samples(build, timeline):
    """Read the current launch's existing native reports on the snapshot worker."""
    events = {row['name']: row for row in timeline.get('events', ())}
    spawn = events.get('native_spawned', {})
    pid, created = spawn.get('pid'), spawn.get('creation')
    if type(pid) is not int or pid <= 0 or not isinstance(created, (float, int)):
        return {}
    if 'compositor_attach_started' in events:
        from native_compositor_version import VERSION as version
        prefix = 'world-live'
    elif 'native_bootstrap_started' in events and 'native_bootstrap_finished' not in events:
        from native_bootstrap_maps import VERSION as version
        prefix = 'session-bootstrap'
    else:
        return {}
    try:
        with (build/f'{prefix}-{pid}.json').open('rb') as stream:
            if os.fstat(stream.fileno()).st_mtime_ns < int(created*1e9):
                return {}
            report = json.loads(stream.read(256*1024))
        if (report.get('pid') == pid and report.get('probeVersion') == version and report.get('failures') == 0):
            return report
    except (OSError, ValueError, TypeError, AttributeError):
        pass  # Missing, locked or malformed telemetry cannot keep the cover indefinitely.
    return {}


class CoverWatchdog:
    """Release only the cosmetic cover. All startup deadlines and owners stay intact."""

    def __init__(self, now_ns):
        self.snapshot_ns = now_ns
        self.progress_ns = now_ns
        self.signal = None

    def reason(self, timeline, report, snapshot_ns, now_ns):
        if type(snapshot_ns) is int and snapshot_ns <= now_ns:
            self.snapshot_ns = max(self.snapshot_ns, snapshot_ns)
        if now_ns - self.snapshot_ns >= COVER_STALL_NS:
            return '启动状态暂未更新'

        events = {row['name']: row['monotonicNs'] for row in timeline.get('events', ())}
        if 'compositor_attach_started' in events:
            count, occluded = report.get('presentOk'), report.get('presentOccluded')
            if report.get('enabled') is True and type(count) is int and count >= 0 and type(occluded) is int:
                if occluded > 0:
                    return f'OW 报告遮挡（presentOccluded={occluded}）'
                if not self.signal or self.signal[0] != 'present' or count > self.signal[1]:
                    self.signal, self.progress_ns = ('present', count), now_ns
            if self.signal and self.signal[0] == 'present':
                if now_ns - self.progress_ns >= COVER_STALL_NS:
                    return f'OW 成功 Present 停滞（presentOk={self.signal[1]}）'
            elif now_ns - events['compositor_attach_started'] >= 2*COVER_STALL_NS:
                return '暂未取得 OW 合成器出画计数'
            observers = events.get('native_observers_ready')
            if observers is not None and 'loading_presentation_ready' not in events and now_ns - observers >= COVER_STALL_NS:
                return '合成帧尚未连通'
        elif 'native_bootstrap_started' in events and 'native_bootstrap_finished' not in events:
            phase = report.get('phase')
            if phase not in (0, 1, 2, 3):
                phase = self.signal[1] if self.signal and self.signal[0] == 'bootstrap' else 0
            if self.signal != ('bootstrap', phase):
                self.signal = ('bootstrap', phase)
                self.progress_ns = now_ns if phase else events['native_bootstrap_started']
            # The original engine deliberately waits 3s before requesting the backing map.
            if phase != 3 and now_ns - self.progress_ns >= (2 if phase in (1, 2) else 1)*COVER_STALL_NS:
                return f'OW 原版场景引导暂未推进（阶段 {phase}）'
        else:
            for start, end, grace in (
                ('loading_native_window_visible', 'native_client_ready', 2),
                ('native_hero_spawn_started', 'native_hero_spawn_complete', 1),
                ('native_weapon_graph_wait_started', 'native_weapon_graph_ready', 1),
            ):
                if start in events and end not in events and now_ns - events[start] >= grace*COVER_STALL_NS:
                    return 'OW 启动阶段暂未推进'
            if ('native_spawned' in events or 'mc_jvm_spawned' in events) and now_ns - max(events.values()) >= 4*COVER_STALL_NS:
                return '游戏加载进度暂未更新'
        return None


def presentation_receipt(snapshot, request_id, now_ms):
    status = snapshot.get('status') or {}
    receipt = status.get('startupPresentation') or {}
    observed = receipt.get('observedMs')
    if (snapshot.get('fresh') and snapshot.get('nativeAlive') and not status.get('error')
            and status.get('phase') in ('hero-selection', 'gameplay')
            and receipt.get('requestId') == request_id and receipt.get('nativePid') == status.get('nativePid')
            and receipt.get('supervisorPid') in snapshot.get('supervisorPids', ())
            and type(observed) is int and 0 <= now_ms - observed <= FRAME_MAX_AGE_MS):
        return receipt
    return None


def generation(value):
    return value & ((1 << 64)-1) if type(value) is int and -(1 << 63) <= value < (1 << 64) else 0


class CompositionGate:
    """Require a fresh, advancing masked composite, from this producer and native camera."""

    def __init__(self):
        self.previous = None

    def observe(self, guest, report, native_pid, guest_pid, now_ms):
        host = generation(report.get('generation'))
        source = generation(guest.get('generation'))
        wall = report.get('sampleWallMs')
        counters = (report.get('presentOk', report.get('frames')),
                    *(report.get(key) for key in ('blended', 'unmaskedFrames', 'colorUploads', 'lastMcFrame')))
        published = guest.get('published')
        if (guest.get('sourcePid') != guest_pid or guest.get('mode') != 'full-world-frame-proof'
                or guest.get('failed') is not False or not (guest.get('player') or {}).get('alive')
                or type(published) is not int or published <= 2
                or not guest.get('hostPoseConnected') or guest.get('hostPoseFlags') != 1
                or not host or generation(guest.get('hostGeneration')) != host
                or not source or generation(report.get('lastMcGeneration')) != source
                or report.get('pid') != native_pid or report.get('enabled') is not True
                or report.get('failures') != 0 or report.get('viewMode') not in (1, 2)
                or type(wall) is not int or not 0 <= now_ms-wall <= FRAME_MAX_AGE_MS
                or any(type(value) is not int or value < 0 for value in counters)):
            self.previous = None
            return None
        frames, blended, unmasked, uploads, frame = counters
        if min(frames, blended, uploads, frame) <= 0:
            self.previous = None
            return None
        scope = (host, source, report['viewMode'])
        previous = self.previous
        self.previous = (scope, wall, frames, blended, unmasked, uploads, frame)
        if previous is None:
            return None
        old_scope, old_wall, old_frames, old_blended, old_unmasked, old_uploads, old_frame = previous
        masked = (blended-old_blended)-(unmasked-old_unmasked)
        if (scope != old_scope or not 0 < wall-old_wall <= FRAME_MAX_AGE_MS or frames <= old_frames
                or not 0 <= unmasked-old_unmasked or masked <= 0 or uploads <= old_uploads or frame <= old_frame):
            return None
        return dict(observedMs=wall, viewMode=report['viewMode'], hostGeneration=host, guestGeneration=source,
                    lastMcFrame=frame, blended=blended, colorUploads=uploads, maskedDelta=masked)
