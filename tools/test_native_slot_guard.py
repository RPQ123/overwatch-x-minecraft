import unittest
from native_slot_guard import slot_input

class InputScope(unittest.TestCase):
    def test_only_slot_digits_and_middle_wheel_are_filtered(self):
        for key in [*range(0x30,0x3a),*range(0x60,0x6a)]:
            self.assertTrue(slot_input('key',0x100,key));self.assertTrue(slot_input('key',0x101,key))
        for key in (0x51,0x45,0x48,0x70,0x75,0x78,0x79,0x7a,0x20,0x10):self.assertFalse(slot_input('key',0x100,key))
        for msg in (0x20a,0x20e,0x207,0x208):self.assertTrue(slot_input('mouse',msg))
        for msg in (0x200,0x201,0x202,0x204,0x205):self.assertFalse(slot_input('mouse',msg))

if __name__=='__main__':unittest.main()
