"""Offline B14/status/window regression fixtures. No Win32 probe/game/input."""
import contextlib
import copy
import importlib.util
import io
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from verify_symmetra_reporting import (AssertionBundle, SUBMISSIONS, case_failure, finalize_result,
                                       require_submission, review_historical)
from verify_symmetra_window import diagnose

ROOT = Path(__file__).resolve().parents[1]


def missing(case):
    counter = SUBMISSIONS[case][0]
    try:
        require_submission(case, {counter:7}, {counter:7})
    except AssertionError as error:
        return case_failure(case, error)
    raise AssertionError('Fixture must block')


class ReportingCheck(unittest.TestCase):
    def test_recorded_b14_failures_have_zero_commits_and_named_assertions(self):
        for key, count in [('symmetra',3),('symmetra-shield',1),('symmetra-turret',1),('symmetra-portal',1)]:
            with self.subTest(key=key):
                folder = ROOT/'research/sprint-20261024'/('integration-live-B14-'+key)
                source = folder/'result.original-B14.json'
                if not source.exists():
                    source = folder/'result.json'
                result = review_historical(json.loads(source.read_text(encoding='utf-8')))
                self.assertEqual((result['status'],result['exitCode']),('BLOCKED',2))
                self.assertEqual(len(result['assertionFailures']),count)
                self.assertTrue(result['error'])
                self.assertTrue(all(f['actual']['delta']==0 and f['assertion'].startswith('native.') for f in result['assertionFailures']))

    def test_successes_plus_missing_signal_is_blocked(self):
        r = dict(cases={'beam':{'passed':True},'shield':missing('shield')},cleaned=True,fullKitAccepted=False)
        self.assertEqual(finalize_result(r),2)
        self.assertEqual(r['cases']['beam']['status'],'PASSED')
        self.assertFalse(r['passed'])

    def test_real_failure_and_cleanup_failure_dominate_blocked(self):
        for failure in ['damage','focus','cleanup']:
            with self.subTest(failure=failure):
                r = dict(cases={'shield':missing('shield')},cleaned=True)
                if failure=='cleanup':r.update(cleaned=False,cleanupError='Input interference')
                else:r['cases'][failure]=case_failure(failure,ValueError('Foreground/input interference' if failure=='focus' else 'Confirmed native E gave no MC shield'))
                self.assertEqual(finalize_result(r),1)
                self.assertEqual(r['status'],'FAILED')

    def test_invalid_regressed_and_duplicate_counters_are_real_failures(self):
        for before,after in [(5,4),(5,7),(None,0),(True,1),(0,'0')]:
            with self.subTest(before=before,after=after):
                with self.assertRaises(AssertionError) as caught:
                    require_submission('turret',{'turretCommits':before},{'turretCommits':after})
                r=dict(cases={'turret':case_failure('turret',caught.exception)},cleaned=True)
                self.assertEqual(finalize_result(r),1)

    def test_blocked_words_without_typed_evidence_do_not_change_exit(self):
        r=dict(cases={'shield':{'passed':False,'error':'BLOCKED: Input interference'}},cleaned=True)
        self.assertEqual(finalize_result(r),1)
        r=dict(cases={'beam':{'passed':True}},cleaned=True,blocked=['passive unsupported'],fullKitAccepted=False)
        self.assertEqual(finalize_result(r),0)

    def test_placement_bundle_preserves_both_assertions(self):
        failures=missing('turret')['assertionFailures']+missing('portal')['assertionFailures']
        r=dict(cases={'placement':case_failure('placement',AssertionBundle(failures))},cleaned=True)
        self.assertEqual(finalize_result(r),2)
        self.assertEqual({f['case'] for f in r['assertionFailures']},{'turret','portal'})


class WindowCheck(unittest.TestCase):
    def snapshot(self, **values):
        window=dict(hwnd=123,title='Overwatch',**{'class':'TankWindowClass'},clientSize=[2560,1440],
                    outerSize=[2560,1440],monitorBounds=[0,0,2560,1440],minimized=False,decorated=False,dpi=96)
        window.update(values)
        return {'windows':[window]}

    def test_supported_and_minimized_window(self):
        self.assertTrue(diagnose(self.snapshot())['ready'])
        d=diagnose(self.snapshot(minimized=True))
        self.assertFalse(d['ready']);self.assertEqual(d['cause'],'MINIMIZED_WINDOW')
        self.assertFalse(d['resolutionChanged']);self.assertFalse(d['inputSent'])

    def test_records_actual_unsupported_monitor_and_decorations(self):
        d=diagnose(self.snapshot(clientSize=[2376,1080],outerSize=[2376,1080],monitorBounds=[0,0,2376,1080]))
        self.assertEqual(d['cause'],'CLIENT_MATCHES_UNSUPPORTED_MONITOR_MODE')
        self.assertIn('unresolved',d['certainty'])
        d=diagnose(self.snapshot(clientSize=[2544,1401],decorated=True))
        self.assertEqual(d['cause'],'DECORATED_CLIENT_SMALLER_THAN_OUTER_WINDOW')

    def test_aspect_alone_does_not_bypass_accepted_sizes_and_disagreement(self):
        d=diagnose(self.snapshot(clientSize=[1280,720],outerSize=[1280,720]))
        self.assertEqual(d['cause'],'SIXTEEN_BY_NINE_SIZE_OUTSIDE_ACCEPTED_PAIR')
        s=self.snapshot();s['driverClientSize']=[1920,1080]
        d=diagnose(s);self.assertFalse(d['ready']);self.assertEqual(d['cause'],'DRIVER_AND_WIN32_CLIENT_DISAGREE')

    def test_ambiguous_or_unknown_cause_is_not_invented(self):
        s=self.snapshot();s['windows']*=2
        self.assertEqual(diagnose(s)['cause'],'RENDER_WINDOW_NOT_UNIQUE')
        d=diagnose(self.snapshot(clientSize=[1700,900],outerSize=[1700,900]))
        self.assertEqual(d['cause'],'UNSUPPORTED_CLIENT_CAUSE_UNDETERMINED')


