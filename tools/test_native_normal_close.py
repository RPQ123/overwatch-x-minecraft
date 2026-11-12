"""Normal-close fault fixtures; no game/process/console is operated."""
import hashlib,json,os,tempfile,unittest
from pathlib import Path
from unittest.mock import Mock,patch
import psutil
import native_normal_close as close

class NormalCloseTests(unittest.TestCase):
    def setUp(self):
        self.temporary=tempfile.TemporaryDirectory();self.root=Path(self.temporary.name)
        self.identity=dict(pid=10,creation=1.0,creationFiletime=100,executable=str(self.root/'native.exe'),sha256='fixture')
        self.primitives=Mock();self.primitives.snapshot.return_value={'slot':123,'expected':123}
        self.primitives.close_window.return_value=20
        self.primitives.acknowledge_shutdown_pause.return_value={'acknowledged':True,'globalKeyboardInput':False}
        self.waiter=Mock();self.waiter.wait.return_value=0
        self.process=Mock();self.process.path=Path(self.identity['executable'])
        self.patches=[patch.object(close,'ROOT',self.root),patch.object(close,'validate_native_identity'),
            patch.object(close,'_verified_primitives',return_value=self.primitives),
            patch.object(close,'NativeExitWaiter',return_value=self.waiter),
            patch.object(close,'ResearchProcess',return_value=self.process),
            patch.object(close,'process_creation',return_value=100),
            patch.object(close,'wait_native_crash_reports',return_value=[]),
            patch.object(close,'stop',side_effect=self.restore),
            patch.object(close,'mapped_callback_owners',return_value={p:{p:'fixture-path'} for p,_ in close.OWNERS})]
        self.mocks=[p.start() for p in self.patches]
        self.reports=self.root/'native-host/build';self.reports.mkdir(parents=True)
        for prefix,_ in close.OWNERS:self.write_report(prefix,False)
    def tearDown(self):
        for p in reversed(self.patches):p.stop()
        self.temporary.cleanup()
    def write_report(self,prefix,restored):
        value=dict(pid=10,probeVersion=42 if prefix=='world-live' else 26,enabled=not restored,restored=restored)
        if prefix=='native-emissions':value['creation']=100
        if prefix=='world-live':value.update(slotInputFilter=not restored,slotInputRestored=restored,viewLightRestored=restored,nativeFrameLimitRestored=restored)
        (self.reports/f'{prefix}-10.json').write_text(json.dumps(value),encoding='utf-8');return value
    def restore(self,pid,**options):return self.write_report(next(p for p,expected in close.OWNERS if options==expected),True)
    def run_close(self):return close.normal_close(self.identity,self.root/'result')
    def failed(self):
        with self.assertRaises(close.NativeCloseError) as error:self.run_close()
        value=json.loads((self.root/'result/result.json').read_text(encoding='utf-8'))
        self.assertEqual(value,error.exception.result);self.assertFalse(value['passed']);self.assertFalse(value['forcedTermination']);return value
    def test_complete_restoration_before_original_close(self):
        def window(pid):
            self.assertTrue(all(json.loads((self.reports/f'{p}-10.json').read_text())['restored'] for p,_ in close.OWNERS));return 20
        self.primitives.close_window.side_effect=window
        value=self.run_close();self.assertTrue(value['passed']);self.assertEqual(value['nativeExitClassification'],'normal-close')
        self.assertEqual(list(value['restoration']),[p for p,_ in close.OWNERS]);self.assertEqual(self.primitives.snapshot.call_count,2)
        self.primitives.acknowledge_shutdown_pause.assert_not_called();self.waiter.close.assert_called_once();self.process.close.assert_called_once()
    def test_pause_only_after_first_wait_timeout(self):
        self.waiter.wait.side_effect=[psutil.TimeoutExpired(3),0]
        self.assertTrue(self.run_close()['passed']);self.primitives.acknowledge_shutdown_pause.assert_called_once_with(10,1.0,20)
        self.assertEqual([c.args for c in self.waiter.wait.call_args_list],[(3,),(20,)])
    def test_unverified_pause_refuses(self):
        self.waiter.wait.side_effect=psutil.TimeoutExpired(3);self.primitives.acknowledge_shutdown_pause.side_effect=ValueError('Render window still exists')
        self.assertIn('Render window still exists',self.failed()['error']);self.assertEqual(self.waiter.wait.call_count,1)
    def test_post_pause_timeout_is_failure(self):
        self.waiter.wait.side_effect=[psutil.TimeoutExpired(3),psutil.TimeoutExpired(20)]
        self.assertEqual(self.failed()['nativeExitClassification'],'normal-close-failed')
    def test_exit_zero_with_matching_report_is_crash(self):
        self.mocks[6].return_value=[{'path':'current-report'}]
        value=self.failed();self.assertEqual(value['exitCode'],0);self.assertEqual(value['nativeExitClassification'],'crash-report')
    def test_nonzero_without_report_is_failure(self):
        self.waiter.wait.return_value=5;self.assertEqual(self.failed()['exitCode'],5)
    def test_evidence_read_error_cannot_be_normal(self):
        self.mocks[6].side_effect=OSError('documents unavailable');self.assertEqual(self.failed()['nativeExitClassification'],'evidence-unavailable')
    def test_identity_change_before_restore_sends_nothing(self):
        self.mocks[1].side_effect=ValueError('PID replaced');self.failed()
        self.mocks[7].assert_not_called();self.primitives.close_window.assert_not_called();self.primitives.acknowledge_shutdown_pause.assert_not_called()
    def test_filetime_mismatch_before_restore_sends_nothing(self):
        self.mocks[5].return_value=101;self.failed();self.mocks[7].assert_not_called();self.primitives.close_window.assert_not_called()
    def test_restoration_failure_never_closes(self):
        self.mocks[7].side_effect=TimeoutError('No active presents');self.failed();self.primitives.close_window.assert_not_called()
    def test_compositor_intermediate_snapshot_is_rejected(self):
        def incomplete(pid,**options):
            value=self.restore(pid,**options)
            if not options:value['viewLightRestored']=False
            return value
        self.mocks[7].side_effect=incomplete;self.failed();self.primitives.close_window.assert_not_called()
    def test_old_pid_report_requires_new_restoration(self):
        self.write_report('native-emissions',True);os.utime(self.reports/'native-emissions-10.json',(0,0))
        self.assertTrue(self.run_close()['passed']);self.assertTrue(any(c.kwargs=={'emissions':True} for c in self.mocks[7].call_args_list))
    def test_wrong_report_creation_rejected(self):
        def wrong(pid,**options):
            value=self.restore(pid,**options)
            if options=={'emissions':True}:value['creation']=101
            return value
        self.mocks[7].side_effect=wrong;self.failed();self.primitives.close_window.assert_not_called()
    def test_restored_owner_needs_no_new_stop_event(self):
        for p,_ in close.OWNERS:self.write_report(p,True)
        self.assertTrue(self.run_close()['passed']);self.mocks[7].assert_not_called()
    def test_mapped_correction_failure_precedes_restore(self):
        self.primitives.snapshot.side_effect=ValueError('interface differs');self.failed();self.mocks[7].assert_not_called();self.primitives.close_window.assert_not_called()
    def test_missing_and_malformed_reports_use_each_mapped_owner_stop_event(self):
        for index,(prefix,_) in enumerate(close.OWNERS):
            path=self.reports/f'{prefix}-10.json'
            if index%2:path.write_text('{"pid":',encoding='utf-8')
            else:path.unlink()
        self.assertTrue(self.run_close()['passed'])
        self.assertEqual([c.kwargs for c in self.mocks[7].call_args_list],[options for _,options in close.OWNERS])
        self.primitives.close_window.assert_called_once_with(10)
    def test_inactive_body_proof_is_held_through_normal_close(self):
        (self.reports/'body-sync-10.json').unlink()
        def restore(pid,**options):
            if options.get('body'):raise close.NoStopEvent('No active local passthrough stop event')
            return self.restore(pid,**options)
        def window(pid):
            self.process.kernel.CloseHandle.assert_not_called()
            return 20
        self.mocks[7].side_effect=restore
        self.primitives.close_window.side_effect=window
        with patch.object(close,'reserve_inactive_body',return_value=43) as reserve:
            body=self.run_close()['restoration']['body-sync']
        reserve.assert_called_once_with(self.process,10,{'body-sync':'fixture-path'})
        self.assertTrue(body['originalCallbacksVerified'])
        self.process.kernel.CloseHandle.assert_called_once_with(43)
    def test_missing_stop_event_without_inactive_proof_does_not_close(self):
        def restore(pid,**options):
            if options.get('body'):raise close.NoStopEvent('No active local passthrough stop event')
            return self.restore(pid,**options)
        self.mocks[7].side_effect=restore
        with patch.object(close,'reserve_inactive_body',return_value=None):
            self.failed()
        self.primitives.close_window.assert_not_called()
    def test_partial_start_skips_only_unmapped_owners(self):
        inventory={p:({p:'fixture-path'} if p=='world-live' else {}) for p,_ in close.OWNERS}
        self.mocks[8].return_value=inventory
        for p,_ in close.OWNERS:
            if p!='world-live':(self.reports/f'{p}-10.json').unlink()
        value=self.run_close();self.assertTrue(value['passed'])
        self.assertTrue(value['restoration']['body-sync']['ownerNotMapped'])
        self.mocks[7].assert_called_once_with(10)
    def test_new_owner_during_restoration_refuses_window_close(self):
        initial={p:({p:'fixture-path'} if p=='world-live' else {}) for p,_ in close.OWNERS}
        complete={p:{p:'fixture-path'} for p,_ in close.OWNERS}
        self.mocks[8].side_effect=[initial,complete]
        self.assertIn('inventory changed',self.failed()['error'])
        self.primitives.close_window.assert_not_called()
    def test_fresh_output_required(self):
        (self.root/'result').mkdir()
        with self.assertRaises(FileExistsError):self.run_close()
        self.mocks[1].assert_not_called()

