import unittest
from observe_native_weapon_states import changed_records

class WeaponStateTests(unittest.TestCase):
    def test_initial_snapshot_is_not_an_attack(self):
        record={'x':{'node':6,'nativeTick':100,'finished':False,'weaponVolleyNode':True}}
        self.assertEqual(changed_records(None,record),[])
    def test_unchanged_and_removed_records_do_not_become_new_executions(self):
        record={'x':{'node':6,'nativeTick':100,'finished':False}}
        self.assertEqual(changed_records(record,record),[])
        self.assertEqual(changed_records(record,{}),[])
    def test_native_tick_and_finish_transition_remain_separate_observations(self):
        active={'node':6,'nativeTick':100,'finished':False};ended={**active,'nativeTick':110,'finished':True}
        self.assertEqual(changed_records({'x':active},{'x':ended}),[ended])
        self.assertEqual(changed_records({'x':active},{'x':{**active,'finished':True}}),[{**active,'finished':True}])
    def test_recreated_script_address_never_reuses_old_identity(self):
        record={'node':6,'nativeTick':100,'finished':False}
        self.assertEqual(changed_records({'old:6':record},{'new:6':record}),[record])

if __name__=='__main__':unittest.main()
