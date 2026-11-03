"""B01c asynchronous start/rejection evidence; no game or HTTP."""
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('hanzo_visual_b01c',ROOT/'research/sprint-20261024/verify_hanzo_arrows_visual.py')
v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)


def sample(serial=1,state='idle',active=False,error=None):
    lab=dict(startSerial=serial,state=state,active=active,wallBlocks=28 if active else 0)
    if error:lab['error']=error
    return dict(hanzoArrowVisualLab=lab,testError='',wallBlocks=625)


class StartRegression(unittest.TestCase):
    def test_waits_past_old_delay_and_requires_fresh_ready(self):
        # An old active snapshot is not the requested start's acknowledgement.
        frames=iter([sample(state='ready',active=True),sample(serial=2),sample(serial=2,state='ready',active=True)])
        class Suite:
            def data(self):return next(frames)
        with patch.object(v.time,'monotonic',side_effect=[0,0,.8,1]),patch.object(v.time,'sleep',lambda _:None):receipt,data=v.wait_start(Suite(),1)
        self.assertTrue(receipt['passed']);self.assertEqual(len(receipt['trace']),3)
        self.assertTrue(data['hanzoArrowVisualLab']['active'])

    def test_real_start_error_is_saved_instead_of_registration_message(self):
        error='Hanzo visual wall site occupied/unloaded: {1924,63,-1990}'
        class Suite:
            def data(self):return sample(serial=2,state='failed',error=error)
        receipt,_=v.wait_start(Suite(),1)
        self.assertFalse(receipt['passed']);self.assertIn(error,receipt['reason'])
        self.assertEqual(receipt['state']['lab']['error'],error)

    def test_missing_route_is_bounded_and_has_last_state(self):
        class Suite:
            def data(self):return sample()
        with patch.object(v.time,'monotonic',side_effect=[0,0,4]),patch.object(v.time,'sleep',lambda _:None):
            receipt,_=v.wait_start(Suite(),1)
        self.assertFalse(receipt['passed']);self.assertIn('deadline',receipt['reason'])
        self.assertEqual(receipt['state']['lab']['startSerial'],1)

    def test_prepare_retains_rejection_receipt_for_final_result(self):
        class Suite:
            result={}
            def data(self):return sample()
            def post(self,action):pass
            def aim(self):pass
        s=Suite();failed=dict(passed=False,reason='scene start rejected: occupied',state=v.start_snapshot(sample()),trace=[])
        with patch.object(v,'wait_cleanup',return_value=dict(passed=True)),patch.object(v,'wait_start',return_value=(failed,sample())):
            with self.assertRaisesRegex(ValueError,'occupied'):v.prepare(s,'primary')
        self.assertEqual(s.result['preparations'][0]['startReceipt'],failed)


if __name__=='__main__':unittest.main()
