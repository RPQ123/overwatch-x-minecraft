"""Offline V3/V4 evidence replay and stage-isolation checks; never starts either game."""
import ast
import json
import struct
from pathlib import Path
import unittest

from torbjorn_verification import calibration_signals,calibration_snapshot,deployment_verdict,hammer_verdict
from junkrat_verification import outcome
from native_map_snapshot import snapshot_map
from capture_skill_plan import BY_ID

ROOT=Path(__file__).resolve().parents[1]


class TorbjornV4Check(unittest.TestCase):
    def artifact(self,name):
        path=ROOT/'research/sprint-20261024'/name/'result.json'
        if not path.exists():self.skipTest('private live artifact is not available')
        return json.loads(path.read_text(encoding='utf-8'))

    def test_V4_never_requested_placement(self):
        data=self.artifact('r26b-V4-torb')
        commands=[row.get('command') for row in data['input']]
        self.assertIn('hold 0x32 120',commands);self.assertNotIn('hold 0x10 120',commands)
        self.assertEqual(data['steps'],{});self.assertIn('native hammer kills',data['error'])

    def test_V3_capture_pass_does_not_authenticate_hammer(self):
        data=self.artifact('r26b-V3-torb-calibrate');flags=calibration_signals(data)
        self.assertTrue(data['passed']);self.assertFalse(data['mcSkillAcceptance'])
        self.assertTrue(flags['placementAnimationObserved']);self.assertFalse(flags['hammerCommitObserved'])
        self.assertEqual(data['changedNodesByPhase']['hammer-swing'],[])

    def test_hammer_missing_signal_vs_adapter_failure(self):
        base=dict(hammerSwings=0,signals=dict(hammerRequests=0))
        self.assertEqual(hammer_verdict(base,base)['status'],'BLOCKED')
        self.assertEqual(hammer_verdict(base,base,dict(modelId=1,strikeTick=0),dict(modelId=1,strikeTick=100))['status'],'FAIL')
        self.assertEqual(hammer_verdict(base,dict(hammerSwings=1))['status'],'PASS')

    def test_placement_requires_new_admission_and_exposes_physical_rejection(self):
        base=dict(deploys=2,deployAttempts=2,turret=True)
        self.assertEqual(deployment_verdict(base,base)['status'],'BLOCKED')
        rejected=dict(deploys=2,deployAttempts=3,turret=False,lastDeployRejection='no-upward-ground')
        result=deployment_verdict(base,rejected)
        self.assertEqual(result['status'],'FAIL');self.assertEqual(result['rejection'],'no-upward-ground')
        self.assertEqual(deployment_verdict(base,dict(deploys=3,turret=True))['status'],'PASS')

    def test_blocked_hammer_keeps_placement_result(self):
        cases=dict(placement=dict(status='PASS'),hammer=dict(status='BLOCKED'))
        self.assertEqual(outcome(cases,True),('BLOCKED',2));self.assertEqual(cases['placement']['status'],'PASS')
        self.assertEqual(outcome(cases,True,error='actual collision failure'),('FAIL',1))

    def test_verifier_requests_Shift_before_scrap_and_hammer(self):
        path=ROOT/'research/sprint-20261024/verify_torb_kit.py';tree=ast.parse(path.read_text(encoding='utf-8'))
        calls=[node for node in ast.walk(tree) if isinstance(node,ast.Call) and node.args and isinstance(node.args[0],ast.Constant)]
        shift=min(node.lineno for node in calls if node.args[0].value=='hold 0x10 120')
        scrap=min(node.lineno for node in calls if node.args[0].value=='torb-scrap-lab')
        self.assertLess(shift,scrap)

    def r27(self,name):
        path=ROOT/'research/sprint-20261027'/name/'result.json'
        if not path.exists():self.skipTest('private r27 live artifact is not available')
        return json.loads(path.read_text(encoding='utf-8'))

    def test_r27_calibration_failed_after_Q_not_placement_or_hammer(self):
        data=self.r27('r27-TC-torb-calibrate')
        self.assertEqual(data['error'],"ValueError('Map cycle or count mismatch')")
        self.assertIn('factoryAfter-hammer-swing',data);self.assertIn('factoryAfter-key1-back',data)
        self.assertNotIn('factoryAfter-Q-core',data)
        self.assertTrue(any(row['label']=='Q-core' for row in data['trace']))
        self.assertFalse(any(row['label']=='hammer-swing' for row in data['trace']))
        armor=[c for row in data['trace'] if row['label']=='Q-core' for c in row['changes']
               if c['script']=='05800000000001c2' and c['node']==19]
        self.assertTrue(any(not row['finished'] for row in armor))

    def test_r27_placement_pass_and_actual_scrap_do_not_supply_missing_hammer(self):
        data=self.r27('r27-TT-torb');steps=data['steps'];stage=steps['hammerSignal']
        self.assertEqual(data['status'],'BLOCKED');self.assertEqual(data['cases']['placement']['status'],'PASS')
        self.assertEqual(steps['placement']['after']['deploys']-steps['placement']['before']['deploys'],1)
        self.assertGreater(stage['after']['shots'],stage['before']['shots'])
        self.assertGreater(stage['after']['scrapTaken'],0)
        self.assertEqual(stage['nativeBefore']['strikeTick'],0);self.assertEqual(stage['nativeAfter']['strikeTick'],0)
        self.assertEqual(hammer_verdict(stage['before'],stage['after'],stage['nativeBefore'],stage['nativeAfter'])['status'],'BLOCKED')

    def test_r27_missing_hammer_maps_to_existing_C08_capture_group(self):
        for skill in ['hammer-select','hammer-strike','hammer-repair','scrap','core','core-end']:
            self.assertEqual(BY_ID['torbjorn-'+skill]['group'],'torbjorn')
        self.assertIn('00f3:10,23,24,29',BY_ID['torbjorn-hammer-strike']['watchHints'])
        self.assertIn('--keep-selected',BY_ID['torbjorn-hammer-strike']['nativeScene'])
        self.assertIn('| C08 | torbjorn |',(ROOT/'docs/INTEGRATION-20261026.md').read_text(encoding='utf-8'))

    def test_snapshot_retries_whole_torn_map_and_records_original_map_context(self):
        class Memory:
            headers=0
            def read(self,address,size):
                if address==0x11000:
                    self.headers+=1
                    return struct.pack('<QQ',0x12000,0 if self.headers==1 else 1)
                raw=bytearray(40)
                if address==0x12000:
                    struct.pack_into('<QQQ',raw,0,0x13000,0x13000,0x13000);raw[25]=1
                else:
                    self_address=0x12000
                    struct.pack_into('<QQQ',raw,0,self_address,self_address,self_address)
                    struct.pack_into('<Q',raw,32,42)
                return bytes(raw[:size])
        class Reader:
            memory=Memory();calls=0
            def sample_weapon(self,*args):
                self.calls+=1;snapshot_map(self.memory,0x11000,'Q')
                return dict(modelId=7,localId=8,records={})
        failures=[];checked=[];pauses=[];reader=Reader()
        sample,gap=calibration_snapshot(reader,7,failures,'Q-core',lambda:checked.append(True),local=8,pause=pauses.append)
        self.assertEqual(sample['modelId'],7);self.assertTrue(gap)
        self.assertEqual(reader.calls,2);self.assertEqual(len(checked),2);self.assertEqual(pauses,[.04])
        self.assertEqual(len(failures),1);self.assertEqual(failures[0]['phase'],'Q-core')
        self.assertEqual(failures[0]['map']['address'],0x11000);self.assertEqual(failures[0]['map']['count'],0)
        self.assertEqual(failures[0]['map']['visited'],0)

    def test_persistent_map_failure_is_bounded_and_remains_failure(self):
        class Reader:
            calls=0
            def sample_weapon(self,*args):
                self.calls+=1;raise ValueError('Map cycle or count mismatch')
        reader=Reader();failures=[];pauses=[]
        with self.assertRaisesRegex(ValueError,'Map cycle'):
            calibration_snapshot(reader,7,failures,'Q-core',lambda:None,pause=pauses.append)
        self.assertEqual(reader.calls,3);self.assertEqual([f['attempt'] for f in failures],[1,2,3]);self.assertEqual(pauses,[.04,.04])

    def test_non_map_identity_or_read_failures_never_retry(self):
        class Reader:
            calls=0
            def sample_weapon(self,*args):
                self.calls+=1;raise ValueError('Native logger record bounds')
        reader=Reader();failures=[]
        with self.assertRaisesRegex(ValueError,'record bounds'):
            calibration_snapshot(reader,7,failures,'baseline',lambda:None,pause=lambda _:self.fail('unexpected retry'))
        self.assertEqual(reader.calls,1);self.assertEqual(failures,[])
        class Departed:
            def sample_weapon(self,*args):return dict(modelId=9,localId=8)
        with self.assertRaisesRegex(ValueError,'model/controller changed'):
            calibration_snapshot(Departed(),7,failures,'Q-core',lambda:None,pause=lambda _:self.fail('identity retry'))

    def test_health_focus_checks_cannot_be_swallowed_as_map_retries(self):
        class Reader:
            def sample_weapon(self,*args):raise AssertionError('must not read after identity rejection')
        def reject():raise ValueError('Input interference')
        failures=[]
        with self.assertRaisesRegex(ValueError,'Input interference'):
            calibration_snapshot(Reader(),7,failures,'Q-core',reject,pause=lambda _:self.fail('identity retry'))
        self.assertEqual(failures,[])


if __name__=='__main__':unittest.main()
