"""Safe scene start/cleanup receipts without game or HTTP."""
import unittest
from unittest.mock import patch
import hanzo_live_lab as lab


def data(start=2,cleanup=3,active=True,pending=0,error=None):
    scene=dict(active=active,state='ready' if active else 'idle',startSerial=start,cleanupSerial=cleanup,
               ownedBlocks=pending,lastCleanup=dict(pending=pending),corridorClear=True,targetDistance=16,targetId=7,lastStart=dict(terrainCleared=0))
    if error:scene.update(state='failed',error=error)
    result=dict(hanzoCombatLab=scene,testError='',wallBlocks=0,cannonLab=False)
    if active:result.update(targetId=7,targetHealth=20)
    return result


class LabRegression(unittest.TestCase):
    def test_stale_ready_is_not_fresh_start(self):
        frames=iter([data(start=1),data(start=2)])
        class Suite:
            def data(self):return next(frames)
        with patch.object(lab.time,'sleep',lambda _:None):receipt,_=lab.wait_start(Suite(),1)
        self.assertTrue(receipt['passed']);self.assertEqual(len(receipt['trace']),2)

    def test_search_refusal_is_saved_exactly(self):
        class Suite:
            def data(self):return data(active=False,error='no safe loaded corridor; unloaded=369; terrain preserved')
        receipt,_=lab.wait_start(Suite(),1)
        self.assertFalse(receipt['passed']);self.assertIn('unloaded=369',receipt['reason'])

    def test_pending_owned_floor_cannot_be_cleaned(self):
        self.assertFalse(lab.cleanup_contract(lab.snapshot(data(active=False,pending=1)),2)['passed'])
        self.assertFalse(lab.cleanup_contract(lab.snapshot(data(active=False)),3)['passed'])
        self.assertTrue(lab.cleanup_contract(lab.snapshot(data(active=False)),2)['passed'])

    def test_missing_registration_posts_nothing(self):
        class Suite:
            def data(self):return {}
            def post(self,action):raise AssertionError('unexpected mutation')
        with self.assertRaisesRegex(ValueError,'Register HanzoCombatLab'):lab.prepare(Suite(),'scatter')

    def test_prepare_retains_failed_start_after_cleanup(self):
        class Suite:
            result={}
            actions=[]
            def data(self):return data(active=False)
            def post(self,action):self.actions.append(action)
            def aim(self):pass
        s=Suite();failed=dict(passed=False,reason='block entity protected',state=lab.snapshot(data(active=False)))
        with patch.object(lab,'wait_cleanup',return_value=dict(passed=True,state=lab.snapshot(data(active=False)))),patch.object(lab,'wait_start',return_value=(failed,{})):
            with self.assertRaisesRegex(ValueError,'block entity protected'):lab.prepare(s,'scatter')
        self.assertEqual(s.actions,['cleanup','hanzo-combat-lab']);self.assertEqual(s.result['labPreparations'][0]['start'],failed)

    def test_close_waits_for_two_acknowledged_clean_samples(self):
        s=object.__new__(lab.HanzoCombatSuite);s.result={};frames=iter([data(),data(active=False,cleanup=3),data(active=False,cleanup=4),data(active=False,cleanup=4)])
        s.data=lambda:next(frames);actions=[];closed=[];s.post=lambda a:actions.append(a);s.save=lambda:None
        class Resource:
            def close(self):closed.append(True)
        s.native=Resource();s.driver=Resource()
        with patch.object(lab.time,'sleep',lambda _:None):s.close()
        self.assertTrue(s.result['cleaned']);self.assertEqual(actions,['cleanup']);self.assertEqual(len(closed),2)


if __name__=='__main__':unittest.main()
