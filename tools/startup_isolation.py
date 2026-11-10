"""Own covered startup audio and input until the launcher acknowledges handoff."""
from __future__ import annotations

import ctypes as c
from ctypes import wintypes as w
from dataclasses import asdict, dataclass
import os
from pathlib import Path
import subprocess
import threading
import time

import psutil

from modpack.config import OW_SHA256, local_path, read_json, sha256, write_json
from startup_core_audio import AudioError, CoreAudio


JOURNAL = 'data/runtime/startup-isolation.json'
WINDOW_PROPERTY = 'OWMC.StartupInput.v1'
CLASSES = {'ow': 'TankWindowClass', 'mc': 'GLFW30'}


@dataclass(frozen=True)
class Target:
    role: str
    pid: int
    created: float
    executable: str

    def path_matches(self, paths):
        if self.role == 'ow':
            return Path(self.executable) == paths.get('owExecutable')
        java = paths.get('java')
        return self.role == 'mc' and Path(self.executable) in (java, java.with_name('javaw.exe'))

    def matches(self, paths):
        try:
            process = psutil.Process(self.pid)
            if (not self.path_matches(paths) or process.create_time() != self.created
                    or Path(process.exe()).resolve() != Path(self.executable) or not process.is_running()):
                return False
            if self.role == 'mc':
                args = process.cmdline() or []
                return Path(args[args.index('--gameDir')+1]).resolve() == paths.get('profile')
            return True
        except (psutil.Error, OSError, ValueError, IndexError):
            return False


class InputWindows:
    def __init__(self):
        from window_layout import user32
        self.user = user32
        self.user.IsWindow.argtypes = [w.HWND]
        self.user.IsWindow.restype = w.BOOL
        self.user.IsWindowEnabled.argtypes = [w.HWND]
        self.user.IsWindowEnabled.restype = w.BOOL
        self.user.EnableWindow.argtypes = [w.HWND, w.BOOL]
        self.user.EnableWindow.restype = w.BOOL
        self.user.GetPropW.argtypes = [w.HWND, w.LPCWSTR]
        self.user.GetPropW.restype = w.HANDLE
        self.user.RemovePropW.argtypes = [w.HWND, w.LPCWSTR]
        self.user.RemovePropW.restype = w.HANDLE

    def belongs(self, handle, target):
        from window_layout import _window_class
        pid = w.DWORD()
        if not self.user.GetWindowThreadProcessId(handle, c.byref(pid)) or pid.value != target.pid:
            return False
        try:
            return _window_class(handle) == CLASSES[target.role]
        except OSError:
            if self.user.IsWindow(handle):
                raise
            return False

    def enabled(self, handle):
        return bool(self.user.IsWindowEnabled(handle))

    def marker(self, handle):
        return self.user.GetPropW(handle, WINDOW_PROPERTY)

    def unmark(self, handle):
        self.user.RemovePropW(handle, WINDOW_PROPERTY)

    def enable(self, handle, enabled):
        self.user.EnableWindow(handle, enabled)
        if self.enabled(handle) != enabled:
            raise RuntimeError('加载期间窗口输入状态回读不一致。')


def native_input_event(pid):
    """Match the existing compositor's event name by PID and exact FILETIME."""
    kernel = c.WinDLL('kernel32', use_last_error=True)
    kernel.OpenProcess.argtypes = [w.DWORD, w.BOOL, w.DWORD]
    kernel.OpenProcess.restype = w.HANDLE
    kernel.GetProcessTimes.argtypes = [w.HANDLE, *([c.POINTER(w.FILETIME)]*4)]
    kernel.GetProcessTimes.restype = w.BOOL
    kernel.CloseHandle.argtypes = [w.HANDLE]
    kernel.CreateEventW.argtypes = [c.c_void_p, w.BOOL, w.BOOL, w.LPCWSTR]
    kernel.CreateEventW.restype = w.HANDLE
    process = kernel.OpenProcess(0x1000, False, pid)  # PROCESS_QUERY_LIMITED_INFORMATION
    if not process:
        raise c.WinError(c.get_last_error())
    try:
        times = [w.FILETIME() for _ in range(4)]
        if not kernel.GetProcessTimes(process, *(c.byref(value) for value in times)):
            raise c.WinError(c.get_last_error())
        stamp = (times[0].dwHighDateTime << 32) | times[0].dwLowDateTime
    finally:
        kernel.CloseHandle(process)
    c.set_last_error(0)
    event = kernel.CreateEventW(None, True, False, f'Local\\OWMCStartupInput_{pid}_{stamp}')
    if not event:
        raise c.WinError(c.get_last_error())
    if c.get_last_error() == 183:
        kernel.CloseHandle(event)
        raise RuntimeError('原版启动输入门已有所有者。')
    return lambda: kernel.CloseHandle(event)


