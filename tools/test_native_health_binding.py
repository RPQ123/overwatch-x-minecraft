import math,struct,unittest
from native_health_binding import health_plan

def pool(enabled=0,maximum=0,current=0):
    raw=bytearray(320);struct.pack_into('<Iff',raw,0,enabled,maximum,current)
    for offset in range(0,320,20):raw[offset+12:offset+20]=bytes((3,0,0,0,0,1,0,0))
    return bytes(raw)

class HealthPlanTests(unittest.TestCase):
    def test_base_health_and_armor_keep_metadata_out_of_write_set(self):
        before=[pool(1,200,169),pool(),pool()]
        after=health_plan(before,[400,100,0])
        self.assertEqual([struct.unpack('<Iff',p) for p in after],[(1,400,400),(1,100,100),(0,0,0)])
        self.assertTrue(all(len(p)==12 for p in after))
        self.assertEqual(health_plan([a+b[12:] for a,b in zip(after,before)],[400,100,0]),after)
    def test_temporary_pool_is_preserved_by_refusing_initialization(self):
        armor=bytearray(pool());struct.pack_into('<Iff',armor,20,1,75,50)
        with self.assertRaisesRegex(ValueError,'additional'):health_plan([pool(1,200,169),bytes(armor),pool()],[400,100,0])
    def test_unexpected_enabled_pool_is_not_deleted(self):
        with self.assertRaisesRegex(ValueError,'unexpected'):health_plan([pool(1,200,169),pool(1,100,100),pool()],[200,0,0])
    def test_bad_configuration_or_live_values_never_produce_writes(self):
        for amount in (-1,math.nan,math.inf,10001):
            with self.subTest(amount=amount),self.assertRaises(ValueError):health_plan([pool(1,200,169),pool(),pool()],[amount,0,0])
        for raw in (pool(2,200,169),pool(1,200,201),pool(1,math.nan,0),pool(0,200,0)):
            with self.assertRaises(ValueError):health_plan([raw,pool(),pool()],[200,0,0])
    def test_malformed_pool_lengths_are_refused(self):
        with self.assertRaises(ValueError):health_plan([pool()[:12],pool(),pool()],[200,0,0])

if __name__=='__main__':unittest.main()