class ScriptCheck(unittest.TestCase):
    def test_actual_runner_returns_two_for_signal_missing_and_one_for_effect_failure(self):
        self._run_fake(shield_commits=0,expected_exit=2)
        self._run_fake(shield_commits=1,expected_exit=1)

    def test_preflight_writes_failure_before_driver_or_backup(self):
        self._run_fake(shield_commits=0,expected_exit=1,bad_window=True)

    def test_constructor_rect_refusal_is_saved_and_driver_is_closed_without_input(self):
        self._run_fake(shield_commits=0,expected_exit=1,constructor_refusal=True)

    def _run_fake(self, shield_commits, expected_exit, bad_window=False, constructor_refusal=False):
        path=ROOT/'research/sprint-20261024/verify_symmetra.py'
        spec=importlib.util.spec_from_file_location('symmetra_test_runner',path)
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        scene=dict(shieldAttempts=0,shieldCommits=0,shieldGrants=0,fixture=dict(active=True,health=200,absorption=0))
        after=copy.deepcopy(scene);after.update(shieldAttempts=1,shieldCommits=shield_commits)
        made=[]
        class FakeSuite:
            def __init__(self,args):
                made.append(self);self.folder=args.output;self.folder.mkdir();self.result=dict(passed=False,input=[])
                self.client_size=(2376,1080) if constructor_refusal else (2560,1440)
                self.driver=SimpleNamespace(send=Mock(),close=Mock());self.identity=SimpleNamespace(health=Mock())
                if constructor_refusal:
                    self.result['input']=[{'command':'rect','reply':'rect 0 0 2376 1080'}]
                    raise ValueError('Original picker requires an accepted 16:9 client; do not resize just for this test')
                self.native=object();self.reads=0
            def choose(self,_):return {'hero':'Symmetra'}
            def post(self,_):pass
            def data(self):
                self.reads+=1
                return {'symmetra':copy.deepcopy(scene if self.reads==1 else after)}
            def close(self):self.result['cleaned']=True
            def save(self):(self.folder/'result.json').write_text(json.dumps(self.result),encoding='utf-8')
        def require(ok,message):
            if not ok:raise ValueError(message)
        stubs={
            'verify_bastion_cannon':SimpleNamespace(Suite=FakeSuite,require=require),
            'verify_deadeye_input_lock':SimpleNamespace(client_command=lambda command,size:command),
            'prepare_hero_symmetra':SimpleNamespace(prepare=lambda *_:{}),
            'native_charge':SimpleNamespace(grant_for_test=lambda *_:True),
            'verify_junk_hanzo':SimpleNamespace(level=lambda *_:None),
            'verify_recall_empty_history':SimpleNamespace(Identity=lambda *_:SimpleNamespace(health=lambda:None)),
            'calibrate_hero_roster':SimpleNamespace(api=lambda *_:{'symmetra':{'fixture':{'active':False}}}),
        }
        with tempfile.TemporaryDirectory(prefix='symmetra-report-fixture-',dir=ROOT/'research') as temp:
            self.assertTrue(Path(temp).resolve().is_relative_to((ROOT/'research').resolve()))
            output=Path(temp)/'result'
            args=SimpleNamespace(output=output,pid=999,case='lifecycle' if bad_window else 'shield')
            diagnostic=dict(ready=not bad_window,cause='MINIMIZED_WINDOW' if bad_window else 'ACCEPTED_CLIENT',clientSize=[2560,1440],resolutionChanged=False,inputSent=False)
            with patch.dict('sys.modules',stubs),patch.object(module,'probe_window',return_value=diagnostic),patch.object(module,'backup',return_value='fixture-backup') as saved,patch.object(module.time,'sleep'),contextlib.redirect_stdout(io.StringIO()):
                code=module.run(args)
            result=json.loads((output/'result.json').read_text(encoding='utf-8'))
            self.assertEqual(code,expected_exit);self.assertEqual(result['exitCode'],expected_exit)
            self.assertTrue(result['assertionFailures']);self.assertTrue(result['error'])
            if bad_window:
                self.assertEqual(made,[]);saved.assert_not_called();self.assertEqual(result['input'],[])
                self.assertEqual(result['windowDiagnostics'][0]['cause'],'MINIMIZED_WINDOW')
            elif constructor_refusal:
                self.assertEqual(result['clientSize'],[2376,1080]);self.assertEqual(len(result['windowDiagnostics']),2)
                self.assertEqual([x['command'] for x in result['input']],['rect'])
                made[0].driver.close.assert_called_once();made[0].driver.send.assert_not_called()
            else:
                self.assertEqual(result['status'],'BLOCKED' if expected_exit==2 else 'FAILED')


if __name__ == '__main__':
    unittest.main()
