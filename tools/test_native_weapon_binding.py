import struct
import unittest
from native_weapon_binding import WeaponBindingReader,constant_return,VOLLEY,DYNAMIC,OUT_AMMO

class Memory:
    base=0x100000
    def __init__(self):self.data=bytearray(0x10000)
    def put(self,address,fmt,*values):struct.pack_into(fmt,self.data,address-self.base,*values)
    def raw(self,address,value):self.data[address-self.base:address-self.base+len(value)]=value
    def read(self,address,size):
        if not self.base<=address<=self.base+len(self.data)-size:raise OSError('Unmapped fixture')
        return bytes(self.data[address-self.base:address-self.base+size])
    def meta(self,obj,vt,getter,info,kind,size):
        self.put(obj,'<Q',vt);self.put(vt+0x28,'<Q',getter)
        self.raw(getter,b'\x48\x8d\x05'+struct.pack('<i',info-getter-7)+b'\xc3'+b'\0'*8)
        self.put(info+0x50,'<I',kind);self.put(info+0x5c,'<i',size)

def fixture(flag=1):
    memory=Memory();volley=0x101000;dynamic=0x102000;info=0x103000;args=0x104000
    memory.meta(volley,0x105000,0x106000,info,VOLLEY,0x200)
    memory.put(info+0x28,'<Q',args);memory.put(info+0x54,'<i',1)
    memory.put(args+8,'<IiQ',OUT_AMMO,0x100,0x107000)
    memory.put(0x107000,'<Q',0x108000);memory.put(0x108030,'<Q',0x109000)
    memory.raw(0x109000,b'\x48\xb8'+struct.pack('<Q',(2<<32)|DYNAMIC)+b'\xc3'+b'\0'*5)
    memory.put(volley+0x100,'<Q',dynamic);memory.meta(dynamic,0x105100,0x106100,0x103100,DYNAMIC,0x20)
    memory.put(dynamic+0x10,'<QQ',0x10a000,flag)
    memory.put(0x10a000,'<QQ',*((0x10b000,1) if flag==1 else (1,0x10b000)))
    memory.put(0x10b000,'<QQ',0,0x0d80000000000035)
    return memory,volley

