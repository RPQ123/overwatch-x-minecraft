"""Stop/restart policy fixtures: no games or real process control."""
from contextlib import ExitStack
from pathlib import Path
import tempfile,unittest
from unittest.mock import Mock,patch
import psutil
import stop_passthrough_session as session

class StopSessionTests(unittest.TestCase):
    def setUp(self):
        self.temporary=tempfile.TemporaryDirectory();self.folder=Path(self.temporary.name)/'stop'
        self.stack=ExitStack();self.addCleanup(self.temporary.cleanup);self.addCleanup(self.stack.close)
        self.guest=Mock(pid=123);self.guest.exe.return_value='C:/runtime/javaw.exe'
        self.guest.cmdline.return_value=['java','--gameDir',str(session.PROFILE)]
        self.guest.create_time.return_value=100;self.guest.is_running.return_value=True
        self.guest.wait.return_value=0
        self.identity=dict(process=self.guest,pid=123,creation=100,executable='C:/runtime/javaw.exe');self.status=[]
        self.pids=self.stack.enter_context(patch.object(session,'native_pids',return_value=[]))
        self.capture=self.stack.enter_context(patch.object(session,'capture_native_identity',return_value={'pid':10}))
        self.get_guest=self.stack.enter_context(patch.object(session,'_guest_identity',return_value=self.identity))
        self.supervisor=self.stack.enter_context(patch.object(session,'stop_supervisor'))
        self.desktop=self.stack.enter_context(patch.object(session,'restore_display',return_value=dict(restored=True)))
        self.api=self.stack.enter_context(patch.object(session,'api',return_value={'sourcePid':123,'mode':'full-world-frame-proof'}))
        self.normal=self.stack.enter_context(patch.object(session,'normal_close',return_value=dict(exitCode=0,nativeExitClassification='normal-close',crashReports=[],passed=True,normalClosePassed=True)))
        self.stack.enter_context(patch.object(session,'write_status',side_effect=lambda value:self.status.append(dict(value))))
    def run_stop(self,keep=False):return session.stop_session(keep,output_root=self.folder)
    def test_default_saves_only_after_normal_native_exit(self):
        self.pids.return_value=[10]
        def done(*args):self.assertFalse(any(c.args==('shutdown',True) for c in self.api.call_args_list));return self.normal.return_value
        self.normal.side_effect=done;value=self.run_stop();self.assertTrue(value['stopped']);self.assertTrue(value['worldSaved'])
        self.capture.assert_called_once_with(10);self.normal.assert_called_once();self.guest.wait.assert_called_once_with(45);self.guest.terminate.assert_not_called()
        self.assertEqual(self.api.call_args_list[-1].args,('shutdown',True))
    def test_keep_guest(self):
        value=self.run_stop(True);self.assertTrue(value['minecraftKeptRunning']);self.assertFalse(value['worldSaved'])
        self.api.assert_not_called();self.guest.wait.assert_not_called();self.supervisor.assert_called_once()
    def test_display_restores_only_after_normal_native_exit(self):
        self.pids.return_value=[10]
        self.normal.side_effect=lambda *a: (self.desktop.assert_not_called() or self.normal.return_value)
        value=self.run_stop(True)
        self.desktop.assert_called_once_with();self.assertTrue(value['desktopRestoration']['restored'])
    def test_display_failure_keeps_mc_and_refuses_restart_success(self):
        self.desktop.side_effect=ValueError('Desktop changed outside the lease')
        with self.assertRaisesRegex(ValueError,'outside the lease'):self.run_stop()
        self.api.assert_not_called();self.guest.wait.assert_not_called()
        self.assertFalse(self.status[-1]['stopped'])
    def test_wrong_native_refused_before_mutation(self):
        self.pids.return_value=[10];self.capture.side_effect=ValueError('hash differs')
        with self.assertRaisesRegex(ValueError,'hash differs'):self.run_stop()
        self.supervisor.assert_not_called();self.api.assert_not_called();self.assertFalse(self.folder.exists())
    def test_wrong_guest_refused_before_mutation(self):
        self.get_guest.side_effect=ValueError('Guest process identity differs')
        with self.assertRaisesRegex(ValueError,'identity differs'):self.run_stop()
        self.supervisor.assert_not_called();self.normal.assert_not_called();self.assertFalse(self.folder.exists())
    def test_native_failure_never_saves_mc_or_reports_stopped(self):
        self.pids.return_value=[10];self.normal.side_effect=session.NativeCloseError(dict(error='No active present',exitCode=None,nativeExitClassification='normal-close-failed',crashReports=[],forcedTermination=False))
        with self.assertRaises(session.NativeCloseError):self.run_stop()
        self.api.assert_not_called();self.guest.wait.assert_not_called();self.assertEqual(self.status[-1]['phase'],'stop-failed')
        self.assertFalse(self.status[-1]['stopped']);self.assertFalse(self.status[-1]['nativeClosePassed']);self.assertTrue(self.status[-1]['minecraftKeptRunning'])
    def test_exit_zero_crash_cannot_continue(self):
        self.pids.return_value=[10];self.normal.side_effect=session.NativeCloseError(dict(error='current crash',exitCode=0,nativeExitClassification='crash-report',crashReports=[{'path':'actual'}]))
        with self.assertRaises(session.NativeCloseError):self.run_stop()
        self.assertEqual(self.status[-1]['nativeExitClassification'],'crash-report');self.api.assert_not_called()
    def test_guest_pid_reuse_prevents_shutdown(self):
        self.guest.create_time.return_value=101
        with self.assertRaisesRegex(ValueError,'identity changed'):self.run_stop()
        self.api.assert_not_called();self.assertFalse(self.status[-1]['worldSaved'])
    def test_changed_http_guest_prevents_shutdown(self):
        self.api.return_value={'sourcePid':124,'mode':'full-world-frame-proof'}
        with self.assertRaisesRegex(ValueError,'identity changed'):self.run_stop()
        self.assertEqual([c.args for c in self.api.call_args_list],[('health',)])
    def test_save_timeout_not_world_saved(self):
        self.guest.wait.side_effect=psutil.TimeoutExpired(45)
        with self.assertRaises(psutil.TimeoutExpired):self.run_stop()
        self.assertFalse(self.status[-1]['worldSaved']);self.assertFalse(self.status[-1]['stopped']);self.guest.terminate.assert_not_called()
    def test_nonzero_guest_exit_not_world_saved(self):
        self.guest.wait.return_value=1
        with self.assertRaisesRegex(RuntimeError,'nonzero'):self.run_stop()
        self.assertFalse(self.status[-1]['worldSaved']);self.assertFalse(self.status[-1]['stopped'])
    def test_absent_guest_native_only(self):
        self.get_guest.return_value=None;self.pids.return_value=[10]
        value=self.run_stop();self.assertTrue(value['stopped']);self.assertFalse(value['worldSaved']);self.api.assert_not_called()
    def test_fresh_evidence_required(self):
        self.folder.mkdir()
        with self.assertRaises(FileExistsError):self.run_stop()
        self.supervisor.assert_not_called();self.normal.assert_not_called()

