"""Own/recover only this root's launcher UI; never an action or game process."""
from __future__ import annotations

import ctypes
from ctypes import wintypes as w
import hashlib
import json
import os
from pathlib import Path
import sys
import time

import psutil
from modpack.config import PackPaths, local_path, read_json, write_json

TITLE = '守望先锋 × 我的世界 — 启动器'


def log(root: Path, event: str, **fields):
    path = local_path(root, 'data/tmp/launcher-ui.log')
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('a', encoding='utf-8') as stream:
        stream.write(json.dumps(dict(time=time.time(), pid=os.getpid(), event=event, **fields),
                                ensure_ascii=False) + '\n')


def prefix(root: Path) -> str:
    digest = hashlib.sha256(str(root.resolve()).casefold().encode('utf-8')).hexdigest()[:20]
    return 'Local\\OWMCProjectLauncher-' + digest


class Event:
    def __init__(self, name: str, *, create=False):
        self.kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        self.kernel.CreateEventW.argtypes = [ctypes.c_void_p, w.BOOL, w.BOOL, w.LPCWSTR]
        self.kernel.CreateEventW.restype = w.HANDLE
        self.kernel.OpenEventW.argtypes = [w.DWORD, w.BOOL, w.LPCWSTR]
        self.kernel.OpenEventW.restype = w.HANDLE
        self.kernel.SetEvent.argtypes = [w.HANDLE]; self.kernel.SetEvent.restype = w.BOOL
        self.kernel.WaitForSingleObject.argtypes = [w.HANDLE, w.DWORD]
        self.kernel.WaitForSingleObject.restype = w.DWORD
        self.kernel.CloseHandle.argtypes = [w.HANDLE]; self.kernel.CloseHandle.restype = w.BOOL
        self.handle = (self.kernel.CreateEventW(None, True, False, name) if create else
                       self.kernel.OpenEventW(0x2, False, name))
        if create and not self.handle:
            raise ctypes.WinError(ctypes.get_last_error())

    def signal(self):
        return bool(self.handle and self.kernel.SetEvent(self.handle))

    def requested(self):
        return bool(self.handle and self.kernel.WaitForSingleObject(self.handle, 0) == 0)

    def close(self):
        if self.handle:
            self.kernel.CloseHandle(self.handle)
            self.handle = None


def notify_ready(root: Path):
    name = os.environ.pop('OWMC_LAUNCH_READY_EVENT', '')
    if not name:
        return
    if not name.startswith('Local\\OWMCLauncherReady-') or len(name) > 160:
        raise ValueError('启动器就绪事件格式无效。')
    event = Event(name)
    try:
        log(root, 'ui-ready-notification', delivered=event.signal())
    finally:
        event.close()


class Owner:
    def __init__(self, root: Path):
        self.root = root.resolve()
        self.path = local_path(self.root, 'data/tmp/launcher-ui-owner.json')
        self.created = psutil.Process().create_time()
        name = prefix(self.root) + f'-close-{os.getpid()}-{round(self.created * 1000)}'
        self.event = Event(name, create=True)
        self.record = dict(schemaVersion=1, root=str(self.root), pid=os.getpid(), created=self.created,
                           script=str(self.root / 'tools/project_launcher.py'), closeEvent=name)
        try:
            write_json(self.path, self.record)
        except BaseException:
            self.event.close()
            raise

    def watch(self, window, ui):
        def check():
            if self.event.requested():
                log(self.root, 'normal-close-request')
                ui.close()
                return
            window.after(100, check)
        window.after(100, check)

    def close(self):
        try:
            current = read_json(self.path)
            if current.get('pid') == os.getpid() and current.get('created') == self.created:
                self.path.unlink()
        except (OSError, ValueError):
            pass
        finally:
            self.event.close()


