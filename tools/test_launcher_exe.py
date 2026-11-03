"""Execute the compiled wrapper only in inert, root-isolated fixtures."""
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest
import uuid

import psutil
from launcher_ui_owner import Event

ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(os.name == 'nt', 'Compiled Windows bootstrap fixtures')
class BootstrapTests(unittest.TestCase):
    def setUp(self):
        scratch = ROOT / 'data/tmp'
        scratch.mkdir(parents=True, exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(prefix='c1-exe-', dir=scratch)
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name) / '中文 空格 & 离线测试'
        (self.root / 'tools').mkdir(parents=True)
        self.exe = self.root / 'ow x mc 启动器.exe'
        shutil.copy2(ROOT / self.exe.name, self.exe)

    def helper(self, body):
        path = self.root / 'tools/open_project_launcher.ps1'
        path.write_text("param([string]$ReadyEvent)\n$ErrorActionPreference='Stop'\n" + body,
                        encoding='utf-8-sig')

    def run_exe(self):
        # No fixture script imports LauncherUI, Tk, the supervisor or either game.
        result = subprocess.run([str(self.exe)], cwd=self.root, capture_output=True,
                                creationflags=subprocess.CREATE_NO_WINDOW, timeout=18)
        log = (self.root / 'data/tmp/launcher-exe.log').read_text(encoding='utf-8')
        return result.returncode, log

    def acknowledge(self):
        return "$ready=[System.Threading.EventWaitHandle]::OpenExisting($ReadyEvent); $null=$ready.Set(); $ready.Dispose()\n"

    def counter(self):
        return '''$file=Join-Path $PSScriptRoot '../attempts.txt'
$count=0
if(Test-Path -LiteralPath $file){$count=[int](Get-Content -LiteralPath $file -Raw)}
$count+=1
[System.IO.File]::WriteAllText($file,[string]$count,[System.Text.UTF8Encoding]::new($false))
'''

    def test_unicode_space_ampersand_path_waits_for_ready_ack(self):
        self.helper(self.acknowledge())
        code, log = self.run_exe()
        self.assertEqual(code, 0, log)
        self.assertIn('attempt=1 ui-ready', log)
        self.assertNotIn('retrying-once', log)
        self.assertIn('中文 空格', log)

    def test_first_failure_retries_once_then_succeeds(self):
        self.helper(self.counter() + 'if($count -eq 1){exit 7}\n' + self.acknowledge())
        code, log = self.run_exe()
        self.assertEqual(code, 0, log)
        self.assertEqual((self.root / 'attempts.txt').read_text(encoding='utf-8'), '2')
        self.assertIn('attempt=1 retrying-once', log)
        self.assertIn('attempt=2 ui-ready', log)

    def test_persistent_failure_is_logged_and_stops_after_two_attempts(self):
        self.helper(self.counter() + 'exit 7\n')
        code, log = self.run_exe()
        self.assertEqual(code, 1)
        self.assertEqual((self.root / 'attempts.txt').read_text(encoding='utf-8'), '2')
        self.assertEqual(log.count('retrying-once'), 1)
        self.assertIn('failed-final', log)
        self.assertNotRegex(log, r'attempt=\d+ ui-ready code=')

    def test_script_success_without_ui_ack_is_failure_and_retried(self):
        self.helper(self.counter() + 'exit 0\n')
        code, log = self.run_exe()
        self.assertEqual(code, 1)
        self.assertEqual((self.root / 'attempts.txt').read_text(encoding='utf-8'), '2')
        self.assertIn('no-ui-acknowledgement code=0', log)

    def test_missing_helper_is_diagnosed_without_a_dialog(self):
        code, log = self.run_exe()
        self.assertEqual(code, 1)
        self.assertEqual(log.count('script-missing'), 2)
        self.assertIn('failed-final', log)
        source = (ROOT / 'tools/launcher_exe/owmc_launcher.c').read_text(encoding='utf-8')
        self.assertNotIn('MessageBox', source)
        self.assertNotIn('INFINITE', source)

    def test_real_helper_passes_ready_event_and_never_creates_a_console(self):
        shutil.copy2(ROOT / 'tools/open_project_launcher.ps1', self.root / 'tools/open_project_launcher.ps1')
        (self.root / 'config').mkdir()
        (self.root / 'config/launcher.json').write_text(json.dumps(dict(schemaVersion=1,
            autoStart=False, paths={'python': sys.executable})), encoding='utf-8')
        (self.root / 'tools/project_launcher.py').write_text('''import ctypes,json,os,pathlib
root=pathlib.Path(__file__).resolve().parents[1]
(root/'inert-python.json').write_text(json.dumps(dict(console=int(ctypes.windll.kernel32.GetConsoleWindow()),cwd=os.getcwd())),encoding='utf-8')
kernel=ctypes.WinDLL('kernel32',use_last_error=True)
kernel.OpenEventW.argtypes=[ctypes.c_uint32,ctypes.c_int,ctypes.c_wchar_p];kernel.OpenEventW.restype=ctypes.c_void_p
kernel.SetEvent.argtypes=[ctypes.c_void_p];kernel.CloseHandle.argtypes=[ctypes.c_void_p]
event=kernel.OpenEventW(2,False,os.environ['OWMC_LAUNCH_READY_EVENT'])
assert event and kernel.SetEvent(event)
kernel.CloseHandle(event)
''', encoding='utf-8')
        code, log = self.run_exe()
        self.assertEqual(code, 0, log)
        result = json.loads((self.root / 'inert-python.json').read_text(encoding='utf-8'))
        self.assertEqual(result, dict(console=0, cwd=str(self.root)))
        self.assertIn('ui-ready', (self.root / 'data/tmp/launcher-powershell.log').read_text(encoding='utf-8'))

    def test_compiled_binary_is_x64_gui_subsystem(self):
        data = self.exe.read_bytes()
        pe = struct.unpack_from('<I', data, 0x3c)[0]
        self.assertEqual(struct.unpack_from('<H', data, pe + 4)[0], 0x8664)
        self.assertEqual(struct.unpack_from('<H', data, pe + 24 + 68)[0], 2)

    def test_os_startfile_shell_route_starts_the_inert_copy(self):
        # Exercise the reported double-click route, but never the real root EXE.
        name = 'Local\\OWMCLauncherReady-shell-test-' + uuid.uuid4().hex
        event = Event(name, create=True)
        self.helper(self.acknowledge() +
                    "$ping=[System.Threading.EventWaitHandle]::OpenExisting('" + name +
                    "'); $null=$ping.Set(); $ping.Dispose()\n")
        try:
            os.startfile(str(self.exe))
            self.assertEqual(event.kernel.WaitForSingleObject(event.handle, 10000), 0)
            path = self.root / 'data/tmp/launcher-exe.log'
            text = path.read_text(encoding='utf-8')
            import re
            pid = int(re.search(r'pid=(\d+)', text).group(1))
            try:
                process = psutil.Process(pid)
                if Path(process.exe()).resolve() == self.exe.resolve():
                    self.assertEqual(process.wait(timeout=5), 0)
            except psutil.NoSuchProcess:
                pass
            self.assertIn('attempt=1 ui-ready', path.read_text(encoding='utf-8'))
        finally:
            event.close()


if __name__ == '__main__':
    unittest.main()