class Lease:
    """Write the baseline before mutation. Only this worker uses live COM references."""
    def __init__(self, paths, windows):
        self.paths, self.windows = paths, windows
        self.path = local_path(paths.root, JOURNAL)
        saved = read_json(self.path) if self.path.exists() else {}
        if saved and saved.get('schemaVersion') != 1:
            raise ValueError('启动隔离回执版本无效。')
        self.audio = list(saved.get('audio', ()))
        self.input = list(saved.get('input', ()))
        self.volumes = {}

    def save(self):
        if self.audio or self.input:
            write_json(self.path, dict(schemaVersion=1, audio=self.audio, input=self.input))
        else:
            self.path.unlink(missing_ok=True)

    def target(self, row):
        target = Target(**row['target'])
        if not target.path_matches(self.paths):
            raise ValueError('启动隔离回执的游戏路径与当前配置不符。')
        return target

    def restore_windows(self):
        # P3 could leave disabled windows after a crash. P4 only undoes old leases.
        for row in self.input[:]:
            target = self.target(row)
            handle, token = row['hwnd'], row['token']
            if self.windows.marker(handle) == token and self.windows.belongs(handle, target):
                if not target.matches(self.paths):
                    continue  # Preserve ownership evidence when identity is temporarily unreadable.
                self.windows.enable(handle, True)
                self.windows.unmark(handle)
            self.input.remove(row)
            self.save()

    @staticmethod
    def key(row):
        return row['device'], row['instance']

    def restore_volume(self, row, volume):
        baseline = row['muteBefore']
        if baseline is not False:  # Originally muted sessions are never owned.
            raise ValueError('无效的启动静音回执。')
        if volume.muted() != baseline:
            volume.mute(baseline)
        self.audio.remove(row)
        self.save()

    def visit_audio(self, session, targets, *, lock):
        pid, single = session.process_id()
        target = targets.get(pid)
        if target and not target.matches(self.paths):
            target = None
        saved = [row for row in self.audio if row['device'] == session.device]
        if not target and not any(row['target']['pid'] == pid for row in saved):
            return
        if not single:
            if target:
                raise RuntimeError('游戏音频会话由多个进程共享，无法单独静音。')
            return
        instance = session.identifier(instance=True)
        if not instance:
            if target:
                raise RuntimeError('游戏音频会话实例标识为空。')
            return
        row = next((row for row in saved if row['instance'] == instance and row['target']['pid'] == pid), None)
        if row and not lock:
            self.target(row)  # Same instance ID is unique even if the old PID has now exited.
            volume = session.volume()
            try:
                self.restore_volume(row, volume)
            finally:
                volume.close()
            return
        if not target or not lock:
            return
        volume = self.volumes.get((session.device, instance)) or session.volume()
        try:
            identifier = session.identifier()
            if not identifier:
                raise RuntimeError('游戏音频会话标识为空。')
            if not row:
                # Windows can carry an expired instance's mute into the next
                # instance. Restore only on the same verified game profile,
                # endpoint and stable session ID, never on a bare reused PID.
                stale = [saved_row for saved_row in saved if saved_row['identifier'] == identifier
                         and saved_row['target']['role'] == target.role
                         and saved_row['target']['executable'] == target.executable
                         and not self.target(saved_row).matches(self.paths)]
                if not stale and volume.muted():
                    return
                row = dict(device=session.device, identifier=identifier, instance=instance,
                           target=asdict(target), muteBefore=False)
                self.audio.append(row)
                for expired in stale:
                    self.audio.remove(expired)
                self.save()
            self.volumes[self.key(row)] = volume
            if not volume.muted():
                volume.mute(True)
        finally:
            if (session.device, instance) not in self.volumes:
                volume.close()

    def restore_audio(self, engine):
        for row in self.audio[:]:
            volume = self.volumes.get(self.key(row))
            if volume:
                try:
                    self.restore_volume(row, volume)
                except AudioError:
                    # A changed/disconnected device can be recovered by a
                    # subsequent enumeration or the persisted receipt.
                    pass
        for session in engine.sessions():
            self.visit_audio(session, {}, lock=False)

    def close_volumes(self):
        for volume in self.volumes.values():
            volume.close()
        self.volumes.clear()


