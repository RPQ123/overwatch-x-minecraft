import unittest
from native_slot_guard import slot_input,weapon_report_ready

class InputScope(unittest.TestCase):
    def test_only_slot_digits_and_middle_wheel_are_filtered(self):
        for key in [*range(0x30,0x3a),*range(0x60,0x6a)]:
            self.assertTrue(slot_input('key',0x100,key));self.assertTrue(slot_input('key',0x101,key))
        for key in (0x51,0x45,0x48,0x70,0x75,0x78,0x79,0x7a,0x20,0x10):self.assertFalse(slot_input('key',0x100,key))
        for msg in (0x20a,0x20e,0x207,0x208):self.assertTrue(slot_input('mouse',msg))
        for msg in (0x200,0x201,0x202,0x204,0x205):self.assertFalse(slot_input('mouse',msg))

    def test_report_is_current_owner_and_capability_not_a_hero_exception(self):
        for hero in (0x02e0000000000006,0x02e0000000000004):
            report=dict(pid=101,hero=hero,modelId=202,probeVersion=27,enabled=True,failures=0,
                        weaponSlotModel=202,weaponSlotCount=2,weaponSlotSelected=1,weaponSlotRefused=0,weaponSlotWallMs=5000)
            self.assertTrue(weapon_report_ready(report,101,202,hero,5100))
            for change in (dict(pid=102),dict(hero=0),dict(modelId=203),dict(weaponSlotModel=203),
                           dict(probeVersion=26),dict(enabled=False),dict(failures=1),dict(weaponSlotCount=1),
                           dict(weaponSlotSelected=0),dict(weaponSlotRefused=1),dict(weaponSlotWallMs=3000),
                           dict(weaponSlotWallMs=5200)):
                self.assertFalse(weapon_report_ready(report|change,101,202,hero,5100),change)

if __name__=='__main__':unittest.main()
