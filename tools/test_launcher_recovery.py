"""Root-isolated UI recovery fixtures; never use the workspace's UI mutex."""
from __future__ import annotations

import ctypes
from ctypes import wintypes as w
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import Mock, patch
import uuid

import psutil
import project_launcher as launcher
import launcher_ui_owner as owner
from modpack.config import write_json

ROOT = Path(__file__).resolve().parents[1]


class DesktopProcess:
    """Popen's STARTUPINFO ignores lpDesktop; use actual Win32 for this fixture."""
    def __init__(self, command, root, desktop, environment, output):
        import msvcrt
        class Startup(ctypes.Structure):
            _fields_ = [('cb', w.DWORD), ('lpReserved', w.LPWSTR), ('lpDesktop', w.LPWSTR),
                        ('lpTitle', w.LPWSTR), ('dwX', w.DWORD), ('dwY', w.DWORD),
                        ('dwXSize', w.DWORD), ('dwYSize', w.DWORD), ('dwXCountChars', w.DWORD),
                        ('dwYCountChars', w.DWORD), ('dwFillAttribute', w.DWORD),
                        ('dwFlags', w.DWORD), ('wShowWindow', w.WORD), ('cbReserved2', w.WORD),
                        ('lpReserved2', ctypes.POINTER(w.BYTE)), ('hStdInput', w.HANDLE),
                        ('hStdOutput', w.HANDLE), ('hStdError', w.HANDLE)]
        class Process(ctypes.Structure):
            _fields_ = [('hProcess', w.HANDLE), ('hThread', w.HANDLE),
                        ('dwProcessId', w.DWORD), ('dwThreadId', w.DWORD)]
        self.kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        self.kernel.CreateProcessW.argtypes = [w.LPCWSTR, w.LPWSTR, ctypes.c_void_p, ctypes.c_void_p,
            w.BOOL, w.DWORD, ctypes.c_void_p, w.LPCWSTR, ctypes.POINTER(Startup), ctypes.POINTER(Process)]
        self.kernel.CreateProcessW.restype = w.BOOL
        self.kernel.WaitForSingleObject.argtypes = [w.HANDLE, w.DWORD]
        self.kernel.GetExitCodeProcess.argtypes = [w.HANDLE, ctypes.POINTER(w.DWORD)]
        self.kernel.TerminateProcess.argtypes = [w.HANDLE, w.UINT]
        self.kernel.CloseHandle.argtypes = [w.HANDLE]
        startup = Startup()
        startup.cb = ctypes.sizeof(startup)
        startup.lpDesktop = desktop
        startup.dwFlags = 0x100  # STARTF_USESTDHANDLES; no visible console.
        handle = msvcrt.get_osfhandle(output.fileno())
        startup.hStdOutput = startup.hStdError = handle
        block = ctypes.create_unicode_buffer('\0'.join(key + '=' + value for key, value in
            sorted(environment.items(), key=lambda item: item[0].upper())) + '\0\0')
        info = Process()
        os.set_handle_inheritable(handle, True)
        try:
            success = self.kernel.CreateProcessW(command[0], ctypes.create_unicode_buffer(subprocess.list2cmdline(command)),
                None, None, True, subprocess.CREATE_NO_WINDOW | 0x400, block, str(root), ctypes.byref(startup), ctypes.byref(info))
            if not success:
                raise ctypes.WinError(ctypes.get_last_error())
        finally:
            os.set_handle_inheritable(handle, False)
        self.pid, self.handle = info.dwProcessId, info.hProcess
        self.kernel.CloseHandle(info.hThread)

    def poll(self):
        value = w.DWORD()
        if not self.kernel.GetExitCodeProcess(self.handle, ctypes.byref(value)):
            raise ctypes.WinError(ctypes.get_last_error())
        return None if value.value == 259 else value.value

    def wait(self, timeout):
        if self.kernel.WaitForSingleObject(self.handle, round(timeout * 1000)) == 258:
            raise subprocess.TimeoutExpired('isolated desktop fixture', timeout)
        return self.poll()

    def terminate(self):
        self.kernel.TerminateProcess(self.handle, 1)

    def close(self):
        self.kernel.CloseHandle(self.handle)


