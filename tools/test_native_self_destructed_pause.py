"""Terminal atexit pause regressions; every process/window/console is a fixture."""
import json
from pathlib import Path
import unittest
from unittest.mock import Mock, patch

import psutil
import native_normal_close as close
import test_native_normal_close as existing
import verify_provided_shutdown_abi as protected


TEXT = 'Process exit initiazed: 0\nshutdown\n请按任意键继续. . .'


class TerminalPauseTests(unittest.TestCase):
    def setUp(self):
        self.fixture = existing.NormalCloseTests('test_complete_restoration_before_original_close')
        self.fixture.setUp()
        self.addCleanup(self.fixture.tearDown)
        self.native = Mock()
        self.native.create_time.return_value = self.fixture.identity['creation']
        self.native.exe.return_value = self.fixture.identity['executable']
        self.native.is_running.return_value = True
        self.process = patch.object(close.psutil, 'Process', return_value=self.native)
        self.process.start(); self.addCleanup(self.process.stop)
        self.windows = patch.object(close, 'native_top_level_windows', return_value=[dict(hwnd=7,className='ConsoleWindowClass')])
        self.window_query = self.windows.start(); self.addCleanup(self.windows.stop)
        self.primitives = self.fixture.primitives
        self.primitives.acknowledge_shutdown_pause.return_value = dict(
            acknowledged=True, consolePids=[10], observedText=TEXT, globalKeyboardInput=False)

    def assert_no_restore_or_snapshot(self):
        self.primitives.snapshot.assert_not_called()
        self.primitives.close_window.assert_not_called()
        self.fixture.mocks[4].assert_not_called()  # ResearchProcess
        self.fixture.mocks[7].assert_not_called()  # stop callback owners
        self.fixture.mocks[8].assert_not_called()  # inventory callback owners

    def test_console_only_terminal_pause_exits_without_touching_destroyed_admin(self):
        result = self.fixture.run_close()
        self.assertEqual(result['nativeExitClassification'],'native-self-destructed-paused')
        self.assertTrue(result['normalClosePassed'])
        self.assertTrue(result['ownerRestorationSkipped'])
        self.assertFalse(result['requestedNormalClose'])
        self.assertFalse(result['forcedTermination'])
        self.assertEqual(result['restoration'],{})
        self.assertEqual(result['shutdownPause']['observedText'],TEXT)
        self.primitives.acknowledge_shutdown_pause.assert_called_once_with(10,1.,0)
        self.fixture.waiter.wait.assert_called_once_with(20)
        self.fixture.waiter.close.assert_called_once()
        self.assert_no_restore_or_snapshot()
        self.assertEqual(self.window_query.call_count,2)
        saved=json.loads((self.fixture.root/'result/result.json').read_text())
        self.assertEqual(saved,result)

    def test_no_owned_window_still_requires_positive_console_proof(self):
        # Console host HWND may belong to conhost, so an empty owned list is
        # eligible only because the protected primitive proves console PID/text.
        self.window_query.return_value=[]
        result=self.fixture.run_close()
        self.assertEqual(result['nativeExitClassification'],'native-self-destructed-paused')
        self.primitives.acknowledge_shutdown_pause.assert_called_once_with(10,1.,0)
        self.assert_no_restore_or_snapshot()

    def test_any_non_console_window_preserves_normal_restore_and_close(self):
        self.window_query.return_value=[dict(hwnd=7,className='ConsoleWindowClass'),dict(hwnd=8,className='RenderWindow')]
        result=self.fixture.run_close()
        self.assertEqual(result['nativeExitClassification'],'normal-close')
        self.primitives.acknowledge_shutdown_pause.assert_not_called()
        self.assertEqual(self.primitives.snapshot.call_count,2)
        self.assertEqual(self.fixture.mocks[7].call_count,4)
        self.primitives.close_window.assert_called_once_with(10)

    def test_window_appearing_during_crash_check_prevents_early_ack(self):
        self.window_query.side_effect=[[],[dict(hwnd=8,className='HiddenOrZeroAreaWindow')]]
        self.assertEqual(self.fixture.run_close()['nativeExitClassification'],'normal-close')
        self.primitives.acknowledge_shutdown_pause.assert_not_called()

    def test_unverified_console_text_falls_back_without_labeling_terminal_success(self):
        self.primitives.acknowledge_shutdown_pause.side_effect=ValueError('No verified original shutdown pause; no input sent')
        result=self.fixture.run_close()
        self.assertEqual(result['nativeExitClassification'],'normal-close')
        self.assertIn('notPaused',result['selfDestructedPauseProbe'])
        self.assertEqual(self.primitives.snapshot.call_count,2)

    def test_crash_before_ack_blocks_all_input(self):
        self.fixture.mocks[6].return_value=[{'path':'matching-current-crash'}]
        result=self.fixture.failed()
        self.assertEqual(result['nativeExitClassification'],'crash-report')
        self.primitives.acknowledge_shutdown_pause.assert_not_called()
        self.assert_no_restore_or_snapshot()

    def test_crash_evidence_unavailable_blocks_input(self):
        self.fixture.mocks[6].side_effect=OSError('crash evidence unavailable')
        result=self.fixture.failed()
        self.assertEqual(result['nativeExitClassification'],'evidence-unavailable')
        self.primitives.acknowledge_shutdown_pause.assert_not_called()
        self.assert_no_restore_or_snapshot()

    def test_crash_after_ack_cannot_be_terminal_success(self):
        self.fixture.mocks[6].side_effect=[[],[{'path':'late-report'}]]
        result=self.fixture.failed()
        self.assertEqual(result['nativeExitClassification'],'crash-report')
        self.assertFalse(result['normalClosePassed'])
        self.assert_no_restore_or_snapshot()

    def test_creation_change_before_probe_blocks_input(self):
        self.native.create_time.return_value=2.
        self.assertIn('identity changed',self.fixture.failed()['error'])
        self.primitives.acknowledge_shutdown_pause.assert_not_called()
        self.window_query.assert_not_called()
        self.assert_no_restore_or_snapshot()

    def test_identity_recheck_before_ack_blocks_input(self):
        self.fixture.mocks[1].side_effect=[None,ValueError('identity changed before console acknowledgement')]
        self.fixture.failed()
        self.primitives.acknowledge_shutdown_pause.assert_not_called()
        self.assert_no_restore_or_snapshot()

    def test_unknown_window_inventory_blocks_input(self):
        self.window_query.side_effect=RuntimeError('window class unavailable')
        self.fixture.failed()
        self.primitives.acknowledge_shutdown_pause.assert_not_called()
        self.assert_no_restore_or_snapshot()

    def test_nonzero_exit_is_not_terminal_success(self):
        self.fixture.waiter.wait.return_value=5
        self.assertEqual(self.fixture.failed()['nativeExitClassification'],'normal-close-failed')
        self.assert_no_restore_or_snapshot()

    def test_pause_exit_timeout_has_no_force_fallback(self):
        self.fixture.waiter.wait.side_effect=psutil.TimeoutExpired(20)
        result=self.fixture.failed()
        self.assertFalse(result['forcedTermination'])
        self.assertEqual(result['nativeExitClassification'],'normal-close-failed')
        self.assert_no_restore_or_snapshot()

    def test_acknowledgement_must_retain_verified_text_and_console_identity(self):
        self.primitives.acknowledge_shutdown_pause.return_value['consolePids']=[11]
        self.assertIn('evidence is incomplete',self.fixture.failed()['error'])
        self.fixture.waiter.wait.assert_not_called()
        self.assert_no_restore_or_snapshot()

    def test_verifier_hash_guard_runs_before_terminal_probe(self):
        self.fixture.mocks[2].side_effect=ValueError('Accepted normal-close verifier identity differs')
        self.fixture.failed()
        self.window_query.assert_not_called()
        self.primitives.acknowledge_shutdown_pause.assert_not_called()


