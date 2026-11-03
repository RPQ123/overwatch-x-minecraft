"""Offline stability regressions. No game, console or input process is used."""
from contextlib import ExitStack, redirect_stdout
import hashlib
import io
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import psutil
import native_normal_close as close
import stop_passthrough_session as session
import test_stop_passthrough_session as existing_stop
import stability_selection as selection
import minecraft_crash_evidence as crash
import dev_cycle_support as cycle
import launch_passthrough_session as supervisor
import project_launcher as launcher


class NativeExitTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.exe = self.root / 'native.exe'
        self.exe.write_bytes(b'guarded-offline-fixture')
        self.sha = hashlib.sha256(self.exe.read_bytes()).hexdigest()
        self.identity = dict(pid=123, creation=10., creationFiletime=100,
                             executable=str(self.exe), sha256=self.sha)
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        self.stack.enter_context(patch.object(close, 'EXE', self.exe))
        self.stack.enter_context(patch.object(close, 'PATCHED_SHA256', self.sha))
        self.process = self.stack.enter_context(patch.object(close.psutil, 'Process', side_effect=psutil.NoSuchProcess(123)))
        self.validation = self.stack.enter_context(patch.object(close, 'validate_native_identity', side_effect=psutil.NoSuchProcess(123)))
        self.crashes = self.stack.enter_context(patch.object(close, 'wait_native_crash_reports', return_value=[]))
        self.primitives = self.stack.enter_context(patch.object(close, '_verified_primitives'))
        self.restore = self.stack.enter_context(patch.object(close, 'stop'))

    def run_close(self):
        return close.normal_close(self.identity, self.root / 'close')

    def test_absent_verified_native_skips_without_claiming_normal_close(self):
        result = self.run_close()
        self.assertTrue(result['passed'])
        self.assertTrue(result['alreadyExited'])
        self.assertFalse(result['normalClosePassed'])
        self.assertFalse(result['requestedNormalClose'])
        self.assertFalse(result['forcedTermination'])
        self.assertEqual(result['nativeExitClassification'], 'already-exited')
        self.primitives.assert_not_called()
        self.restore.assert_not_called()
        self.assertEqual(json.loads((self.root/'close/result.json').read_text()), result)

    def test_crash_before_close_is_retained_and_allows_other_game_cleanup(self):
        self.crashes.return_value = [{'path': 'matching-crash'}]
        result = self.run_close()
        self.assertEqual(result['nativeExitClassification'], 'already-exited-crash-report')
        self.assertTrue(result['passed'])
        self.assertFalse(result['normalClosePassed'])

    def test_unavailable_crash_evidence_is_not_a_normal_exit_claim(self):
        self.crashes.side_effect = OSError('report unreadable')
        result = self.run_close()
        self.assertEqual(result['nativeExitClassification'], 'already-exited-evidence-unavailable')
        self.assertFalse(result['normalClosePassed'])

    def test_reused_pid_is_refused_before_any_close(self):
        process = Mock()
        process.create_time.return_value = 11.
        self.process.side_effect = None
        self.process.return_value = process
        with self.assertRaises(close.NativeCloseError) as failure:
            self.run_close()
        self.assertIn('identity changed', failure.exception.result['exitVerificationError'])
        self.restore.assert_not_called()
        self.primitives.assert_not_called()

    def test_access_denied_is_not_absence(self):
        self.process.side_effect = psutil.AccessDenied(123)
        with self.assertRaises(close.NativeCloseError):
            self.run_close()
        self.restore.assert_not_called()

    def test_wrong_saved_hash_cannot_authorize_exit_shortcut(self):
        self.identity['sha256'] = 'wrong'
        with self.assertRaises(close.NativeCloseError):
            self.run_close()
        self.process.assert_not_called()

    def test_exit_during_read_requires_actual_absence(self):
        self.validation.side_effect = None
        self.primitives.return_value.snapshot.side_effect = OSError('read after exit')
        with patch.object(close, 'NativeExitWaiter') as waiter, patch.object(close, 'ResearchProcess') as reader, patch.object(close, 'process_creation', return_value=100):
            result = self.run_close()
        self.assertTrue(result['alreadyExited'])
        waiter.return_value.close.assert_called_once()
        reader.return_value.close.assert_called_once()
        self.restore.assert_not_called()


