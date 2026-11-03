import struct,unittest
from native_weapon_binding import WeaponBindingReader
from test_native_weapon_binding import Memory
from inspect_native_control_skills import literal,ref,inline,calibrated_policy

class CalibrationChecks(unittest.TestCase):
    def test_deployed_cooldown_does_not_relabel_the_beta_projectile_as_modern(self):
        hero=0x02e0000000000042;beta=(30,5,7,20,3,1,25,10)
        self.assertEqual(calibrated_policy(hero,beta,[])['profile'],'beta')
        modern=calibrated_policy(hero,(*beta[:7],12),[])
        self.assertEqual((modern['baselineCooldown'],modern['observedCooldown']),(10,12))
        self.assertEqual(modern['profile'],'beta-with-requested-modern-cooldown')
        for i in range(8):
            changed=list(beta);changed[i]=11 if i==7 else changed[i]+1
            with self.assertRaises(ValueError):calibrated_policy(hero,tuple(changed),[])
        with self.assertRaises(ValueError):calibrated_policy(hero,(*beta[:6],75,12),[])
        with self.assertRaises(ValueError):calibrated_policy(hero,beta,[[8,1,1,1]])
        with self.assertRaises(ValueError):calibrated_policy(hero,beta[:-1],[])

    def test_pharah_and_unknown_heroes_cannot_inherit_the_mccree_exception(self):
        pharah=(60,5,100,0,8,1,1,12);hero=0x02e0000000000008
        self.assertEqual(calibrated_policy(hero,pharah,[[8,1,1,1]])['profile'],'beta')
        for amount in (0,25,75):
            with self.assertRaises(ValueError):calibrated_policy(hero,(*pharah[:6],amount,12),[[8,1,1,1]])
        with self.assertRaises(ValueError):calibrated_policy(hero,(*pharah[:7],10),[[8,1,1,1]])
        with self.assertRaises(ValueError):calibrated_policy(0x02e0000000000029,pharah,[[8,1,1,1]])

    def test_integer_gravity_and_float_radius_keep_their_declared_types(self):
        memory=Memory();obj=0x101000;reader=WeaponBindingReader(memory)
        memory.meta(obj,0x105000,0x106000,0x103000,0x3ae7427e,24)
        memory.put(0x103028,'<Q',0x104000);memory.put(0x103054,'<i',1)
        memory.put(0x104008,'<IiQ',0x5180e750,16,0x107000)
        memory.put(0x107000,'<Q',0x108000);memory.put(0x108030,'<Q',0x109000)
        memory.raw(0x109000,b'\xb8'+struct.pack('<I',0x954a3bab)+b'\xc3'+bytes(26));memory.put(obj+16,'<i',20)
        self.assertEqual(literal(reader,obj),20)
        memory.put(0x103050,'<I',0x7b13a0d4);memory.put(obj+16,'<f',.2)
        self.assertAlmostEqual(literal(reader,obj),.2)
        for value in (float('nan'),float('inf'),-1,10001):
            memory.put(obj+16,'<f',value)
            with self.assertRaises(ValueError):literal(reader,obj)
        memory.put(0x103050,'<I',0xf8cc195d)
        with self.assertRaisesRegex(ValueError,'not a measured literal'):literal(reader,obj)

    def test_reference_declaration_and_runtime_object_both_must_match(self):
        class Reader:
            def field(self,obj,key):return (10,100,2,20)
            def pointer(self,at):return 200
            def metadata(self,at):return (0,20,24)
        b=Reader();self.assertEqual(ref(b,1,2,10,20),200)
        for owner,target in ((11,20),(10,21)):
            with self.assertRaises(ValueError):ref(b,1,2,owner,target)
        b.metadata=lambda at:(0,21,24)
        with self.assertRaisesRegex(ValueError,'object type'):ref(b,1,2,10,20)

    def test_inline_storage_uses_both_native_orders_and_refuses_invalid_counts(self):
        class Reader:
            flag=1;count=1
            def field(self,obj,key):return (10,100,5,20)
            def unpack(self,fmt,at):
                if at==100:return (200,self.flag)
                if at==200:return (300,self.count) if self.flag==1 else (self.count,300)
                if at==300:return (400,500)
                raise AssertionError('unbounded read')
        b=Reader()
        for b.flag in (1,2):self.assertEqual(inline(b,1,2,10,20,16),[(400,500)])
        for b.count in (-1,17,2**31):
            with self.assertRaisesRegex(ValueError,'bounds'):inline(b,1,2,10,20,16)
        b.count=0;self.assertEqual(inline(b,1,2,10,20,16),[])
        b.flag=0
        with self.assertRaisesRegex(ValueError,'storage'):inline(b,1,2,10,20,16)
        b.flag=1
        with self.assertRaisesRegex(ValueError,'declaration'):inline(b,1,2,10,21,16)

if __name__=='__main__':unittest.main()
