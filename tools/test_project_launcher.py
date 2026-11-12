"""Launcher process/lifecycle fixtures. Never start or stop a real game."""
from __future__ import annotations

import hashlib
import contextlib
import io
import json
from pathlib import Path
import tempfile
import time
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import project_launcher as launcher


class LauncherFixtures(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.backend = launcher.SessionBackend(self.root)
        self.log = self.root / 'action.log'

    def settings(self, **extra):
        value = dict(schemaVersion=1, flightKey='F6', worldName='fixture', worldSeed=-490526775015596785)
        value.update(extra)
        (self.root / 'passthrough-settings.json').write_text(json.dumps(value), encoding='utf-8')
        return value

    def test_existing_supervisor_never_spawns_or_validates_another_owner(self):
        with patch.object(self.backend, 'supervisors', return_value=[Mock(pid=7)]), \
             patch.object(self.backend, 'spawn') as spawn, patch.object(self.backend, 'validate_start') as validate:
            result = self.backend.start(self.log)
        self.assertEqual(result['result'], 'existing-supervisor')
        spawn.assert_not_called()
        validate.assert_not_called()

    def test_start_delegates_only_to_existing_supervisor_entry(self):
        with patch.object(self.backend, 'supervisors', return_value=[]), \
             patch.object(self.backend, 'validate_start') as validate, \
             patch.object(self.backend, 'spawn', return_value=Mock(pid=9)) as spawn:
            result = self.backend.start(self.log)
        validate.assert_called_once()
        command, log = spawn.call_args.args
        self.assertEqual(command, [str(self.backend.python), '-u', str(self.root / 'tools/launch_passthrough_session.py')])
        self.assertEqual(log, self.log)
        self.assertNotIn('ready', result)
        self.assertEqual(result['supervisorPid'], 9)

    def test_conflicting_legacy_key_refuses_before_any_process_launch(self):
        self.settings(flightKey='F9')
        with patch.object(self.backend, 'supervisors', return_value=[]), patch.object(self.backend, 'spawn') as spawn:
            with self.assertRaisesRegex(ValueError, '暮色森林门'):
                self.backend.start(self.log)
        spawn.assert_not_called()
        self.assertEqual(self.backend.settings()['flightKey'], 'F9')

    def test_wrong_executable_hash_refuses_launch(self):
        self.settings()
        for name in ('.venv/Scripts/python.exe', 'tools/launch_passthrough_session.py', 'tools/stop_passthrough_session.py'):
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b'fixture')
        path = self.root / launcher.EXE_RELATIVE
        path.parent.mkdir(parents=True)
        path.write_bytes(b'not-an-offline-client')
        with self.assertRaisesRegex(ValueError, 'SHA256'):
            self.backend.validate_start()

    def test_exact_hash_gate_is_exercised_with_private_fixture(self):
        self.settings()
        for name in ('.venv/Scripts/python.exe', 'tools/launch_passthrough_session.py', 'tools/stop_passthrough_session.py', str(launcher.EXE_RELATIVE)):
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b'fixture')
        with patch.object(launcher, 'TARGET_SHA256', hashlib.sha256(b'fixture').hexdigest()):
            self.backend.validate_start()

    def test_restart_never_starts_after_strict_restoration_failure(self):
        with patch.object(self.backend, 'stop', side_effect=RuntimeError('Native callback restoration failed')), \
             patch.object(self.backend, 'start') as start:
            with self.assertRaisesRegex(RuntimeError, 'restoration failed'):
                launcher.execute_action(self.backend, 'restart', self.log)
        start.assert_not_called()

    def test_restart_orders_complete_stop_before_start(self):
        events = []
        with patch.object(self.backend, 'stop', side_effect=lambda log: events.append('stop')), \
             patch.object(self.backend, 'start', side_effect=lambda log: events.append('start') or {'ok': True}):
            self.assertEqual(launcher.execute_action(self.backend, 'restart', self.log), {'ok': True})
        self.assertEqual(events, ['stop', 'start'])

    def test_stop_uses_existing_full_save_and_restore_entrypoint(self):
        with patch.object(self.backend, 'checked_command', return_value={}) as run:
            self.backend.stop(self.log)
        command = run.call_args.args[0]
        self.assertEqual(command[-1], str(self.root / 'tools/stop_passthrough_session.py'))
        self.assertNotIn('--keep-minecraft', command)

    def test_nonzero_stop_process_is_reported_as_failure(self):
        with patch.object(self.backend, 'spawn', return_value=Mock(wait=Mock(return_value=1))):
            with self.assertRaisesRegex(RuntimeError, '已停止后续步骤'):
                self.backend.stop(self.log)

    def test_new_world_validates_before_configuration_entry(self):
        with patch.object(self.backend, 'checked_command') as run:
            with self.assertRaises(ValueError):
                launcher.execute_action(self.backend, 'new-world', self.log, '../unsafe')
            run.assert_not_called()
            launcher.execute_action(self.backend, 'new-world', self.log, 'Boss Fixture')
        command = run.call_args.args[0]
        self.assertEqual(command[-2:], ['--new-world', 'Boss Fixture'])
        self.assertEqual(command[-3], str(self.root / 'tools/configure_passthrough.py'))

    def test_detached_spawn_has_logs_and_no_parent_console_lifetime(self):
        with patch.object(launcher.subprocess, 'Popen', return_value=Mock(pid=8)) as popen:
            self.backend.spawn(['fixture.exe'], self.log)
        kwargs = popen.call_args.kwargs
        self.assertTrue(kwargs['close_fds'])
        self.assertEqual(kwargs['stdin'], launcher.subprocess.DEVNULL)
        self.assertEqual(kwargs['creationflags'], launcher.detached_flags())
        self.assertTrue(self.log.is_file())

    def test_action_mutex_rejects_duplicate_without_replacing_active_record(self):
        with patch.object(launcher, 'NamedMutex') as mutex, patch.object(launcher, 'execute_action') as execute, \
             contextlib.redirect_stdout(io.StringIO()):
            mutex.return_value.acquire.return_value = False
            code = launcher.run_action(self.backend, 'restart', self.log)
        self.assertEqual(code, 2)
        execute.assert_not_called()
        self.assertFalse(self.backend.action_path.exists())

    @unittest.skipUnless(launcher.os.name == 'nt', 'Windows named mutex fixture')
    def test_real_named_mutex_excludes_duplicate_and_releases(self):
        first = launcher.NamedMutex(self.root, 'fixture')
        second = launcher.NamedMutex(self.root, 'fixture')
        third = launcher.NamedMutex(self.root, 'fixture')
        self.addCleanup(first.close)
        self.addCleanup(second.close)
        self.addCleanup(third.close)
        self.assertTrue(first.acquire())
        self.assertFalse(second.acquire())
        first.close()
        self.assertTrue(third.acquire())

    def test_failed_action_keeps_evidence_and_releases_mutex(self):
        with patch.object(launcher, 'NamedMutex') as mutex, \
             patch.object(launcher, 'execute_action', side_effect=ValueError('strict stop refused')), \
             patch.object(launcher.traceback, 'print_exc'):
            mutex.return_value.acquire.return_value = True
            code = launcher.run_action(self.backend, 'restart', self.log)
        record = launcher.read_object(self.backend.action_path)
        self.assertEqual(code, 1)
        self.assertEqual(record['phase'], 'failed')
        self.assertIn('strict stop refused', record['error'])
        self.assertGreater(record['created'], 0)
        mutex.return_value.close.assert_called_once()

    def test_settings_holds_same_action_mutex_until_editor_process_exits(self):
        with patch.object(launcher, 'NamedMutex') as mutex:
            mutex.return_value.acquire.return_value = True
            def editor(command, log):
                mutex.return_value.close.assert_not_called()
                self.assertEqual(command[-2:], ['-Settings', '-WaitForExit'])
                self.assertIn(str(self.root / 'tools/open_project_launcher.ps1'), command)
                return {'exitCode': 0}
            with patch.object(self.backend, 'checked_command', side_effect=editor), \
                 patch.object(launcher, 'execute_action', wraps=launcher.execute_action):
                self.assertEqual(launcher.run_action(self.backend, 'settings', self.log, request_id='fixture-request'), 0)
        record = launcher.read_object(self.backend.action_path)
        self.assertEqual(record['requestId'], 'fixture-request')
        self.assertEqual(record['phase'], 'succeeded')
        mutex.return_value.close.assert_called_once()

    def test_shared_action_requires_current_creation_and_exact_interpreter_script(self):
        process = Mock()
        process.create_time.return_value = 200.0
        process.is_running.return_value = True
        process.exe.return_value = str(self.backend.python)
        process.cmdline.return_value = [str(self.backend.python), str(self.root / 'tools/project_launcher.py'), '--action', 'settings']
        record = {'pid': 42, 'created': 200.0, 'phase': 'running'}
        with patch.object(launcher.psutil, 'Process', return_value=process):
            self.assertTrue(self.backend.action_active(record))
            self.assertFalse(self.backend.action_active({**record, 'created': 100.0}))
            self.assertFalse(self.backend.action_active({**record, 'phase': 'succeeded'}))
            process.exe.return_value = str(self.root / 'unrelated/python.exe')
            self.assertFalse(self.backend.action_active(record))
            process.exe.return_value = str(self.backend.python)
            process.cmdline.return_value = [str(self.backend.python), str(self.root / 'elsewhere/project_launcher.py'), '--action', 'settings']
            self.assertFalse(self.backend.action_active(record))

    def test_legacy_configure_gui_owner_is_recognized_after_launcher_reopens(self):
        process = Mock()
        process.create_time.return_value = 200.0
        process.is_running.return_value = True
        process.exe.return_value = str(self.backend.python)
        process.cmdline.return_value = [str(self.backend.python), str(self.root / 'tools/configure_passthrough.py'), '--gui']
        with patch.object(launcher.psutil, 'Process', return_value=process):
            self.assertTrue(self.backend.action_active({'pid': 42, 'created': 200.0, 'phase': 'running'}))

    def test_stale_reused_pid_cannot_authorize_window_operation(self):
        process = Mock()
        process.exe.return_value = str(self.root / launcher.EXE_RELATIVE)
        process.create_time.return_value = 200
        process.is_running.return_value = True
        with patch.object(launcher.psutil, 'Process', return_value=process):
            self.assertIsNone(self.backend.native_identity({'nativePid': 42, 'startedMs': 100000}))

    def test_path_mismatch_cannot_authorize_window_operation(self):
        process = Mock()
        process.exe.return_value = str(self.root / 'other/GameClientApp.patched.exe')
        with patch.object(launcher.psutil, 'Process', return_value=process):
            self.assertIsNone(self.backend.native_identity({'nativePid': 42, 'startedMs': 100000}))

    def test_fresh_matching_native_identity(self):
        process = Mock()
        process.exe.return_value = str(self.root / launcher.EXE_RELATIVE)
        process.create_time.return_value = 99
        process.is_running.return_value = True
        with patch.object(launcher.psutil, 'Process', return_value=process):
            self.assertIs(self.backend.native_identity({'nativePid': 42, 'startedMs': 100000}), process)

    def test_show_restores_only_matching_game_windows_without_resizing(self):
        native = Mock(pid=42)
        guest = Mock(pid=99)
        guest.cmdline.return_value = ['java.exe', str(self.root / 'guest-passthrough-client')]
        executable = self.root / launcher.EXE_RELATIVE
        executable.parent.mkdir(parents=True)
        executable.write_bytes(b'fixture')
        launcher.write_object(self.root / 'passthrough-settings.json', {'schemaVersion': 1,'nativeFullscreen': True})
        launcher.write_object(self.backend.status_path, {'state': {'minecraft': {'sourcePid': 99, 'mode': 'full-world-frame-proof'}}})
        layout = SimpleNamespace(arrange=Mock(return_value={'ok': True}),
                                  windows_for_pid=Mock(side_effect=lambda pid, visible_only: [SimpleNamespace(handle=pid + 100)]),
                                  user32=SimpleNamespace(ShowWindow=Mock()))
        with patch.object(self.backend, 'native_identity', return_value=native), \
             patch.object(launcher.psutil, 'Process', return_value=guest), \
             patch.object(launcher, 'TARGET_SHA256', hashlib.sha256(b'fixture').hexdigest()), \
             patch.dict('sys.modules', {'window_layout': layout}):
            self.assertEqual(self.backend.show_windows(), {'ok': True})
        layout.arrange.assert_called_once_with(42, 99, 0, 0,native_fullscreen=True)
        self.assertEqual(layout.user32.ShowWindow.call_count, 2)
        self.assertTrue(all(call.args[1] == 9 for call in layout.user32.ShowWindow.call_args_list))

    def test_show_refuses_other_minecraft_profile(self):
        native = Mock(pid=42)
        guest = Mock(pid=99)
        guest.cmdline.return_value = ['java.exe', 'some-other-world']
        executable = self.root / launcher.EXE_RELATIVE
        executable.parent.mkdir(parents=True)
        executable.write_bytes(b'fixture')
        launcher.write_object(self.backend.status_path, {'state': {'minecraft': {'sourcePid': 99, 'mode': 'full-world-frame-proof'}}})
        with patch.object(self.backend, 'native_identity', return_value=native), \
             patch.object(launcher.psutil, 'Process', return_value=guest), \
             patch.object(launcher, 'TARGET_SHA256', hashlib.sha256(b'fixture').hexdigest()):
            with self.assertRaisesRegex(ValueError, '不是本项目独立档案'):
                self.backend.show_windows()

    def test_snapshot_needs_fresh_heartbeat_not_merely_saved_ready(self):
        self.settings()
        launcher.write_object(self.backend.status_path, {'ready': True, 'heartbeatMs': (time.time() - 40) * 1000})
        with patch.object(self.backend, 'native_identity', return_value=None), patch.object(self.backend, 'supervisors', return_value=[]):
            snapshot = self.backend.snapshot()
        self.assertFalse(snapshot['fresh'])
        self.assertFalse(snapshot['nativeAlive'])

    def test_recent_log_is_bounded_and_cannot_read_outside_launcher_logs(self):
        path = self.backend.logs / 'fixture.log'
        path.parent.mkdir(parents=True)
        path.write_text('\n'.join(str(index) for index in range(100)), encoding='utf-8')
        self.assertEqual(self.backend.recent_log({'log': str(path)}), [str(index) for index in range(92, 100)])
        outside = self.root / 'private.txt'
        outside.write_text('not a launcher log', encoding='utf-8')
        self.assertEqual(self.backend.recent_log({'log': str(outside)}), [])

    def test_startup_log_header_survives_long_output_and_is_updated_in_place(self):
        path=self.backend.logs/'启动 测试.log'
        path.parent.mkdir(parents=True)
        path.touch()
        base=dict(root=str(self.root/'中文 路径'),windowsBuild='10.0.22631',
                  primaryDisplay=dict(width=2560,height=1440,refreshHz=165),scalePercent=150)
        with patch('startup_timeline.startup_environment',return_value=base):
            self.assertEqual(launcher.reserve_log_header(path,self.root),base)
        body=('中间日志\n'*5000+'结尾\n').encode('utf-8')
        with path.open('ab') as stream:stream.write(body)
        launcher.update_log_header(path,base,dict(status='ready',totalMs=1200,stagesMs={'compositor_attach':500},
            events=[dict(name='loading_presentation_ready',guest=dict(published=55),report=dict(lastMcFrame=42))]))
        self.assertEqual(path.read_bytes()[launcher.LOG_HEADER_BYTES:],body)
        preview=self.backend.recent_log({'log':str(path)})
        summary=json.loads(preview[0].removeprefix(launcher.LOG_HEADER.decode()))
        self.assertEqual(summary['primaryDisplay']['refreshHz'],165)
        self.assertEqual(summary['worldLive']['lastMcFrame'],42)
        self.assertEqual(summary['mc']['published'],55)
        self.assertEqual(summary['stagesMs'],{'compositor_attach':500})
        self.assertEqual(preview[-1],'结尾')
        self.assertLessEqual(len(preview),10)

    def test_process_matching_uses_exact_script_path_and_interpreter(self):
        target = self.root / 'tools/launch_passthrough_session.py'
        interpreter = self.root / '.venv/Scripts/python.exe'
        correct = Mock(info={'exe': str(interpreter), 'cmdline': [str(interpreter), str(target)]})
        wrong = Mock(info={'exe': str(interpreter), 'cmdline': [str(interpreter), str(self.root / 'other/launch_passthrough_session.py')]})
        wrong_interpreter = Mock(info={'exe': str(self.root / 'other/python.exe'), 'cmdline': ['python', str(target)]})
        with patch.object(launcher.psutil, 'process_iter', return_value=[correct, wrong, wrong_interpreter]):
            self.assertEqual(launcher._script_processes(target, {interpreter.resolve()}), [correct])


