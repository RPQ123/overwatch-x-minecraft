"""Request identity, progress and presentation evidence for a covered cold start."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import time

import psutil

from modpack.config import local_path, read_json, write_json

LOAD_SECONDS = 180
FRAME_MAX_AGE_MS = 1500
START_ACTIONS = ('start', 'toggle', 'reboot', 'restart')


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
            raise LoadingCancelled('启动等待超过 180 秒。' if state == 'timeout' else '启动加载已取消。')

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
    elif 'mc_world_ready' in events and 'native_weapon_graph_ready' in events:
        step = '正在连接画面'
    elif 'mc_world_ready' not in events:
        step = '正在启动 Minecraft'
        if 'native_spawned' in events and 'native_weapon_graph_ready' not in events:
            step += '  ·  正在载入英雄'
    else:
        step = '正在载入英雄'
    return done, total, step


def matching_timeline(snapshot, request_id):
    timeline = snapshot.get('loadingTimeline') or {}
    return timeline if (timeline.get('request') or {}).get('requestId') == request_id else {}


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
        counters = tuple(report.get(key) for key in ('frames', 'blended', 'unmaskedFrames', 'colorUploads', 'lastMcFrame'))
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