def verified_ui(process, root: Path, interpreters: set[Path], created=None) -> bool:
    """Require the actual script position and GUI-only command line, not a substring."""
    try:
        if process.pid == os.getpid() or not process.is_running():
            return False
        if created is not None and abs(process.create_time() - created) > .001:
            return False
        if Path(process.exe()).resolve() not in interpreters:
            return False
        arguments = process.cmdline()
        index = 1
        while index < len(arguments) and arguments[index] in ('-u', '-B', '-E', '-s'):
            index += 1
        if index != len(arguments) - 1:
            return False  # No --action/--snapshot/-m/-c or script-as-data argument.
        script = Path(arguments[index])
        if not script.is_absolute():
            script = Path(process.cwd()) / script
        return (script.resolve() == root.resolve() / 'tools/project_launcher.py'
                and Path(process.cwd()).resolve() == root.resolve())
    except (psutil.Error, OSError, ValueError, IndexError):
        return False


class Windows:
    def __init__(self):
        self.user = ctypes.WinDLL('user32', use_last_error=True)
        self.callback = ctypes.WINFUNCTYPE(w.BOOL, w.HWND, w.LPARAM)
        self.user.EnumWindows.argtypes = [self.callback, w.LPARAM]
        self.user.EnumWindows.restype = w.BOOL
        self.user.EnumThreadWindows.argtypes = [w.DWORD, self.callback, w.LPARAM]
        self.user.EnumThreadWindows.restype = w.BOOL
        self.user.GetWindowThreadProcessId.argtypes = [w.HWND, ctypes.POINTER(w.DWORD)]
        self.user.GetWindowThreadProcessId.restype = w.DWORD
        self.user.IsWindowVisible.argtypes = [w.HWND]; self.user.IsWindowVisible.restype = w.BOOL
        self.user.ShowWindow.argtypes = [w.HWND, ctypes.c_int]
        self.user.SetForegroundWindow.argtypes = [w.HWND]
        self.user.PostMessageW.argtypes = [w.HWND, w.UINT, w.WPARAM, w.LPARAM]
        self.user.PostMessageW.restype = w.BOOL
        self.dwm = ctypes.WinDLL('dwmapi', use_last_error=True)
        self.dwm.DwmGetWindowAttribute.argtypes = [w.HWND, w.DWORD, ctypes.c_void_p, w.DWORD]
        self.dwm.DwmGetWindowAttribute.restype = ctypes.c_long

    def _belongs(self, handle, pid):
        owner = w.DWORD()
        self.user.GetWindowThreadProcessId(handle, ctypes.byref(owner))
        return owner.value == pid

    def visible(self, pid):
        handles = []
        errors = []
        @self.callback
        def collect(handle, _):
            try:
                if self._belongs(handle, pid) and self.user.IsWindowVisible(handle):
                    cloaked = w.DWORD()
                    result = self.dwm.DwmGetWindowAttribute(handle, 14, ctypes.byref(cloaked), ctypes.sizeof(cloaked))
                    if result != 0 or not cloaked.value:
                        handles.append(int(handle))
                return True
            except Exception as error:
                errors.append(error)
                return False
        ctypes.set_last_error(0)
        success = self.user.EnumWindows(collect, 0)
        error = ctypes.get_last_error()
        if errors:
            raise errors[0]
        if not success and error:
            raise ctypes.WinError(error)
        return handles  # EnumWindows enumerates this desktop, not another desktop's UI.

    def activate(self, pid, handle):
        if self._belongs(handle, pid) and self.user.IsWindowVisible(handle):
            self.user.ShowWindow(handle, 9)
            self.user.SetForegroundWindow(handle)
            return True
        return False

    def close_windows(self, process):
        handles = set()
        @self.callback
        def collect(handle, _):
            if self._belongs(handle, process.pid):
                handles.add(int(handle))
            return True
        for thread in process.threads():
            self.user.EnumThreadWindows(thread.id, collect, 0)
        for handle in handles:
            if self._belongs(handle, process.pid):
                self.user.PostMessageW(handle, 0x10, 0, 0)  # WM_CLOSE, including legacy Tk.


