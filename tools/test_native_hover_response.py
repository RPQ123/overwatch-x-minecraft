"""Guard the only payload that may be changed by the hover response adapter."""
import math,struct,unittest
from native_hover_response import delay_value

class DelayTests(unittest.TestCase):
    def test_original_and_idempotent_zero(self):
        self.assertAlmostEqual(delay_value(0x7b13a0d4,struct.pack('<f',.2)),.2)
        self.assertEqual(delay_value(0x7b13a0d4,struct.pack('<f',0)),0)
    def test_unrelated_values_types_and_layouts_are_rejected(self):
        for kind,raw in [(0x7b13a0d4,struct.pack('<f',n)) for n in [-.2,.1,1,math.nan,math.inf]]+[(1,struct.pack('<f',.2)),(0x7b13a0d4,b'\0'*8)]:
            with self.subTest(kind=kind,raw=raw),self.assertRaises(ValueError):delay_value(kind,raw)

if __name__=='__main__':unittest.main()