class PrimitiveIdentityTests(unittest.TestCase):
    def test_accepted_verifier_unchanged(self):self.assertEqual(hashlib.sha256(close.VERIFIER.read_bytes()).hexdigest(),close.VERIFIER_SHA256)
    def test_unknown_verifier_rejected_before_import(self):
        with tempfile.TemporaryDirectory() as name:
            path=Path(name)/'verifier.py';path.write_text('different')
            with patch.object(close,'VERIFIER',path),patch.object(close.importlib,'import_module') as load:
                with self.assertRaisesRegex(ValueError,'verifier identity'):close._verified_primitives()
                load.assert_not_called()
    def test_waiter_pins_filetime_and_process_handle(self):
        kernel=Mock();kernel.OpenProcess.return_value=123
        def times(handle,creation,*args):creation._obj.value=42;return True
        def code(handle,output):output._obj.value=0;return True
        kernel.GetProcessTimes.side_effect=times;kernel.GetExitCodeProcess.side_effect=code;kernel.WaitForSingleObject.side_effect=[0x102,0]
        with patch.object(close.ctypes,'WinDLL',return_value=kernel):
            waiter=close.NativeExitWaiter({'pid':10,'creationFiletime':42})
            with self.assertRaises(psutil.TimeoutExpired):waiter.wait(3)
            self.assertEqual(waiter.wait(20),0);waiter.close()
        self.assertEqual([c.args for c in kernel.WaitForSingleObject.call_args_list],[(123,3000),(123,20000)]);kernel.CloseHandle.assert_called_once_with(123)
    def test_waiter_reused_pid_rejected_and_handle_closed(self):
        kernel=Mock();kernel.OpenProcess.return_value=123
        def times(handle,creation,*args):creation._obj.value=43;return True
        kernel.GetProcessTimes.side_effect=times
        with patch.object(close.ctypes,'WinDLL',return_value=kernel):
            with self.assertRaisesRegex(ValueError,'FILETIME changed'):close.NativeExitWaiter({'pid':10,'creationFiletime':42})
        kernel.CloseHandle.assert_called_once_with(123);kernel.WaitForSingleObject.assert_not_called()

if __name__=='__main__':unittest.main()