class SessionExitTests(existing_stop.StopSessionTests):
    # Reuse the established fully mocked stop harness and its policy regressions.
    def test_already_exited_native_still_saves_live_mc(self):
        self.pids.return_value = [10]
        self.normal.return_value.update(alreadyExited=True, normalClosePassed=False,
                                        nativeExitClassification='already-exited-crash-report', crashReports=[{'path':'crash'}])
        value = self.run_stop()
        self.assertTrue(value['stopped'])
        self.assertTrue(value['worldSaved'])
        self.assertFalse(value['nativeClosePassed'])
        self.assertTrue(value['nativeExitVerified'])
        self.assertEqual(value['nativeCrashEvidence'], [{'path':'crash'}])

    def test_native_exit_during_capture_still_saves_mc(self):
        exe = self.folder.parent / 'native.exe'
        exe.write_bytes(b'fixture')
        self.pids.side_effect = [[10], []]
        self.capture.side_effect = psutil.NoSuchProcess(10)
        with patch.object(session, 'EXE', exe), patch.object(session, 'PATCHED_SHA256', hashlib.sha256(b'fixture').hexdigest()), patch.object(session.psutil, 'pid_exists', return_value=False):
            value = self.run_stop()
        self.assertTrue(value['worldSaved'])
        self.assertTrue(value['nativeExitedBeforeCapture'][0]['alreadyExited'])
        self.normal.assert_not_called()

    def test_pid_reuse_during_capture_does_not_stop_either_game(self):
        self.pids.return_value = [10]
        self.capture.side_effect = psutil.NoSuchProcess(10)
        with patch.object(session.psutil, 'pid_exists', return_value=True):
            with self.assertRaisesRegex(ValueError, 'identity changed'):
                self.run_stop()
        self.supervisor.assert_not_called()
        self.api.assert_not_called()

    def test_guest_exits_before_save_no_false_save_claim(self):
        self.guest.is_running.return_value = False
        value = self.run_stop()
        self.assertTrue(value['stopped'])
        self.assertTrue(value['minecraftAlreadyExited'])
        self.assertFalse(value['worldSaved'])
        self.api.assert_not_called()

    def test_opt_in_glfw_normal_close_does_not_claim_save(self):
        self.get_guest.side_effect = RuntimeError('API unavailable; preserved')
        self.identity['windowCloseOnly'] = True
        with patch.object(session, '_guest_window_identity', return_value=self.identity), patch.object(session, '_close_guest_window', return_value=0) as window:
            value = session.stop_session(output_root=self.folder, allow_window_close=True)
        window.assert_called_once_with(self.identity)
        self.assertTrue(value['stopped'])
        self.assertFalse(value['worldSaved'])
        self.assertTrue(value['minecraftSaveUnconfirmed'])
        self.api.assert_not_called()

    def test_crash_cleanup_never_weakens_wrong_guest_identity(self):
        self.get_guest.side_effect = ValueError('identity differs')
        with patch.object(session, '_guest_window_identity') as fallback:
            with self.assertRaisesRegex(ValueError, 'identity differs'):
                session.stop_session(output_root=self.folder, allow_window_close=True)
        fallback.assert_not_called()
        self.supervisor.assert_not_called()


class SelectionTests(unittest.TestCase):
    def setUp(self):
        self.suite = Mock()
        self.suite.result = {}
        self.suite.args.pid = 123
        self.suite.client_size = (1920, 1080)
        self.suite.driver.foreground.return_value = True
        self.suite.driver.send.return_value = 'rect 1920 1080'
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        self.view = self.stack.enter_context(patch.object(selection, 'native_view_state'))
        self.stack.enter_context(patch('calibrate_hero_roster.observe', return_value=dict(hero=0x02e0000000000042, modelId=20)))
        self.stack.enter_context(patch.object(selection.time, 'sleep'))

    def modes(self, *modes):
        self.view.side_effect = [dict(viewMode=m, cameraVtableRva=100+m) for m in modes]

    def sent(self):
        return [call.args[0] for call in self.suite.driver.send.call_args_list]

    def test_ability_camera_after_reinhardt_requests_h_and_proves_picker(self):
        self.modes(0, 2, 2, 2, 1)
        actor = selection.choose(self.suite, 'McCree')
        self.assertEqual(actor['modelId'], 20)
        self.assertEqual(self.sent().count('hold 0x48 150'), 1)
        self.assertEqual(sum(c.startswith('click ') for c in self.sent()), 2)
        self.assertTrue(self.suite.result['selectionDiagnostics'][0]['passed'])

    def test_already_open_picker_is_never_toggled_closed(self):
        self.modes(2, 2, 2, 1)
        selection.choose(self.suite, 'McCree')
        self.assertNotIn('hold 0x48 150', self.sent())

    def test_unknown_camera_never_allows_blind_clicks(self):
        self.view.return_value = dict(viewMode=0)
        with patch.object(selection.time, 'monotonic', side_effect=[0, 11]):
            with self.assertRaisesRegex(ValueError, 'expected mode=2'):
                selection.choose(self.suite, 'McCree')
        self.assertFalse(any(c.startswith('click ') for c in self.sent()))
        self.suite.save.assert_called_once()

    def test_focus_loss_aborts_before_any_input(self):
        self.suite.driver.foreground.return_value = False
        with self.assertRaisesRegex(ValueError, 'interference'):
            selection.choose(self.suite, 'McCree')
        self.suite.driver.send.assert_not_called()

    def test_same_hero_in_ability_camera_is_not_success(self):
        self.modes(2, 2, 2, 0)
        with patch.object(selection.time, 'monotonic', side_effect=[0, 11]):
            with self.assertRaisesRegex(ValueError, 'expected mode=1'):
                selection.choose(self.suite, 'McCree')