def launch_wrappers(candidates):
    """Do not confuse this launch's own venv parent with a stale UI either."""
    try:
        current = psutil.Process()
        executable = Path(current.exe()).resolve()
        tail = current.cmdline()[1:]
        ancestors = {process.pid for process in current.parents()}
        return {process.pid for process in candidates if process.pid in ancestors
                and Path(process.exe()).resolve() != executable and process.cmdline()[1:] == tail}
    except (psutil.Error, OSError, ValueError):
        return set()


def close_invisible(root, process, interpreters, windows, *, grace=2.0):
    created = process.create_time()
    if not verified_ui(process, root, interpreters, created) or windows.visible(process.pid):
        return False
    try:
        record = read_json(local_path(root, 'data/tmp/launcher-ui-owner.json'))
        expected = prefix(root) + f'-close-{process.pid}-{round(created * 1000)}'
        if (record.get('pid') == process.pid and record.get('created') == created
                and record.get('root') == str(root.resolve()) and record.get('closeEvent') == expected):
            event = Event(expected)
            try:
                event.signal()
            finally:
                event.close()
    except (OSError, ValueError):
        pass
    windows.close_windows(process)
    try:
        process.wait(timeout=grace)
        log(root, 'old-ui-closed-normally', oldPid=process.pid, created=created)
        return True
    except psutil.TimeoutExpired:
        # A legacy/hung UI cannot consume WM_CLOSE. Recheck immediately before
        # ending only that invisible UI; never terminate its independent children.
        if not verified_ui(process, root, interpreters, created) or windows.visible(process.pid):
            return False
        process.terminate()
        process.wait(timeout=2)
        log(root, 'unresponsive-invisible-ui-ended', oldPid=process.pid, created=created)
        return True
    except psutil.NoSuchProcess:
        return True


def acquire_ui(root: Path, mutex, mutex_factory, *, windows=None, startup_grace=4.0) -> bool:
    if mutex.acquire():
        return True
    root = root.resolve()
    windows = windows or Windows()
    python = PackPaths(root).get('python')
    interpreters = {python.resolve(), Path(sys.executable).resolve(),
                    Path(getattr(sys, '_base_executable', sys.executable)).resolve()}
    recovery = mutex_factory(root, 'ui-recovery')
    try:
        # A finite retry serializes simultaneous desktop double-clicks.
        deadline = time.monotonic() + 6
        while not recovery.acquire():
            if time.monotonic() >= deadline:
                raise RuntimeError('启动器恢复操作尚未完成，请查看 data/tmp/launcher-ui.log。')
            time.sleep(.1)
        if mutex.acquire():
            return True
        candidates = [process for process in psutil.process_iter()
                      if verified_ui(process, root, interpreters)]
        # CPython venv redirectors mirror the script command line but do not
        # execute Tk or own the mutex. Close the actual interpreter first.
        parents = set()
        for process in candidates:
            try:
                parents.add(process.ppid())
            except psutil.Error:
                pass
        parents.update(launch_wrappers(candidates))
        owners = [process for process in candidates if process.pid not in parents]
        for process in owners:
            # Let a just-created UI finish constructing before treating it as stale.
            remaining = min(startup_grace, max(0, startup_grace - (time.time() - process.create_time())))
            startup_deadline = time.monotonic() + remaining
            while True:
                if not verified_ui(process, root, interpreters):
                    break
                handles = windows.visible(process.pid)
                if handles:
                    if windows.activate(process.pid, handles[0]) is not False:
                        log(root, 'existing-visible-ui', oldPid=process.pid)
                        notify_ready(root)
                        return False
                if time.monotonic() >= startup_deadline:
                    break
                time.sleep(.1)
        for process in owners:
            try:
                close_invisible(root, process, interpreters, windows)
            except psutil.NoSuchProcess:
                pass
        deadline = time.monotonic() + 2
        while time.monotonic() < deadline:
            if mutex.acquire():
                log(root, 'ui-mutex-recovered', oldPids=[process.pid for process in owners])
                return True
            time.sleep(.05)
        raise RuntimeError('无法确认旧启动器身份或释放界面锁，未关闭其他进程；详情见 data/tmp/launcher-ui.log。')
    finally:
        recovery.close()