class GuestIdentityTests(unittest.TestCase):
    def test_profile_argument_is_exact(self):
        self.assertFalse(session._profile_arguments(['java','-Dpath='+str(session.PROFILE)]));self.assertFalse(session._profile_arguments(['java','--gameDir']))
        self.assertTrue(session._profile_arguments(['java','--gameDir',str(session.PROFILE)]))
    def test_http_absent_living_guest_refuses(self):
        with patch.object(session,'api',side_effect=OSError('offline')),patch.object(session,'_project_guest_processes',return_value=[Mock()]):
            with self.assertRaisesRegex(RuntimeError,'preserved'):session._guest_identity()
    def test_http_absent_no_guest_is_absent(self):
        with patch.object(session,'api',side_effect=OSError('offline')),patch.object(session,'_project_guest_processes',return_value=[]):self.assertIsNone(session._guest_identity())
    def test_wrong_profile_refuses(self):
        guest=Mock(pid=123);guest.exe.return_value='C:/java.exe';guest.cmdline.return_value=['java','--gameDir','C:/unrelated']
        with patch.object(session,'api',return_value={'mode':'full-world-frame-proof','sourcePid':123}),patch.object(session.psutil,'Process',return_value=guest):
            with self.assertRaisesRegex(ValueError,'identity differs'):session._guest_identity()
    def test_unknown_health_mode_refuses(self):
        with patch.object(session,'api',return_value={'mode':'other','sourcePid':123}),patch.object(session.psutil,'Process') as process:
            with self.assertRaisesRegex(ValueError,'identity differs'):session._guest_identity()
            process.assert_not_called()

if __name__=='__main__':unittest.main()