class PresentationFixtures(unittest.TestCase):
    def test_completion_does_not_reuse_an_old_requests_error(self):
        message = launcher.action_completion_message(1, 'new-id', {'requestId': 'old-id', 'phase': 'failed',
                                                                    'error': 'UNRELATED OLD ERROR'}, Path('new.log'))
        self.assertNotIn('UNRELATED OLD ERROR', message)
        self.assertIn('尚未取得本次匹配回执', message)
        self.assertIn('new.log', message)

    def test_completion_reports_exact_request_failure(self):
        message = launcher.action_completion_message(1, 'new-id', {'requestId': 'new-id', 'phase': 'failed',
                                                                   'error': '本次严格恢复失败'}, Path('new.log'))
        self.assertIn('本次严格恢复失败', message)
        self.assertIn('本次操作失败', message)

    def test_completion_zero_exit_without_terminal_receipt_is_not_success(self):
        message = launcher.action_completion_message(0, 'id', {'requestId': 'id', 'phase': 'running'}, Path('x.log'))
        self.assertIn('回执未完成', message)
        self.assertNotIn('本次后台操作已结束', message)

    def test_settings_close_does_not_claim_a_save_occurred(self):
        message = launcher.action_completion_message(0, 'id', {'requestId': 'id', 'phase': 'succeeded',
                                                               'action': 'settings'}, Path('x.log'))
        self.assertIn('关闭窗口本身不代表保存', message)

    def test_rejected_duplicate_has_its_own_feedback(self):
        message = launcher.action_completion_message(2, 'new-id', {'requestId': 'old-id'}, Path('new.log'))
        self.assertIn('本次请求未执行', message)
        self.assertIn('new.log', message)

    def test_explicit_show_targets_only_current_tk_owner(self):
        window = Mock(winfo_id=Mock(return_value=123))
        user = Mock()
        user.GetAncestor.return_value = 777
        def assign_owner(_handle, pointer):
            launcher.ctypes.cast(pointer, launcher.ctypes.POINTER(launcher.wintypes.DWORD)).contents.value = launcher.os.getpid()
            return 5
        user.GetWindowThreadProcessId.side_effect = assign_owner
        with patch.object(launcher.ctypes, 'WinDLL', return_value=user):
            launcher.show_launcher_window(window)
        window.update_idletasks.assert_called_once()
        window.deiconify.assert_called_once()
        self.assertEqual([call.args[0].value for call in user.ShowWindow.call_args_list], [777, 777])
        self.assertEqual([call.args[1] for call in user.ShowWindow.call_args_list], [5, 9])
        self.assertEqual(user.SetForegroundWindow.call_args.args[0].value, 777)

    def test_explicit_show_rejects_a_foreign_hwnd(self):
        user = Mock()
        user.GetAncestor.return_value = 777
        def assign_other_owner(_handle, pointer):
            launcher.ctypes.cast(pointer, launcher.ctypes.POINTER(launcher.wintypes.DWORD)).contents.value = launcher.os.getpid() + 99
            return 5
        user.GetWindowThreadProcessId.side_effect = assign_other_owner
        with patch.object(launcher.ctypes, 'WinDLL', return_value=user), \
             self.assertRaisesRegex(RuntimeError, 'current UI process'):
            launcher.show_launcher_window(Mock(winfo_id=Mock(return_value=123)))
        user.ShowWindow.assert_not_called()
        user.SetForegroundWindow.assert_not_called()

    def test_main_explicitly_shows_ui_after_build_before_mainloop(self):
        import tkinter
        events = []
        window = Mock()
        window.mainloop.side_effect = lambda: events.append('mainloop')
        with tempfile.TemporaryDirectory() as test_root, \
             patch.object(launcher, 'ROOT', Path(test_root)), \
             patch('sys.argv', ['project_launcher.py']), \
             patch.object(launcher, 'NamedMutex') as mutex, \
             patch.object(tkinter, 'Tk', return_value=window), \
             patch.object(launcher, 'LauncherUI', side_effect=lambda *args: events.append('build')), \
             patch.object(launcher, 'show_launcher_window', side_effect=lambda *args: events.append('show')):
            mutex.return_value.acquire.return_value = True
            self.assertEqual(launcher.main(), 0)
        self.assertEqual(events, ['build', 'show', 'mainloop'])
        window.destroy.assert_called_once()
        mutex.return_value.close.assert_called_once()

    def _helper_process_fixture(self, *, exit_code=0, output=None):
        # The helper creates .NET objects, not Start-Process. Both objects are
        # inert here: Start only records its settings and never creates a PID.
        destination = ('ConvertTo-Json -Compress' if output is None else
                       "ConvertTo-Json -Compress | Set-Content -LiteralPath '" +
                       str(output).replace("'", "''") + "' -Encoding UTF8")
        return '''$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()
function New-Object {
    param([string]$TypeName)
    if ($TypeName -eq 'System.Diagnostics.ProcessStartInfo') {
        return [pscustomobject]@{FileName=''; Arguments=''; WorkingDirectory=''; UseShellExecute=$true; CreateNoWindow=$false}
    }
    if ($TypeName -ne 'System.Diagnostics.Process') { throw ('Unexpected object: ' + $TypeName) }
    $fakeProcess = [pscustomobject]@{StartInfo=$null; ExitCode=REPLACE_EXIT_CODE; Started=$false; Waited=$false}
    $fakeProcess | Add-Member -MemberType ScriptMethod -Name Start -Value { $this.Started=$true; return $true }
    $fakeProcess | Add-Member -MemberType ScriptMethod -Name WaitForExit -Value { $this.Waited=$true }
    $fakeProcess | Add-Member -MemberType ScriptMethod -Name Dispose -Value {
        [pscustomobject]@{file=$this.StartInfo.FileName; arguments=$this.StartInfo.Arguments;
            cwd=$this.StartInfo.WorkingDirectory; noWindow=$this.StartInfo.CreateNoWindow;
            shell=$this.StartInfo.UseShellExecute; started=$this.Started; wait=$this.Waited;
            disposed=$true; policy=$env:OWMC_NO_CONSOLE} | REPLACE_OUTPUT
    }
    return $fakeProcess
}
'''.replace('REPLACE_EXIT_CODE', str(exit_code)).replace('REPLACE_OUTPUT', destination)

    @unittest.skipUnless(launcher.os.name == 'nt', 'Windows desktop entry fixture')
    def test_desktop_helper_requests_hidden_python_and_quotes_script_path(self):
        helper = launcher.ROOT / 'tools/open_project_launcher.ps1'
        script = self._helper_process_fixture() + ". '" + str(helper).replace("'", "''") + "'\n"
        result = launcher.subprocess.run(['powershell.exe', '-NoProfile', '-NonInteractive',
                                         '-ExecutionPolicy', 'Bypass', '-Command', script],
                                         capture_output=True, text=True, encoding='utf-8',
                                         creationflags=launcher.subprocess.CREATE_NO_WINDOW, timeout=20)
        self.assertEqual(result.returncode, 0, result.stderr)
        value = json.loads(result.stdout)
        self.assertEqual(Path(value['file']), launcher.ROOT / '.venv/Scripts/python.exe')
        self.assertTrue(value['noWindow'])
        self.assertFalse(value['shell'])
        self.assertTrue(value['started'])
        self.assertTrue(value['disposed'])
        self.assertFalse(value['wait'])
        self.assertEqual(value['policy'], '1')
        self.assertEqual(Path(value['cwd']), launcher.ROOT)
        self.assertEqual(value['arguments'], '-u "' + str(launcher.ROOT / 'tools/project_launcher.py') + '"')
        entry = (launcher.ROOT / 'tools/launcher_exe/owmc_launcher.c').read_text(encoding='utf-8')
        self.assertNotIn('pythonw.exe', entry)
        self.assertIn('-WindowStyle Hidden -File', entry)
        self.assertIn('CREATE_NO_WINDOW', entry)

    @unittest.skipUnless(launcher.os.name == 'nt', 'Windows settings helper fixture')
    def test_settings_helper_waits_and_propagates_child_failure(self):
        helper = launcher.ROOT / 'tools/open_project_launcher.ps1'
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / 'called.json'
            script = self._helper_process_fixture(exit_code=7, output=output)
            script += "& '" + str(helper).replace("'", "''") + "' -Settings -WaitForExit\nexit $LASTEXITCODE\n"
            result = launcher.subprocess.run(['powershell.exe', '-NoProfile', '-NonInteractive',
                                             '-ExecutionPolicy', 'Bypass', '-Command', script],
                                             capture_output=True, text=True, encoding='utf-8',
                                             creationflags=launcher.subprocess.CREATE_NO_WINDOW, timeout=20)
            self.assertEqual(result.returncode, 7, result.stderr)
            value = json.loads(output.read_text(encoding='utf-8-sig'))
        self.assertTrue(value['wait'])
        self.assertTrue(value['disposed'])
        self.assertTrue(value['started'])
        self.assertTrue(value['noWindow'])
        self.assertFalse(value['shell'])
        self.assertEqual(value['policy'], '1')
        self.assertEqual(value['arguments'], '-u "' + str(launcher.ROOT / 'tools/configure_passthrough.py') +
                         '" --gui --settings-owned')

    def test_picker_false_ready_is_a_normal_stage(self):
        title, detail, color = launcher.describe_snapshot({'status': {'phase': 'hero-selection', 'ready': False},
                                                         'nativeAlive': True, 'fresh': True})
        self.assertIn('等待选择英雄', title)
        self.assertEqual(color, 'normal')
        self.assertIn('正常阶段', detail)

    def test_ready_is_not_full_playable_acceptance(self):
        title, detail, _ = launcher.describe_snapshot({'status': {'phase': 'gameplay', 'ready': True},
                                                     'nativeAlive': True, 'fresh': True})
        self.assertIn('运行信号', title)
        self.assertIn('仍需游戏内验证', detail)

    def test_exit_zero_with_matching_crash_report_is_failure(self):
        title, detail, color = launcher.describe_snapshot({'status': {'stopped': True, 'nativeExitCode': 0,
                                                    'nativeExitClassification': 'crash-report'}, 'nativeAlive': False})
        self.assertEqual(color, 'error')
        self.assertIn('异常退出', title)
        self.assertIn('0', detail)

    def test_new_supervisor_does_not_display_old_crash_as_new_start_failure(self):
        title, _, color = launcher.describe_snapshot({'status': {'nativeExitClassification': 'crash-report'},
                                                    'nativeAlive': False, 'supervisorPids': [9]})
        self.assertEqual(title, '启动 / 恢复中')
        self.assertEqual(color, 'warning')

    def test_health_alone_never_proves_composition_or_ready(self):
        title, _, color = launcher.describe_snapshot({'status': {'state': {'minecraft': {'failed': False}}},
                                                    'nativeAlive': False, 'fresh': True})
        self.assertEqual(title, '尚未启动')
        self.assertEqual(color, 'neutral')

    def test_map_requires_all_real_acceptance_gates(self):
        item = {'compatibility': {'status': 'accepted'},
                'acceptance': dict(archive_preflight=True, world_load=True, boss_fight=True, reset_replay=False)}
        self.assertFalse(launcher.map_is_accepted(item))
        item['acceptance']['reset_replay'] = True
        self.assertTrue(launcher.map_is_accepted(item))
        item['compatibility']['status'] = 'pending'
        self.assertFalse(launcher.map_is_accepted(item))

    def test_catalog_missing_invalid_and_valid_are_separate(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / 'catalog.json'
            self.assertEqual(launcher.load_catalog(path)[0], [])
            path.write_text('{', encoding='utf-8')
            self.assertIn('失败', launcher.load_catalog(path)[1])
            launcher.write_object(path, {'schema_version': 1, 'maps': [{'id': 'x', 'title': 'Map', 'status': 'candidate',
                                                                        'source_url': 'https://example.com/author/map'}]})
            maps, error = launcher.load_catalog(path)
            self.assertEqual(error, '')
            self.assertFalse(launcher.map_is_accepted(maps[0]))

    def test_close_ui_does_not_touch_pending_coordinator(self):
        ui = object.__new__(launcher.LauncherUI)
        ui.window = Mock()
        ui.pending = Mock()
        ui.backend = Mock()
        ui.close()
        self.assertTrue(ui.closed)
        ui.window.destroy.assert_called_once()
        ui.pending.terminate.assert_not_called()
        ui.backend.stop.assert_not_called()

    def test_double_click_does_not_dispatch_second_action(self):
        ui = object.__new__(launcher.LauncherUI)
        ui.pending = Mock(poll=Mock(return_value=None))
        ui.backend = Mock()
        ui.action_var = Mock()
        ui.dispatch('start')
        ui.backend.spawn.assert_not_called()

    def test_open_settings_shows_in_window_page_without_spawning(self):
        ui = object.__new__(launcher.LauncherUI)
        ui.dispatch = Mock()
        ui.pending = None
        ui.last_snapshot = {}
        ui.settings = Mock()
        ui.show_page = Mock()
        ui.open_settings()
        ui.settings.load.assert_called_once()
        ui.show_page.assert_called_once_with('settings')
        ui.dispatch.assert_not_called()

    def test_toggle_on_leftovers_reboots_instead_of_stopping(self):
        ui = object.__new__(launcher.LauncherUI)
        ui.dispatch = Mock()
        ui.last_snapshot = {'supervisorPids': [], 'projectPids': [5]}
        ui.toggle()
        ui.dispatch.assert_called_once_with('reboot')

    def test_robust_stop_retries_until_no_project_process(self):
        backend = launcher.SessionBackend(Path(tempfile.mkdtemp()))
        calls = []
        def stop(log, **kwargs):
            calls.append(kwargs)
            if len(calls) == 1:
                raise RuntimeError('killed mid-restore')
            return {'ok': True}
        with patch.object(backend, 'stop', side_effect=stop),              patch.object(backend, 'supervisors', return_value=[]),              patch.object(backend, 'project_processes', side_effect=[[Mock()], []]),              patch.object(launcher.time, 'sleep'):
            result = backend.robust_stop(Path('x.log'))
        self.assertEqual(result['attempts'], 2)
        self.assertTrue(all(c.get('allow_window_close') for c in calls))

    def test_clean_start_retries_once_after_failed_start(self):
        backend = launcher.SessionBackend(Path(tempfile.mkdtemp()))
        with patch.object(backend, 'supervisors', return_value=[]),              patch.object(backend, 'project_processes', return_value=[]),              patch.object(backend, 'start', return_value={'result': 'supervisor-started'}) as start,              patch.object(backend, 'wait_started', side_effect=['supervisor-exited', 'hero-selection']):
            result = backend.clean_start(Path('x.log'))
        self.assertEqual(start.call_count, 2)
        self.assertEqual(result['phase'], 'hero-selection')

    def test_reopened_ui_does_not_dispatch_while_settings_owner_is_alive(self):
        ui = object.__new__(launcher.LauncherUI)
        ui.pending = None
        ui.last_snapshot = {'actionActive': True, 'action': {'action': 'settings'}}
        ui.backend = Mock()
        ui.action_var = Mock()
        ui.dispatch('restart')
        ui.backend.spawn.assert_not_called()
        self.assertIn('设置', ui.action_var.set.call_args.args[0])


if __name__ == '__main__':
    unittest.main()