class WindowInventoryTests(unittest.TestCase):
    def user(self, rows):
        user=Mock()
        def enumerate_windows(callback,argument):
            return all(callback(hwnd,argument) for hwnd in rows)
        def owner(hwnd,result):
            result._obj.value=rows[hwnd][0]
            return 1
        def class_name(hwnd,buffer,size):
            buffer.value=rows[hwnd][1]
            return len(buffer.value)
        user.EnumWindows.side_effect=enumerate_windows
        user.GetWindowThreadProcessId.side_effect=owner
        user.GetClassNameW.side_effect=class_name
        return user

    def test_inventory_includes_hidden_and_zero_area_windows(self):
        user=self.user({7:(10,'ConsoleWindowClass'),8:(10,'HiddenRenderWindow'),9:(11,'Unrelated')})
        with patch.object(close.ctypes,'WinDLL',return_value=user):
            rows=close.native_top_level_windows(10)
        self.assertEqual(rows,[dict(hwnd=7,className='ConsoleWindowClass'),dict(hwnd=8,className='HiddenRenderWindow')])
        user.IsWindowVisible.assert_not_called()
        user.GetClientRect.assert_not_called()

    def test_callback_class_failure_cannot_look_like_empty_inventory(self):
        user=self.user({7:(10,'')})
        with patch.object(close.ctypes,'WinDLL',return_value=user):
            with self.assertRaisesRegex(RuntimeError,'class unavailable'):
                close.native_top_level_windows(10)

    def test_callback_owner_failure_cannot_look_like_empty_inventory(self):
        user=self.user({7:(10,'ConsoleWindowClass')})
        user.GetWindowThreadProcessId.side_effect=None
        user.GetWindowThreadProcessId.return_value=0
        with patch.object(close.ctypes,'WinDLL',return_value=user):
            with self.assertRaisesRegex(RuntimeError,'owner unavailable'):
                close.native_top_level_windows(10)

    def test_callback_exception_cannot_be_discarded_as_empty_inventory(self):
        user=self.user({7:(10,'ConsoleWindowClass')})
        user.GetClassNameW.side_effect=OSError('fixture window read failed')
        with patch.object(close.ctypes,'WinDLL',return_value=user):
            with self.assertRaisesRegex(RuntimeError,'enumeration callback failed'):
                close.native_top_level_windows(10)