class ViewProofTests(unittest.TestCase):
    def test_positive_types_distinguish_picker_default_and_ability_camera(self):
        base = 0x100000
        process = Mock(base=base)
        pointers = {base+0x17b7f90:0x20000, 0x20000+0xb0:0x30000,
                    0x40000:0x50000, 0x50000+0x40:0x60000,
                    0x60000+0x260:0x70000, 0x50000+0x50:0x70000,
                    0x70000:base+0x15c7000}
        reader = Mock()
        reader.pointer.side_effect = pointers.__getitem__
        reader.unpack.return_value = (0x40000, 1, 1)
        with patch.object(selection, 'ResearchProcess', return_value=process), patch.object(selection, 'PoseReader', return_value=reader):
            self.assertEqual(selection.native_view_state(123)['viewMode'], 1)
            pointers[0x70000] = base+0x15f2cf8
            self.assertEqual(selection.native_view_state(123)['viewMode'], 2)
            pointers[0x70000] = base+0x1234
            self.assertEqual(selection.native_view_state(123)['viewMode'], 0)
            pointers[0x70000] = base+0x15c7000
            pointers[0x50000+0x50] = 0x80000
            self.assertEqual(selection.native_view_state(123)['viewMode'], 0)
        self.assertEqual(process.close.call_count, 4)


class GuestWindowCloseTests(unittest.TestCase):
    def setUp(self):
        self.guest = Mock(pid=123)
        self.guest.is_running.return_value = True
        self.guest.create_time.return_value = 100.
        self.guest.exe.return_value = 'C:/runtime/javaw.exe'
        self.guest.cmdline.return_value = ['java', '--gameDir', str(session.PROFILE)]
        self.guest.wait.return_value = 0
        self.identity = dict(process=self.guest, pid=123, creation=100., executable=self.guest.exe())
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        self.windows = self.stack.enter_context(patch('window_layout.windows_for_pid', return_value=[SimpleNamespace(handle=456)]))
        self.stack.enter_context(patch('window_layout._window_class', return_value='GLFW30'))
        self.user = self.stack.enter_context(patch('window_layout.user32'))
        def owner(hwnd, result):
            result._obj.value = 123
            return 1
        self.user.GetWindowThreadProcessId.side_effect = owner
        self.user.PostMessageW.return_value = True

    def test_only_verified_glfw_receives_normal_close(self):
        self.assertEqual(session._close_guest_window(self.identity), 0)
        self.assertEqual(self.user.PostMessageW.call_args.args[1:], (0x0010, 0, 0))
        self.guest.wait.assert_called_once_with(45)
        self.guest.kill.assert_not_called()
        self.guest.terminate.assert_not_called()

    def test_changed_creation_before_post_receives_no_close(self):
        self.guest.create_time.side_effect = [100., 101.]
        with self.assertRaisesRegex(ValueError, 'identity changed'):
            session._close_guest_window(self.identity)
        self.user.PostMessageW.assert_not_called()

    def test_changed_window_pid_receives_no_close(self):
        def other(hwnd, result):
            result._obj.value = 124
            return 1
        self.user.GetWindowThreadProcessId.side_effect = other
        with self.assertRaisesRegex(ValueError, 'window owner changed'):
            session._close_guest_window(self.identity)
        self.user.PostMessageW.assert_not_called()

    def test_ambiguous_windows_receive_no_close(self):
        self.windows.return_value = [SimpleNamespace(handle=456), SimpleNamespace(handle=457)]
        with self.assertRaisesRegex(RuntimeError, 'unique Minecraft GLFW'):
            session._close_guest_window(self.identity)
        self.user.PostMessageW.assert_not_called()

    def test_timeout_has_no_force_fallback(self):
        self.guest.wait.side_effect = psutil.TimeoutExpired(45)
        with self.assertRaises(psutil.TimeoutExpired):
            session._close_guest_window(self.identity)
        self.guest.kill.assert_not_called()
        self.guest.terminate.assert_not_called()


class CrashTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.profile = self.root / 'guest-passthrough-client'
        self.reports = self.profile / 'crash-reports'
        self.reports.mkdir(parents=True)
        self.log = self.profile / 'logs/latest.log'
        self.log.parent.mkdir()
        self.log.write_text('old Crash report saved to: historic\n')
        self.report = self.reports / 'crash-old-client.txt'
        self.report.write_text('Description: historic\n')
        self.baseline = crash.snapshot(self.root)

    def test_old_report_and_log_are_ignored(self):
        self.assertEqual(crash.detect(self.baseline), [])
        with self.log.open('a') as stream:
            stream.write('ordinary log tail\n')
        self.assertEqual(crash.detect(self.baseline), [])

    def test_new_client_report_is_retained_with_description(self):
        report = self.reports / 'crash-now-client.txt'
        report.write_text('Description: Rendering entity in world\njava.lang.NullPointerException: HostPoseReader\n')
        found = crash.detect(self.baseline)
        self.assertEqual(len(found), 1)
        self.assertIn('Rendering entity', found[0]['description'])
        self.assertEqual(found[0]['kind'], 'mc-client-crash')

    def test_rewritten_report_and_jvm_fatal_are_detected(self):
        self.report.write_text('Description: new error, same path\n')
        (self.root / 'hs_err_pid123.log').write_text('fatal JVM fixture')
        self.assertEqual({r['kind'] for r in crash.detect(self.baseline)}, {'mc-client-crash', 'jvm-crash'})

    def test_append_and_rotated_log_markers_are_detected(self):
        with self.log.open('a') as stream:
            stream.write('Reported exception thrown!\n')
        self.assertEqual(crash.detect(self.baseline)[0]['kind'], 'mc-crash-log')
        self.log.unlink()
        self.log.write_text('Crash report saved to: now\n')
        self.assertEqual(crash.detect(self.baseline)[0]['kind'], 'mc-crash-log')

    def test_server_report_does_not_falsely_claim_client_crash(self):
        (self.reports / 'crash-now-server.txt').write_text('server fixture')
        self.assertEqual(crash.detect(self.baseline), [])

    def test_guest_recovery_does_not_restart_after_crash(self):
        native = Mock()
        native.is_running.return_value = False
        evidence = [{'path': 'fixture-client-crash'}]
        with patch.object(supervisor.psutil, 'Process', return_value=native), patch.object(supervisor, 'minecraft_snapshot', return_value={}), patch.object(supervisor, 'minecraft_crashes', return_value=evidence), patch.object(supervisor, 'launch_guest') as launch, patch.object(supervisor, 'write_status'):
            recovery = supervisor.GuestRecovery({'sourcePid': 12})
            record = {'settings': {}}
            with self.assertRaises(crash.MinecraftCrashError):
                recovery.recover(record)
        launch.assert_not_called()
        self.assertEqual(record['phase'], 'minecraft-crashed')
        self.assertEqual(record['minecraftCrashEvidence'], evidence)

    def test_cycle_records_crash_and_normal_cleanup_without_force(self):
        state, output = self.root/'baseline.json', self.root/'crash.json'
        state.write_text(json.dumps(self.baseline))
        (self.reports/'crash-now-client.txt').write_text('Description: fixture crash')
        with redirect_stdout(io.StringIO()):
            self.assertTrue(cycle.check_crash(state, output))
            with patch.object(cycle.subprocess, 'run', return_value=SimpleNamespace(returncode=0)) as run, patch.object(cycle, 'project_processes', return_value=[]):
                self.assertEqual(cycle.normal_cleanup(self.root), 0)
        self.assertEqual(run.call_count, 1)
        self.assertIn('crash-stop', run.call_args.args[0])
        self.assertFalse(json.loads(output.read_text())['forcedTermination'])
        self.assertFalse(json.loads((self.root/'cleanup-result.json').read_text())['forcedTermination'])

    def test_launcher_crash_stop_is_explicit_and_still_uses_established_stop(self):
        backend = launcher.SessionBackend(self.root)
        with patch.object(backend, 'checked_command', return_value={}) as command:
            launcher.execute_action(backend, 'crash-stop', self.root/'stop.log')
        self.assertEqual(command.call_args.args[0][-2:], [str(self.root/'tools/stop_passthrough_session.py'), '--allow-window-close'])

    def test_unrelated_java_and_fake_native_name_are_ignored(self):
        def process(pid, exe, args):
            p = Mock(pid=pid)
            p.info = dict(exe=str(exe), cmdline=args)
            p.create_time.return_value = 100.
            return p
        unrelated = process(1, self.root/'java.exe', ['java', '--gameDir', str(self.root/'other')])
        fake_native = process(2, self.root/'GameClientApp.patched.exe', [])
        actual = process(3, self.root/'javaw.exe', ['java', '--gameDir', str(cycle.ROOT/'guest-passthrough-client')])
        with patch.object(cycle.psutil, 'process_iter', return_value=[unrelated, fake_native, actual]):
            self.assertEqual([p['pid'] for p in cycle.project_processes()], [3])

    def test_pretest_backup_copies_stopped_profiles_including_saves(self):
        save = self.profile/'saves/world/level.dat'
        save.parent.mkdir(parents=True)
        save.write_bytes(b'fixture-save')
        logs = self.root/'research/dev-cycle'
        with patch.object(cycle, 'ROOT', self.root), patch.object(cycle, 'project_processes', return_value=[]), redirect_stdout(io.StringIO()):
            receipt = cycle.backup_profiles(logs)
        self.assertEqual((Path(receipt['directory'])/'guest-passthrough-client/saves/world/level.dat').read_bytes(), b'fixture-save')
        self.assertEqual(save.read_bytes(), b'fixture-save')
        self.assertTrue(receipt['stoppedBeforeBackup'])

    def test_backup_refuses_to_copy_a_running_profile(self):
        logs = self.root/'research/dev-cycle'
        with patch.object(cycle, 'project_processes', return_value=[{'pid':123}]):
            with self.assertRaisesRegex(RuntimeError, '游戏仍在运行'):
                cycle.backup_profiles(logs)
        self.assertFalse(logs.exists())

    def run_cycle_fixture(self, *, code, checks):
        self.guest = Mock(pid=20)
        self.guest.cmdline.return_value = ['java', '--gameDir', str(supervisor.PROFILE)]
        self.guest.exe.return_value = 'C:/runtime/javaw.exe'
        self.guest.create_time.return_value = 2.
        self.child = Mock(returncode=code)
        self.child.poll.return_value = code
        if checks == [False, True]:
            self.child.poll.return_value = None
        self.arguments = SimpleNamespace(state='unused', crash_output='unused', logs=str(self.root),
                                         test='a test with spaces $(literal).py', evidence='output with spaces')
        with ExitStack() as stack, redirect_stdout(io.StringIO()):
            stack.enter_context(patch.object(cycle, 'check_crash', side_effect=checks))
            self.cleanup = stack.enter_context(patch.object(cycle, 'normal_cleanup', return_value=0))
            self.popen = stack.enter_context(patch.object(cycle.subprocess, 'Popen', return_value=self.child))
            stack.enter_context(patch.object(supervisor, 'native_pids', return_value=[10]))
            stack.enter_context(patch.object(supervisor, 'api', return_value=dict(sourcePid=20, mode='full-world-frame-proof', worldName='world with spaces')))
            stack.enter_context(patch.object(close, 'capture_native_identity', return_value=dict(pid=10, creation=1.)))
            stack.enter_context(patch.object(cycle.psutil, 'Process', return_value=self.guest))
            stack.enter_context(patch.object(Path, 'read_bytes', return_value=b'fixture-jar'))
            result = cycle.run_test(self.arguments)
        return result

    def test_real_test_exit_code_and_literal_arguments_are_preserved(self):
        self.assertEqual(self.run_cycle_fixture(code=7, checks=[False, False]), 7)
        self.assertIn(self.arguments.test, self.popen.call_args.args[0])
        self.assertIn('world with spaces', self.popen.call_args.args[0])
        self.assertNotIn('shell', self.popen.call_args.kwargs)
        self.cleanup.assert_not_called()  # shell caller owns non-crash cleanup

    def test_crash_during_test_normally_cleans_and_returns_four(self):
        self.assertEqual(self.run_cycle_fixture(code=0, checks=[False, True]), 4)
        self.cleanup.assert_called_once_with(str(self.root))
        self.child.wait.assert_called_once_with(20)


if __name__ == '__main__':
    unittest.main()
