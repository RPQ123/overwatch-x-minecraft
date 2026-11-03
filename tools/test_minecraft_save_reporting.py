"""Offline save reporting and automatic-exit journals; no live game access."""
from contextlib import ExitStack, redirect_stdout
import io
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch
import psutil

import minecraft_save_evidence as evidence
import stop_passthrough_session as session
import launch_passthrough_session as supervisor
import test_stop_passthrough_session as existing

WORLD='fixture world'
SAVE=('Stopping server\nSaving players\nSaving worlds\n'
      "Saving chunks for level 'ServerLevel[fixture world]'/minecraft:overworld\n"
      'ThreadedAnvilChunkStorage: All dimensions are saved\n')


class SaveEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.profile=Path(self.temp.name)/'profile';self.log=self.profile/'logs/latest.log'
        self.log.parent.mkdir(parents=True);self.log.write_text('client startup fixture\n')

    def append(self,text):
        with self.log.open('a',encoding='utf-8') as stream:stream.write(text)

    def test_new_complete_save_sequence_proves_current_shutdown(self):
        baseline=evidence.capture(self.profile,WORLD);self.append(SAVE)
        self.assertTrue(evidence.inspect(baseline)['complete'])

    def test_old_save_markers_never_confirm_a_second_stop(self):
        self.append(SAVE);baseline=evidence.capture(self.profile,WORLD)
        self.assertFalse(evidence.inspect(baseline)['complete'])

    def test_world_identity_and_completion_marker_are_required(self):
        baseline=evidence.capture(self.profile,'other world');self.append(SAVE)
        self.assertFalse(evidence.inspect(baseline)['complete'])

    def test_partial_save_is_unconfirmed(self):
        baseline=evidence.capture(self.profile,WORLD);self.append(SAVE.replace('All dimensions are saved','saving in progress'))
        self.assertFalse(evidence.inspect(baseline)['complete'])

    def test_rotated_or_rewritten_log_cannot_reuse_old_completion(self):
        baseline=evidence.capture(self.profile,WORLD)
        self.log.write_text('a different client log\n'+SAVE,encoding='utf-8')
        result=evidence.inspect(baseline)
        self.assertFalse(result['complete']);self.assertTrue(result['logs'][0]['streamChanged'])

    def test_save_error_blocks_success_even_after_completion_marker(self):
        baseline=evidence.capture(self.profile,WORLD);self.append(SAVE+'[Server thread/ERROR]: Failed to save chunk 1,2\n')
        result=evidence.inspect(baseline)
        self.assertFalse(result['complete']);self.assertTrue(result['saveErrors'])


