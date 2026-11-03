"""Offline B11 replay and harness isolation tests; no Suite, process, or live input."""
import json
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock,patch

from junkrat_verification import DeferredSkill,base_verdict,creation_verdict,outcome,plan
import junkrat_live_verification as live

ROOT=Path(__file__).resolve().parents[1]


class JunkratB11Check(unittest.TestCase):
    def artifact(self,key):
        p=ROOT/'research/sprint-20261024'/('integration-live-B11-'+key)/'result.json'
        if not p.is_file():self.skipTest('private B11 result is not available')
        return json.loads(p.read_text(encoding='utf-8'))

    def test_B11_first_run_base_really_passed_before_Q(self):
        row=self.artifact('junkrat')
        self.assertEqual(base_verdict(row['steps'])['status'],'PASS')
        self.assertIn('actual native create32 deadline',row['error'])
        self.assertEqual(row['steps']['detonate']['after']['damageApplied'],20)

    def test_B11_followups_have_no_new_events_not_a_counter_reset(self):
        models=[]
        for key in ('junkrat-base','junkrat-tire','junkrat-wall','junkrat-passive'):
            row=self.artifact(key);models.append(row['actor']['modelId'])
            self.assertEqual(base_verdict(row['steps'])['status'],'FAIL')
            before=row['steps']['grenade']['before'];after=row['steps']['detonate']['after']
            self.assertEqual([before[n] for n in ('grenades','mines','traps','detonations')],[after[n] for n in ('grenades','mines','traps','detonations')])
        self.assertEqual(len(set(models)),1)
        self.assertEqual(models[0],self.artifact('junkrat')['actor']['modelId'])

    def test_modes_are_independent_and_default_is_only_base(self):
        self.assertEqual(plan(),('base',))
        for name in ('base','tire','wall','passive'):self.assertEqual(plan(name),(name,))
        self.assertEqual(plan('all'),('base','passive','tire','wall'))

    def test_missing_native_create_is_deferred_but_MC_rejection_fails(self):
        before=dict(tire=dict(casts=0,castAttempts=0),signals=dict(tireCreateEvents=0))
        self.assertEqual(creation_verdict(before,before)['status'],'DEFERRED')
        rejected=dict(tire=dict(casts=0,castAttempts=1,lastCastRejection='occupied-spawn'))
        self.assertEqual(creation_verdict(before,rejected)['status'],'FAIL')
        native_before=dict(modelId=8,createTick=0);native_after=dict(modelId=8,createTick=100)
        self.assertEqual(creation_verdict(before,before,native_before,native_after)['status'],'FAIL')
        accepted=dict(tire=dict(casts=1,castAttempts=1,active=True))
        self.assertEqual(creation_verdict(before,accepted)['status'],'PASS')

    def test_deferred_does_not_relabel_base_as_failure_or_success_as_full_kit(self):
        cases=dict(base=dict(status='PASS'),tire=dict(status='DEFERRED'))
        self.assertEqual(outcome(cases,True),('BLOCKED',2))
        self.assertEqual(cases['base']['status'],'PASS')
        self.assertEqual(outcome(dict(base=dict(status='PASS')),True),('PASS',0))
        self.assertEqual(outcome(cases,True,error='real failure'),('FAIL',1))
        self.assertEqual(outcome(cases,False),('FAIL',1))

    def test_normal_picker_requires_real_model_recreation(self):
        s=SimpleNamespace(choose=Mock(side_effect=[dict(hero=0x02e000000000006e,modelId=11),dict(hero=live.HERO,modelId=12)]),native=object())
        with patch.object(live,'native_snapshot',return_value=dict(modelId=10)),patch.dict('sys.modules',{'observe_native_weapon_states':SimpleNamespace(WeaponStates=lambda native:'fresh-reader')}):
            r={};actor=live.recreate_actor(s,r,'base')
        self.assertEqual([call.args[0] for call in s.choose.call_args_list],['Soldier76','Junkrat'])
        self.assertEqual(actor['modelId'],12);self.assertEqual(s.states,'fresh-reader')
        s.choose=Mock(side_effect=[dict(modelId=11),dict(hero=live.HERO,modelId=10)])
        with patch.object(live,'native_snapshot',return_value=dict(modelId=10)):
            with self.assertRaisesRegex(ValueError,'same native model'):live.recreate_actor(s,{},'base')

    def test_all_keeps_passive_independent_and_Q_deferred_cases_last(self):
        s=SimpleNamespace(post=Mock());r=dict(steps={})
        with patch.object(live,'prepare'),patch.object(live,'base',return_value=dict(status='PASS')),patch.object(live,'passive',return_value=dict(status='PASS')),patch.object(live,'tire',side_effect=DeferredSkill('no native commit')):
            live.run_cases(s,SimpleNamespace(junk_mode='all'),r,Mock(),Mock(),Mock())
        self.assertEqual(r['status'],'BLOCKED');self.assertFalse(r['passed'])
        self.assertEqual({k:v['status'] for k,v in r['cases'].items()},dict(base='PASS',passive='PASS',tire='DEFERRED',wall='DEFERRED'))

    def test_death_fixture_keeps_PID_world_and_route_guards_while_dead(self):
        s=SimpleNamespace(identity=SimpleNamespace(quick=Mock()),args=SimpleNamespace(mc_pid=42,world='isolated'))
        health=dict(sourcePid=42,worldName='isolated',player=dict(alive=False,survival=False))
        request=Mock(side_effect=[health,dict(junkrat={}),health,dict(accepted=True)])
        with patch.dict('sys.modules',{'verify_recall_empty_history':SimpleNamespace(request=request)}):
            live.death_fixture_request(s,'combat');live.death_fixture_request(s,'combat/test/junk-respawn-lab')
            with self.assertRaisesRegex(ValueError,'unapproved'):live.death_fixture_request(s,'combat/test/anything-else')
        self.assertEqual(request.call_args_list[-1].kwargs,dict(post=True))
        request=Mock(return_value=dict(health,worldName='unowned'))
        with patch.dict('sys.modules',{'verify_recall_empty_history':SimpleNamespace(request=request)}):
            with self.assertRaisesRegex(ValueError,'PID/world mismatch'):live.death_fixture_request(s,'combat/test/junk-respawn-lab')
        self.assertEqual(request.call_count,1)  # no POST to an unowned world


if __name__=='__main__':unittest.main()