def recover_startup_isolation(paths):
    try:
        _recover_startup_isolation(paths)
    except (OSError, RuntimeError, ValueError) as failure:
        print(f'启动静音或旧窗口状态暂未恢复，保留回执：{failure}', flush=True)


def _recover_startup_isolation(paths):
    if not local_path(paths.root, JOURNAL).is_file():
        return
    from project_launcher import NamedMutex
    mutex = NamedMutex(paths.root, 'startup-isolation')
    if not mutex.acquire():
        return  # A live worker still owns the receipt.
    try:
        lease = Lease(paths, InputWindows())
        lease.restore_windows()
        if lease.audio:
            with CoreAudio() as engine:
                engine.refresh()
                lease.restore_audio(engine)
    finally:
        mutex.close()


class StartupIsolation:
    def __init__(self, paths, ticket=None):
        self.paths = paths
        self.ticket = ticket
        self.targets = {}
        self.lock = threading.Lock()
        self.wake = threading.Event()
        self.stop = threading.Event()
        self.pending = 0
        self.events = []

    def __enter__(self):
        self.thread = threading.Thread(target=self._run, name='owmc-startup-isolation', daemon=True)
        self.thread.start()
        return self

    def spawn(self, command, *, role, **kwargs):
        if self.ticket:
            self.ticket.checkpoint()
        child = subprocess.Popen(command, **kwargs)
        try:
            executable = Path(command[0]).resolve()
            process = psutil.Process(child.pid)
            target = Target(role, child.pid, process.create_time(), str(executable))
            if not target.matches(self.paths) or (role == 'ow' and sha256(executable) != OW_SHA256):
                raise ValueError('进程不符合启动隔离的身份范围。')
            if role == 'ow':
                try:
                    self.events.append(native_input_event(child.pid))
                except (OSError, ValueError) as failure:
                    print(f'启动期间的 OW 输入锁暂不可用，已继续启动：{failure}', flush=True)
            with self.lock:
                self.targets[child.pid] = target
        except (psutil.Error, OSError, ValueError) as failure:
            print(f'启动隔离未接管该进程，已继续启动：{failure}', flush=True)
        self.wake.set()
        return child

    def _run(self):
        from project_launcher import NamedMutex
        mutex = NamedMutex(self.paths.root, 'startup-isolation')
        try:
            if not mutex.acquire():
                raise RuntimeError('已有启动静音或恢复操作。')
            lease = Lease(self.paths, InputWindows())
            lease.restore_windows()
            with CoreAudio(self.wake) as engine:
                try:
                    engine.refresh()
                    lease.restore_audio(engine)
                    next_devices = next_scan = 0
                    while not self.stop.is_set() and (not self.ticket or self.ticket.state() == 'pending'):
                        with self.lock:
                            targets = dict(self.targets)
                        now = time.monotonic()
                        if now >= next_devices:
                            engine.refresh()
                            next_devices = now + .1
                        scan = now >= next_scan
                        for session in engine.sessions(enumerate_all=scan):
                            lease.visit_audio(session, targets, lock=True)
                        if scan:
                            next_scan = now + .1
                        self.wake.wait(.02)
                        self.wake.clear()
                finally:
                    try:
                        lease.restore_audio(engine)
                    finally:
                        self.pending = len(lease.audio) + len(lease.input)
                        lease.close_volumes()
        except Exception as failure:
            print(f'启动静音暂不可用，已继续启动：{failure}', flush=True)
        finally:
            mutex.close()

    def close(self):
        self.stop.set()
        self.wake.set()
        for close_event in self.events:
            close_event()
        self.events.clear()
        self.thread.join(2)
        if self.thread.is_alive():
            print('音频设备恢复仍在后台处理，已保留回执。', flush=True)

    def __exit__(self, *_):
        self.close()