class StopSaveReportingTests(unittest.TestCase):
    def setUp(self):
        self.fixture=existing.StopSessionTests('test_absent_guest_native_only');self.fixture.setUp()
        self.addCleanup(self.fixture.stack.close);self.addCleanup(self.fixture.temporary.cleanup)
        self.stack=ExitStack();self.addCleanup(self.stack.close)
        self.profile=Path(self.fixture.temporary.name)/'profile'
        self.log=self.profile/'logs/latest.log';self.log.parent.mkdir(parents=True);self.log.write_text('client startup\n')
        self.stack.enter_context(patch.object(session,'PROFILE',self.profile))
        self.fixture.identity['worldName']=WORLD
        self.fixture.guest.cmdline.return_value=['java','--gameDir',str(self.profile)]
        self.fixture.api.side_effect=self.api

    def append(self,text=SAVE):
        with self.log.open('a',encoding='utf-8') as stream:stream.write(text)

    def api(self,route,post=False):
        if route=='health':return dict(sourcePid=123,mode='full-world-frame-proof',worldName=WORLD)
        self.append();return {'accepted':True}

    def run_stop(self,*,window=False):
        with redirect_stdout(io.StringIO()):
            return session.stop_session(output_root=self.fixture.folder,allow_window_close=window)

    def test_empty_session_reports_not_requested_instead_of_failed_save(self):
        self.fixture.get_guest.return_value=None
        self.append()  # an old successful save must not be borrowed
        result=self.run_stop()
        self.assertIsNone(result['worldSaved'])
        self.assertEqual(result['worldSaveStatus'],'not-requested-no-live-guest')
        self.assertTrue(result['minecraftAbsentAtStop'])
        self.assertFalse(result['minecraftShutdownRequested'])
        self.assertEqual(result['nativeStopAction'],'none-already-absent')
        self.fixture.normal.assert_not_called();self.fixture.api.assert_not_called()

    def test_normal_api_save_keeps_scoped_world_completion_proof(self):
        result=self.run_stop()
        self.assertTrue(result['worldSaved']);self.assertTrue(result['minecraftSaveLogVerified'])
        self.assertEqual(result['worldSaveStatus'],'saved-log-confirmed')
        self.assertEqual(result['minecraftIdentity']['pid'],123)
        self.assertEqual(result['minecraftIdentity']['worldName'],WORLD)
        self.fixture.guest.wait.assert_called_once_with(45)

    def test_repeated_stop_does_not_claim_another_save(self):
        self.assertTrue(self.run_stop()['worldSaved'])
        self.fixture.folder=Path(self.fixture.temporary.name)/'second-stop'
        self.fixture.get_guest.return_value=None;self.fixture.api.reset_mock()
        result=self.run_stop()
        self.assertIsNone(result['worldSaved'])
        self.assertEqual(result['worldSaveStatus'],'not-requested-no-live-guest')
        self.fixture.api.assert_not_called()

    def window_stop(self,*,complete):
        self.fixture.get_guest.side_effect=RuntimeError('HTTP unavailable; preserved')
        self.fixture.identity['windowCloseOnly']=True
        def close(identity):
            if complete:self.append()
            return 0
        with patch.object(session,'_guest_window_identity',return_value=self.fixture.identity),patch.object(session,'_close_guest_window',side_effect=close):
            return self.run_stop(window=True)

    def test_normal_glfw_close_with_actual_save_log_is_confirmed(self):
        result=self.window_stop(complete=True)
        self.assertTrue(result['worldSaved']);self.assertFalse(result['minecraftSaveUnconfirmed'])
        self.assertEqual(result['worldSaveStatus'],'saved-log-confirmed')

    def test_glfw_exit_zero_alone_is_unknown_not_save_failure_or_success(self):
        result=self.window_stop(complete=False)
        self.assertIsNone(result['worldSaved']);self.assertTrue(result['minecraftSaveUnconfirmed'])
        self.assertEqual(result['worldSaveStatus'],'unconfirmed-normal-window-exit')

    def test_http_transport_failure_uses_only_verified_normal_window_fallback(self):
        def broken(route,post=False):
            if route=='shutdown':raise OSError('fixture dropped HTTP reply')
            return dict(sourcePid=123,mode='full-world-frame-proof')
        self.fixture.api.side_effect=broken
        with patch.object(session,'_close_guest_window',side_effect=lambda identity:(self.append() or 0)) as close:
            result=self.run_stop(window=True)
        close.assert_called_once_with(self.fixture.identity)
        self.assertTrue(result['worldSaved'])
        self.assertIn('dropped HTTP reply',result['minecraftShutdownRequestError'])
        self.assertEqual(result['minecraftCloseMethod'],'verified-GLFW-after-HTTP-error')
        self.fixture.guest.terminate.assert_not_called();self.fixture.guest.kill.assert_not_called()

    def test_http_transport_failure_without_opt_in_remains_explicit(self):
        def broken(route,post=False):
            if route=='shutdown':raise OSError('fixture reply lost')
            return dict(sourcePid=123,mode='full-world-frame-proof')
        self.fixture.api.side_effect=broken
        with self.assertRaises(OSError),redirect_stdout(io.StringIO()):self.run_stop()
        result=json.loads((self.fixture.folder/'session-result.json').read_text())
        self.assertIsNone(result['worldSaved']);self.assertEqual(result['worldSaveStatus'],'unconfirmed-shutdown-failed')
        self.assertIn('reply lost',result['minecraftSaveError'])

    def test_explicit_shutdown_refusal_is_not_a_success(self):
        self.fixture.api.side_effect=lambda route,post=False:({'accepted':False} if route=='shutdown' else dict(sourcePid=123,mode='full-world-frame-proof'))
        with self.assertRaisesRegex(ValueError,'refused'):self.run_stop()
        self.fixture.guest.wait.assert_not_called()

    def test_guest_dying_before_save_is_recorded_as_unknown(self):
        self.fixture.guest.is_running.return_value=False
        result=self.run_stop()
        self.assertIsNone(result['worldSaved']);self.assertTrue(result['minecraftAlreadyExited'])
        self.assertEqual(result['worldSaveStatus'],'unconfirmed-already-exited')
        self.fixture.api.assert_not_called()

    def test_guest_already_exited_but_own_appended_completion_can_be_confirmed(self):
        self.fixture.guest.is_running.return_value=False
        self.fixture.supervisor.side_effect=self.append
        result=self.run_stop()
        self.assertTrue(result['worldSaved']);self.assertTrue(result['minecraftAlreadyExited'])
        self.assertEqual(result['worldSaveStatus'],'saved-log-confirmed')

    def test_save_error_is_not_hidden_by_zero_exit(self):
        def save_error(route,post=False):
            if route=='shutdown':
                self.append(SAVE+'[Server thread/ERROR]: Failed to save world fixture\n');return {'accepted':True}
            return dict(sourcePid=123,mode='full-world-frame-proof')
        self.fixture.api.side_effect=save_error
        with self.assertRaisesRegex(RuntimeError,'save errors'):self.run_stop()
        result=json.loads((self.fixture.folder/'session-result.json').read_text())
        self.assertFalse(result['worldSaved']);self.assertFalse(result['minecraftKeptRunning'])
        self.assertEqual(result['worldSaveStatus'],'failed-save-log-error')


class SupervisorExitJournalTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.profile=self.root/'profile'
        self.log=self.profile/'logs/latest.log';self.log.parent.mkdir(parents=True);self.log.write_text('client startup\n')
        self.stack=ExitStack();self.addCleanup(self.stack.close)
        self.stack.enter_context(patch.object(supervisor,'PROFILE',self.profile))
        self.process=Mock(pid=123);self.process.is_running.return_value=True
        self.process.exe.return_value='C:/runtime/java.exe';self.process.create_time.return_value=1.
        self.process.cmdline.return_value=['java','--gameDir',str(self.profile)]
        self.process.wait.return_value=0
        self.recovery=SimpleNamespace(identity=self.process,guest={'sourcePid':123})
        self.record=dict(nativePid=456,nativeCreation=2.,nativeExitCode=0,nativeExitObservedMs=3000,nativeExitClassification='process-exit-unclassified')
        self.api_mock=self.stack.enter_context(patch.object(supervisor,'api',side_effect=self.api))

    def api(self,route,post=False):
        if route=='health':return dict(sourcePid=123,mode='full-world-frame-proof',worldName=WORLD)
        with self.log.open('a') as stream:stream.write(SAVE)
        return {'accepted':True}

    def finish(self):
        return supervisor.finish_guest_after_native_exit(self.recovery,self.record,output=self.root/'exit.json')

    def test_automatic_save_provenance_is_persisted_before_next_stop(self):
        result=self.finish()
        self.assertTrue(result['worldSaved']);self.assertEqual(result['worldSaveStatus'],'saved-log-confirmed')
        self.assertFalse(result['nativeCloseRequested'])
        self.assertEqual(result['nativeExitTrigger'],'unknown-not-instrumented')
        self.assertEqual(json.loads((self.root/'exit.json').read_text()),result)
        self.assertEqual(self.record['nativeExitReceipt'],str(self.root/'exit.json'))
        self.process.wait.assert_called_once_with(45)

    def test_automatic_http_error_is_no_longer_swallowed_or_marked_stopped(self):
        def broken(route,post=False):
            if route=='shutdown':raise OSError('fixture HTTP save error')
            return dict(sourcePid=123,mode='full-world-frame-proof',worldName=WORLD)
        self.api_mock.side_effect=broken
        result=self.finish()
        self.assertIsNone(result['worldSaved']);self.assertIn('HTTP save error',result['minecraftSaveError'])
        self.assertFalse(self.record['stopped']);self.assertTrue(result['minecraftKeptRunning'])
        self.process.terminate.assert_not_called();self.process.kill.assert_not_called()

    def test_other_http_source_is_preserved(self):
        self.api_mock.return_value=dict(sourcePid=999,mode='full-world-frame-proof');self.api_mock.side_effect=None
        result=self.finish()
        self.assertIsNone(result['worldSaved'])
        self.assertEqual([call.args[0] for call in self.api_mock.call_args_list],['health'])
        self.process.wait.assert_not_called()

    def test_absent_guest_does_not_borrow_historic_save_or_call_api(self):
        self.process.is_running.return_value=False
        result=self.finish()
        self.assertIsNone(result['worldSaved']);self.assertEqual(result['worldSaveStatus'],'not-requested-no-live-guest')
        self.api_mock.assert_not_called()

    def test_unreadable_guest_identity_is_recorded_without_assuming_exit(self):
        self.process.is_running.side_effect=psutil.AccessDenied(123)
        result=self.finish()
        self.assertIsNone(result['worldSaved']);self.assertIsNone(result['minecraftKeptRunning'])
        self.assertFalse(self.record['stopped'])
        self.assertIn('AccessDenied',result['minecraftIdentityError'])
        self.assertTrue((self.root/'exit.json').is_file())
        self.api_mock.assert_not_called()


if __name__=='__main__':unittest.main()