class BindingTests(unittest.TestCase):
    def test_context_product_is_pure_and_pins_the_original_getter(self):
        memory=Memory();memory.data.extend(bytes(0x1610000));obj=0x101000;dynamic=0x102000
        memory.meta(obj,0x105000,0x106000,0x103000,0xcc3a08f4,104)
        memory.meta(dynamic,0x105100,0x106100,0x103100,DYNAMIC,32)
        for offset,storage,items,count in [(0x20,0x10a000,0x10b000,6),(0x30,0x10a100,0x10b100,1),(0x40,0x10a200,0x10b200,1)]:
            memory.put(obj+offset,'<QQ',storage,1);memory.put(storage,'<QQ',items,count)
        code=bytes([70,0,31,0,102,0]);memory.raw(0x10b000,code);memory.put(0x10b100,'<Q',dynamic);memory.put(0x10b200,'<f',17)
        memory.put(dynamic+16,'<QQ',0x10a300,1);memory.put(0x10a300,'<QQ',0x10b300,1);memory.put(0x10b300,'<QQ',0,0x0d800000000009b9)
        memory.put(obj+8,'<Q',0x10c000);memory.put(0x10c000,'<Q',memory.base+0x160ae38);memory.put(memory.base+0x160ae38+0xd0,'<Q',memory.base+0xf6adc0)
        reader=WeaponBindingReader(memory);value=reader.pure_product_expression(obj)
        self.assertEqual(value['constant'],17);self.assertEqual(value['contextPath'],['0d800000000009b9'])
        for offset,byte in [(0,30),(2,30),(4,206),(5,1)]:
            changed=bytearray(code);changed[offset]=byte;memory.raw(0x10b000,changed)
            with self.assertRaises(ValueError):reader.pure_product_expression(obj)
        memory.raw(0x10b000,code);memory.put(memory.base+0x160ae38+0xd0,'<Q',memory.base+0xf6adc1)
        with self.assertRaises(ValueError):reader.pure_product_expression(obj)
    def test_equal_exit_conditional_is_constant_without_evaluating_its_condition(self):
        for flag in (1,2):
            memory=Memory();obj=0x101000
            memory.meta(obj,0x105000,0x106000,0x103000,0xec502a81,104)
            memory.put(obj+0x20,'<QQ',0x10a000,flag);memory.put(obj+0x40,'<QQ',0x10a100,flag)
            memory.put(0x10a000,'<QQ',*((0x10b000,11) if flag==1 else (11,0x10b000)))
            memory.put(0x10a100,'<QQ',*((0x10b100,2) if flag==1 else (2,0x10b100)))
            code=bytes([31,0,4,6,70,0,1,4,70,1,0]);memory.raw(0x10b000,code);memory.put(0x10b100,'<ff',17,17)
            reader=WeaponBindingReader(memory);self.assertEqual(reader.equal_branch_float_expression(obj)['value'],17)
            memory.put(0x10b104,'<f',20)
            with self.assertRaises(ValueError):reader.equal_branch_float_expression(obj)
            memory.put(0x10b104,'<f',17)
            for offset,value in ((0,30),(3,5),(7,3),(9,2),(10,1)):
                changed=bytearray(code);changed[offset]=value;memory.raw(0x10b000,changed)
                with self.assertRaises(ValueError):reader.equal_branch_float_expression(obj)
            memory.raw(0x10b000,code);memory.put(0x10b100,'<ff',float('nan'),float('nan'))
            with self.assertRaises(ValueError):reader.equal_branch_float_expression(obj)
    def test_only_literal_float_expression_is_accepted(self):
        for flag in (1,2):
            memory=Memory();obj=0x101000
            memory.meta(obj,0x105000,0x106000,0x103000,0xec502a81,104)
            memory.put(obj+0x20,'<QQ',0x10a000,flag);memory.put(obj+0x40,'<QQ',0x10a100,flag)
            memory.put(0x10a000,'<QQ',*((0x10b000,3) if flag==1 else (3,0x10b000)))
            memory.put(0x10a100,'<QQ',*((0x10b100,1) if flag==1 else (1,0x10b100)))
            memory.raw(0x10b000,bytes([70,0,0]));memory.put(0x10b100,'<f',15)
            reader=WeaponBindingReader(memory);self.assertEqual(reader.literal_float_expression(obj)['value'],15)
            for code in (bytes([70,1,0]),bytes([71,0,0]),bytes([70,0,3])):
                memory.raw(0x10b000,code)
                with self.assertRaises(ValueError):reader.literal_float_expression(obj)
            memory.raw(0x10b000,bytes([70,0,0]));memory.put(0x10b100,'<f',float('nan'))
            with self.assertRaises(ValueError):reader.literal_float_expression(obj)
    def test_original_integer_config_uses_declared_signed_primitive(self):
        memory,obj=fixture()
        memory.put(0x103050,'<I',0x3ae7427e)
        memory.put(0x104008,'<Ii',0x5180e750,0x100)
        memory.raw(0x109000,bytes.fromhex('8b4128c3'))
        memory.put(0x107028,'<I',0x954a3bab)
        for value in (70,-1):
            memory.put(obj+0x100,'<i',value)
            self.assertEqual(WeaponBindingReader(memory).literal_int(obj),value)
        memory.put(0x107028,'<I',123)
        with self.assertRaises(ValueError):WeaponBindingReader(memory).literal_int(obj)
    def test_damage_follows_declared_impact_health_amount_chain(self):
        memory=Memory();objects=[0x101000+i*0x200 for i in range(4)]
        kinds=[VOLLEY,0x4ef1dd7e,0x06a06f4e,DYNAMIC]
        keys=[0x3d131607,0x89174668,0xc43222bc];offsets=[0x168,0x38,0x38]
        for i,(obj,kind) in enumerate(zip(objects,kinds)):
            memory.meta(obj,0x105000+i*0x100,0x106000+i*0x100,0x103000+i*0x100,kind,0x210 if i==0 else 0x200)
            if i==3:continue
            info=0x103000+i*0x100;args=0x104000+i*0x100;con=0x107000+i*0x100;vt=0x108000+i*0x100;getter=0x109000+i*0x100
            memory.put(info+0x28,'<Q',args);memory.put(info+0x54,'<i',1);memory.put(args+8,'<IiQ',keys[i],offsets[i],con)
            memory.put(con,'<Q',vt);memory.put(vt+0x30,'<Q',getter)
            declared=kinds[i+1] if i<2 else 0xbfd9aadd
            memory.raw(getter,b'\x48\xb8'+struct.pack('<Q',(2<<32)|declared)+b'\xc3'+b'\0'*5);memory.put(obj+offsets[i],'<Q',objects[i+1])
        memory.put(objects[3]+0x10,'<QQ',0x10a000,2);memory.put(0x10a000,'<QQ',1,0x10b000);memory.put(0x10b000,'<QQ',0,0x0d800000000001dc)
        binding=WeaponBindingReader(memory).impact_damage(objects[0])
        self.assertEqual(binding['resourcePath'],['0d800000000001dc']);self.assertEqual(binding['unit'],'overwatch-hp')
        memory.put(0x103150,'<I',DYNAMIC)
        with self.assertRaises(ValueError):WeaponBindingReader(memory).impact_damage(objects[0])
    def test_both_native_list_storage_variants(self):
        for flag in [0,1]:
            memory,volley=fixture(flag);binding=WeaponBindingReader(memory).ammo_output(volley)
            self.assertEqual(binding['resourcePath'],['0d80000000000035'])
            self.assertFalse(binding['nativeCalls']);self.assertFalse(binding['ammoBehaviorVerified'])
    def test_only_named_output_field_is_followed(self):
        memory,volley=fixture();memory.put(0x104008,'<I',123)
        with self.assertRaises(ValueError):WeaponBindingReader(memory).ammo_output(volley)
    def test_wrong_type_or_category_or_path_refused(self):
        for address,fmt,values in [(0x103050,'<I',(123,)),(0x103150,'<I',(123,)),(0x10400c,'<i',(0x200,)),(0x10a008,'<Q',(33,)),(0x10b008,'<Q',(0,))]:
            with self.subTest(address=address),self.assertRaises(ValueError):
                memory,volley=fixture();memory.put(address,fmt,*values);WeaponBindingReader(memory).ammo_output(volley)
    def test_constraint_getters_are_decoded_never_called(self):
        self.assertEqual(constant_return(b'\xb8\x03\0\0\0\xc3'),3)
        with self.assertRaises(ValueError):constant_return(b'\xff\xd0\xc3'+b'\0'*13)
    def test_native_metadata_backed_constraint_getter(self):
        memory,volley=fixture()
        # Measured beta getter: return this->metadata->hash | object_category.
        code=bytes.fromhex('488b412848b900000000020000008b4050480bc1c3')
        memory.raw(0x109000,code);memory.put(0x107028,'<Q',0x103100)
        self.assertEqual(WeaponBindingReader(memory).ammo_output(volley)['resourcePath'],['0d80000000000035'])
        # A different load or an immediate containing low bits is not calibrated.
        for changed in [code[:16]+b'\x51'+code[17:],code[:6]+struct.pack('<Q',(2<<32)|1)+code[14:]]:
            memory.raw(0x109000,changed)
            with self.assertRaises(ValueError):WeaponBindingReader(memory).ammo_output(volley)
    def test_inheritance_cycle_refused(self):
        memory,volley=fixture();memory.put(0x104008,'<I',123);memory.put(0x103020,'<Q',0x103000)
        with self.assertRaises(ValueError):WeaponBindingReader(memory).ammo_output(volley)

if __name__=='__main__':unittest.main()
