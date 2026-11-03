"""Saved B01b assertion isolation + async-cleanup regression, no game/API calls."""
import importlib.util
import json
from pathlib import Path
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('hanzo_visual_b01b',ROOT/'research/sprint-20261024/verify_hanzo_arrows_visual.py')
visual=importlib.util.module_from_spec(spec);spec.loader.exec_module(visual)


def clean_data(serial=6,frame=2000):
    return {'cannonLab':False,'wallBlocks':0,'hanzoArrowVisualLab':{'active':False,'wallBlocks':0,'cleanupSerial':serial,'lastCleanupWall':2000},
            'hanzoArrowFx':{'frameWall':frame,'activeStuck':0},'hanzoSkills':{'arrows':0,'dragons':0,'embeddedArrows':0}}


class B01bRegression(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.saved=json.loads((ROOT/'research/sprint-20261024/integration-live-B01b-hanzo-visual/result.json').read_text(encoding='utf-8'))

    def test_saved_error_isolation(self):
        for kind,wanted in [('primary',True),('sonic',False),('scatter',True)]:
            row=self.saved['rows'][kind];result=visual.render_contract(row['before'],row['after'],kind)
            self.assertEqual(result['passed'],wanted,kind)
            self.assertFalse(result['nativeColorVariablesResolved'])
            if kind=='sonic':self.assertEqual(set(result['activeErrors']),{'hanzo-sonic-pulse','hanzo-sonic-sense'})

    def test_new_role_counters_cannot_hide_real_failure(self):
        before={'fx':{'assetErrors':{},'assetErrorCounts':{}}};after={'fx':{'assetErrors':{},'assetErrorCounts':{'PRIMARY':1}}}
        self.assertFalse(visual.render_contract(before,after,'primary')['passed'])
        self.assertTrue(visual.render_contract(before,after,'scatter')['passed'])

    def test_missing_native_is_blocked_not_pass(self):
        legacy=self.saved['rows']['scatter']['after']['skills']['scatterContext']
        self.assertEqual(visual.scatter_parameters_contract(legacy,False)['status'],'FAIL','old 75 damage is not current x4 policy')
        context=dict(legacy,parentDamage=300,childDamage=300,damageMultiplier=4,damageAdaptation='MC 适配：用户要求')
        result=visual.scatter_parameters_contract(context,False)
        self.assertEqual(result['status'],'BLOCKED');self.assertFalse(result['passed']);self.assertTrue(result['unchangedFallback'])
        broken=dict(context,childDamage=0);self.assertEqual(visual.scatter_parameters_contract(broken,False)['status'],'FAIL')
        old_double=dict(context,parentDamage=150,childDamage=150,damageMultiplier=2)
        self.assertEqual(visual.scatter_parameters_contract(old_double,False)['status'],'FAIL')

    def test_native_scatter_quadruple_damage_expectations(self):
        for q,base_parent in [(0,25),(.5,75),(1,125)]:
            context=dict(nativeValues=True,q=q,parentSpeed=25+65*q,childSpeed=.8*(20+65*q),
                         parentDamage=4*base_parent,childDamage=4*(15+60*q),identity='fixture',
                         damageMultiplier=4,damageAdaptation='MC 适配：用户要求')
            self.assertEqual(visual.scatter_parameters_contract(context,True)['status'],'PASS')
            self.assertEqual(visual.scatter_parameters_contract(dict(context,childDamage=2*(15+60*q)),True)['status'],'FAIL')
            self.assertEqual(visual.scatter_parameters_contract(dict(context,parentDamage=8*125),True)['status'],'FAIL')

    def test_cleanup_ack_and_original_conditions_remain_required(self):
        self.assertFalse(visual.cleanup_contract(visual.cleanup_snapshot(clean_data(serial=5)),5)['passed'])
        self.assertFalse(visual.cleanup_contract(visual.cleanup_snapshot(clean_data(frame=1999)),5)['passed'])
        dirty=clean_data();dirty['targetHealth']=20
        self.assertFalse(visual.cleanup_contract(visual.cleanup_snapshot(dirty),5)['passed'])
        self.assertTrue(visual.cleanup_contract(visual.cleanup_snapshot(clean_data()),5)['passed'])

    def test_close_waits_for_ack_instead_of_stale_pending(self):
        suite=object.__new__(visual.HanzoVisualSuite);suite.result={};actions=[];closed=[]
        pending=clean_data(serial=5);pending['hanzoArrowVisualLab']['wallBlocks']=28
        samples=iter([pending,pending,clean_data(frame=1999),clean_data(),clean_data()])
        suite.data=lambda:next(samples);suite.post=lambda action:actions.append(action);suite.save=lambda:None
        class Resource:
            def close(self):closed.append(True)
        suite.native=Resource();suite.driver=Resource()
        with patch.object(visual.time,'sleep',lambda _:None):suite.close()
        self.assertTrue(suite.result['cleaned']);self.assertEqual(actions,['cleanup']);self.assertEqual(len(closed),2)
        self.assertEqual(suite.result['cleanupReceipt']['state']['cleanupSerial'],6)


if __name__=='__main__':unittest.main()