class ProtectedConsoleTests(unittest.TestCase):
    def acknowledge(self,text,*,console_pid=10):
        user,kernel=Mock(),Mock()
        user.IsWindow.return_value=False
        kernel.AttachConsole.return_value=True
        def console_ids(ids,capacity):
            ids[0]=console_pid
            return 1
        kernel.GetConsoleProcessList.side_effect=console_ids
        kernel.CreateFileW.side_effect=[101,102]
        def screen(handle,result):
            result._obj.size.x=120;result._obj.cursor.y=5
            return True
        kernel.GetConsoleScreenBufferInfo.side_effect=screen
        def read(handle,buffer,size,coordinate,received):
            buffer.value=text;received._obj.value=len(text)
            return True
        kernel.ReadConsoleOutputCharacterW.side_effect=read
        def write(handle,events,count,sent):
            sent._obj.value=count
            return True
        kernel.WriteConsoleInputW.side_effect=write
        native=Mock();native.create_time.return_value=1.
        native.exe.return_value=str(protected.ROOT/'overwatch-2015/Overwatch Beta 0.8.0.24919/GameClientApp.patched.exe')
        self.kernel=kernel
        def dll(name,**kwargs):
            return user if name=='user32' else kernel
        with patch.object(protected.ctypes,'WinDLL',side_effect=dll),patch.object(protected.psutil,'Process',return_value=native):
            return protected.acknowledge_shutdown_pause(10,1.,0)

    def test_unchanged_protected_primitive_observes_before_exact_console_return(self):
        result=self.acknowledge(TEXT)
        self.assertEqual(result['observedText'],TEXT)
        self.assertFalse(result['globalKeyboardInput'])
        self.assertEqual(self.kernel.WriteConsoleInputW.call_args.args[0],102)
        self.assertEqual(self.kernel.WriteConsoleInputW.call_args.args[2],2)

    def test_each_required_text_marker_is_checked_before_input(self):
        for marker in ('Process exit initiazed: 0','shutdown','请按任意键'):
            with self.subTest(missing=marker):
                with self.assertRaisesRegex(ValueError,'No verified original shutdown pause'):
                    self.acknowledge(TEXT.replace(marker,''))
                self.kernel.WriteConsoleInputW.assert_not_called()

    def test_other_console_cannot_receive_input(self):
        with self.assertRaisesRegex(ValueError,'does not own this native identity'):
            self.acknowledge(TEXT,console_pid=11)
        self.kernel.WriteConsoleInputW.assert_not_called()


if __name__=='__main__':
    unittest.main()