class IsolatedRoot(unittest.TestCase):
    def setUp(self):
        scratch = ROOT / 'data/tmp'
        scratch.mkdir(parents=True, exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(prefix='c1-recovery-', dir=scratch)
        self.root = Path(self.temporary.name)
        self.addCleanup(self.temporary.cleanup)
        self.python = Path(sys.executable).resolve()
        write_json(self.root / 'config/launcher.json',
                   dict(schemaVersion=1, autoStart=False, paths={'python': str(self.python)}))
        self.assertNotEqual(launcher.NamedMutex(self.root, 'ui').name,
                            launcher.NamedMutex(ROOT, 'ui').name)


class IdentityTests(IsolatedRoot):
    def process(self):
        process = Mock(pid=123456)
        process.exe.return_value = str(self.python)
        process.cwd.return_value = str(self.root)
        process.cmdline.return_value = [str(self.python), '-B', str(self.root / 'tools/project_launcher.py')]
        process.is_running.return_value = True
        process.create_time.return_value = time.time() - 100
        return process

    def test_only_exact_root_gui_command_line_is_eligible(self):
        process = self.process()
        self.assertTrue(owner.verified_ui(process, self.root, {self.python}))
        for arguments in (
            [str(self.python), str(self.root / 'tools/project_launcher.py'), '--action', 'start'],
            [str(self.python), str(self.root / 'tools/project_launcher.py'), '--snapshot'],
            [str(self.python), '-c', str(self.root / 'tools/project_launcher.py')],
            [str(self.python), 'another.py', str(self.root / 'tools/project_launcher.py')],
            [str(self.python), str(self.root / 'other/project_launcher.py')],
        ):
            process.cmdline.return_value = arguments
            self.assertFalse(owner.verified_ui(process, self.root, {self.python}), arguments)

    def test_pid_reuse_refuses_any_close(self):
        process = self.process()
        process.create_time.side_effect = [10, 20]
        windows = Mock()
        self.assertFalse(owner.close_invisible(self.root, process, {self.python}, windows))
        windows.close_windows.assert_not_called()
        process.terminate.assert_not_called()

    def test_visible_ui_is_never_closed(self):
        process = self.process()
        windows = Mock(visible=Mock(return_value=[77]))
        self.assertFalse(owner.close_invisible(self.root, process, {self.python}, windows))
        windows.close_windows.assert_not_called()
        process.terminate.assert_not_called()

    def test_normal_close_does_not_terminate(self):
        process = self.process()
        windows = Mock(visible=Mock(return_value=[]))
        self.assertTrue(owner.close_invisible(self.root, process, {self.python}, windows))
        windows.close_windows.assert_called_once_with(process)
        process.terminate.assert_not_called()

    def test_unresponsive_invisible_gui_rechecks_identity_before_ui_only_termination(self):
        process = self.process()
        process.wait.side_effect = [psutil.TimeoutExpired(2), None]
        windows = Mock(visible=Mock(return_value=[]))
        self.assertTrue(owner.close_invisible(self.root, process, {self.python}, windows, grace=0))
        self.assertEqual(windows.visible.call_count, 2)
        process.terminate.assert_called_once()

    def test_ui_that_becomes_visible_during_close_is_preserved(self):
        process = self.process()
        process.wait.side_effect = psutil.TimeoutExpired(2)
        windows = Mock(visible=Mock(side_effect=[[], [77]]))
        self.assertFalse(owner.close_invisible(self.root, process, {self.python}, windows, grace=0))
        process.terminate.assert_not_called()

    def test_existing_visible_root_ui_is_activated_without_new_owner_or_popup(self):
        process = self.process()
        mutex = Mock(acquire=Mock(return_value=False))
        recovery = Mock(acquire=Mock(return_value=True))
        windows = Mock(visible=Mock(return_value=[77]))
        with patch.object(owner.psutil, 'process_iter', return_value=[process]):
            self.assertFalse(owner.acquire_ui(self.root, mutex, Mock(return_value=recovery),
                                              windows=windows, startup_grace=0))
        windows.activate.assert_called_once_with(process.pid, 77)
        process.terminate.assert_not_called()
        recovery.close.assert_called_once()

    def test_venv_redirector_is_not_treated_as_the_tk_owner(self):
        wrapper = self.process()
        process = self.process()
        process.pid = wrapper.pid + 1
        process.ppid.return_value = wrapper.pid
        wrapper.ppid.return_value = 1
        mutex = Mock(acquire=Mock(side_effect=[False, False, True]))
        recovery = Mock(acquire=Mock(return_value=True))
        windows = Mock(visible=Mock(return_value=[]))
        with patch.object(owner.psutil, 'process_iter', return_value=[wrapper, process]), \
             patch.object(owner, 'close_invisible', return_value=True) as close:
            self.assertTrue(owner.acquire_ui(self.root, mutex, Mock(return_value=recovery),
                                             windows=windows, startup_grace=0))
        close.assert_called_once_with(self.root, process, unittest.mock.ANY, windows)
        wrapper.terminate.assert_not_called()

    def test_current_launchs_own_venv_parent_is_not_a_stale_ui(self):
        wrapper = self.process()
        current = Mock()
        current.exe.return_value = str(self.root / 'base/python.exe')
        current.cmdline.return_value = wrapper.cmdline.return_value
        current.parents.return_value = [wrapper]
        with patch.object(owner.psutil, 'Process', return_value=current):
            self.assertEqual(owner.launch_wrappers([wrapper]), {wrapper.pid})

    def test_main_constructor_failure_still_destroys_root_and_releases_mutex(self):
        import tkinter
        window = Mock()
        with patch.object(launcher, 'ROOT', self.root), patch.object(sys, 'argv', ['project_launcher.py']), \
             patch.object(tkinter, 'Tk', return_value=window), \
             patch.object(launcher, 'LauncherUI', side_effect=RuntimeError('fixture constructor')):
            with self.assertRaisesRegex(RuntimeError, 'fixture constructor'):
                launcher.main()
        window.destroy.assert_called_once()
        check = launcher.NamedMutex(self.root, 'ui')
        try:
            self.assertTrue(check.acquire())
        finally:
            check.close()
        self.assertFalse((self.root / 'data/tmp/launcher-ui-owner.json').exists())


@unittest.skipUnless(os.name == 'nt', 'Windows Tk/desktop ownership fixtures')
class RealTkTests(IsolatedRoot):
    def setUp(self):
        super().setUp()
        scripts = self.root / 'tk-scripts'
        for name in ('tcl8.6', 'tk8.6'):
            shutil.copytree(Path(sys.base_prefix) / 'tcl' / name, scripts / name)
        self.environment = {**os.environ, 'TCL_LIBRARY': str(scripts / 'tcl8.6'),
                            'TK_LIBRARY': str(scripts / 'tk8.6'), 'PYTHONDONTWRITEBYTECODE': '1',
                            'TEMP': str(self.root), 'TMP': str(self.root)}

    def stop_fixture(self, process):
        if process is None:
            return
        try:
            if process.poll() is None:
                current = psutil.Process(process.pid)
                try:
                    record = json.loads((self.root / 'data/tmp/launcher-ui-owner.json').read_text(encoding='utf-8'))
                    event = owner.Event(record['closeEvent'])
                    try:
                        event.signal()
                    finally:
                        event.close()
                except (OSError, ValueError, KeyError):
                    pass
                try:
                    owner.Windows().close_windows(current)
                    process.wait(timeout=3)
                except (psutil.Error, OSError, subprocess.TimeoutExpired):
                    pass
                if process.poll() is None:
                    process.terminate()  # Only this fixture's directly owned handle.
            process.wait(timeout=4)
            self.assertFalse(psutil.pid_exists(process.pid))
        finally:
            if isinstance(process, DesktopProcess):
                process.close()

    def run_fixture(self, *, visible=False, legacy=False, desktop=None, through_main=False):
        # The only created UI is an inert Tk root. Production main supplies
        # finally/destroy; the legacy branch has its own explicit finally.
        script = self.root / 'tools/project_launcher.py'
        script.parent.mkdir()
        script.write_text('''import ctypes,os,sys,time
from pathlib import Path
sys.path.insert(0,TOOLS_PATH)
import tkinter as tk
import project_launcher as app
import launcher_ui_owner as owner
root=Path(__file__).resolve().parents[1]
app.ROOT=root
class InertUI:
    def __init__(self,window,backend):
        self.window=window;self.closed=False
        window.title(owner.TITLE);window.geometry('260x100')
        user=ctypes.WinDLL('user32');kernel=ctypes.WinDLL('kernel32')
        user.GetThreadDesktop.argtypes=[ctypes.c_uint32];user.GetThreadDesktop.restype=ctypes.c_void_p
        user.GetUserObjectInformationW.argtypes=[ctypes.c_void_p,ctypes.c_int,ctypes.c_void_p,ctypes.c_uint32,ctypes.c_void_p]
        desktop=ctypes.create_unicode_buffer(256);needed=ctypes.c_uint32()
        assert user.GetUserObjectInformationW(user.GetThreadDesktop(kernel.GetCurrentThreadId()),2,desktop,ctypes.sizeof(desktop),ctypes.byref(needed))
        (root/'actual-desktop.txt').write_text(desktop.value,encoding='utf-8')
        window.after(20000,self.close)
    def close(self):
        self.closed=True;self.window.destroy()
if os.environ.get('C1_FIXTURE_LEGACY')=='1':
    mutex=app.NamedMutex(root,'ui');window=None
    try:
        assert mutex.acquire()
        window=tk.Tk();ui=InertUI(window,None)
        window.update_idletasks();window.withdraw()
        owner.notify_ready(root);window.mainloop()
    finally:
        if window is not None:
            try:window.destroy()
            except tk.TclError:pass
        mutex.close()
else:
    app.LauncherUI=InertUI
    if os.environ.get('C1_FIXTURE_VISIBLE')!='1':
        app.show_launcher_window=lambda window: (window.update_idletasks(),window.withdraw())
    raise SystemExit(app.main())
'''.replace('TOOLS_PATH', repr(str(ROOT / 'tools'))), encoding='utf-8')
        name = 'Local\\OWMCLauncherReady-test-' + uuid.uuid4().hex
        ready = owner.Event(name, create=True)
        log = (self.root / 'fixture.log').open('wb')
        environment = {**self.environment, 'OWMC_LAUNCH_READY_EVENT': name,
                       'C1_FIXTURE_VISIBLE': str(int(visible)), 'C1_FIXTURE_LEGACY': str(int(legacy))}
        command = [sys.executable, '-B', str(script)]
        process = None
        replacement = None
        replacement_ready = None
        observed = []
        acquired = launcher.NamedMutex(self.root, 'ui')
        try:
            process = (DesktopProcess(command, self.root, desktop, environment, log) if desktop else
                       subprocess.Popen(command, cwd=self.root, stdout=log, stderr=subprocess.STDOUT,
                                        creationflags=subprocess.CREATE_NO_WINDOW, env=environment))
            self.assertEqual(ready.kernel.WaitForSingleObject(ready.handle, 10000), 0,
                             (self.root / 'fixture.log').read_text(encoding='utf-8', errors='replace'))
            interpreters = {self.python, Path(sys._base_executable).resolve()}
            observed = [item.pid for item in psutil.process_iter()
                        if owner.verified_ui(item, self.root, interpreters)]
            if visible and not desktop:
                self.assertFalse(owner.acquire_ui(self.root, acquired, launcher.NamedMutex, startup_grace=0))
                self.assertIsNone(process.poll())
            else:
                if through_main:
                    replacement_name = 'Local\\OWMCLauncherReady-replacement-' + uuid.uuid4().hex
                    replacement_ready = owner.Event(replacement_name, create=True)
                    replacement = subprocess.Popen(command, cwd=self.root, stdout=log, stderr=subprocess.STDOUT,
                        creationflags=subprocess.CREATE_NO_WINDOW,
                        env={**environment, 'C1_FIXTURE_VISIBLE': '1', 'C1_FIXTURE_LEGACY': '0',
                             'OWMC_LAUNCH_READY_EVENT': replacement_name})
                    self.assertEqual(replacement_ready.kernel.WaitForSingleObject(replacement_ready.handle, 12000), 0,
                                     (self.root / 'fixture.log').read_text(encoding='utf-8', errors='replace'))
                    self.assertIsNone(replacement.poll())
                else:
                    self.assertTrue(owner.acquire_ui(self.root, acquired, launcher.NamedMutex, startup_grace=0))
                self.assertEqual(process.wait(timeout=3), 0)
                entries = [json.loads(line) for line in (self.root / 'data/tmp/launcher-ui.log').read_text(encoding='utf-8').splitlines()]
                self.assertTrue(any(row['event'] == 'old-ui-closed-normally' for row in entries))
                self.assertFalse(any(row['event'] == 'unresponsive-invisible-ui-ended' for row in entries))
        finally:
            acquired.close()
            try:
                try:
                    self.stop_fixture(replacement)
                finally:
                    self.stop_fixture(process)
            finally:
                if replacement_ready is not None:
                    replacement_ready.close()
                ready.close()
                log.close()
                remaining = [item.pid for item in psutil.process_iter()
                             if owner.verified_ui(item, self.root, {self.python, Path(sys._base_executable).resolve()})]
                path = ROOT / 'research/oneclick/c1-round3-ui-evidence.jsonl'
                with path.open('a', encoding='utf-8') as stream:
                    stream.write(json.dumps(dict(test=self.id(), isolatedMutex=owner.prefix(self.root),
                        observedPids=observed, remainingPids=remaining, desktop=desktop,
                        throughMain=through_main, gamesLaunched=False)) + '\n')
                self.assertEqual(remaining, [])

    def test_invisible_tk_ui_closes_through_event_and_mutex_is_recovered(self):
        self.run_fixture()

    def test_legacy_invisible_tk_ui_closes_through_wm_close(self):
        self.run_fixture(legacy=True)

    def test_visible_tk_ui_is_retained(self):
        self.run_fixture(visible=True)

    def test_new_main_recovers_hidden_ui_without_ending_its_own_venv_parent(self):
        self.run_fixture(through_main=True)

    def test_other_desktop_ui_closes_without_switching_the_input_desktop(self):
        user = ctypes.WinDLL('user32', use_last_error=True)
        user.CreateDesktopW.argtypes = [w.LPCWSTR, w.LPCWSTR, ctypes.c_void_p, w.DWORD, w.DWORD, ctypes.c_void_p]
        user.CreateDesktopW.restype = w.HANDLE
        user.CloseDesktop.argtypes = [w.HANDLE]
        user.GetProcessWindowStation.restype = w.HANDLE
        user.GetUserObjectInformationW.argtypes = [w.HANDLE, ctypes.c_int, ctypes.c_void_p, w.DWORD, ctypes.POINTER(w.DWORD)]
        station = ctypes.create_unicode_buffer(256)
        needed = w.DWORD()
        self.assertTrue(user.GetUserObjectInformationW(user.GetProcessWindowStation(), 2, station,
                                                        ctypes.sizeof(station), ctypes.byref(needed)))
        name = 'C1-test-' + uuid.uuid4().hex
        handle = user.CreateDesktopW(name, None, None, 0, 0xc3, None)
        if not handle:
            self.skipTest('Sandbox does not permit a separate test desktop: ' + str(ctypes.get_last_error()))
        try:
            self.run_fixture(visible=True, desktop=station.value + '\\' + name)
            self.assertEqual((self.root / 'actual-desktop.txt').read_text(encoding='utf-8'), name)
        finally:
            self.assertTrue(user.CloseDesktop(handle))


if __name__ == '__main__':
    unittest.main()
