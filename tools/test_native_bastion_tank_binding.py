"""Native Tank metadata fixtures; no input, native execution or live processes."""
import struct
import unittest

from inspect_native_scripts import ScriptReader
from native_armory_binding import PRIMARY_RESOURCES, bastion_tank_profile
from native_weapon_binding import WeaponBindingReader
from test_native_weapon_binding import Memory


class TankFixture:
    def __init__(self, flag=1):
        self.memory=Memory();self.memory.data=bytearray(0x40000);self.cursor=self.memory.base+0x1000
        self.flag=flag;self.infos={};self.constraints={}
        self.reader=ScriptReader(self.memory);self.reader.bindings=WeaponBindingReader(self.memory)
        scalar=0xbfd9aadd
        fields=[(0xac2f916a,0x140,2,scalar),(0x5257be73,0x128,2,scalar),
                (0x308e35d5,0x130,2,scalar),(0x472bec0c,0x190,2,scalar),
                (0x120fd2f8,0x198,2,scalar),(0xb5d34136,0x100,3,0x7f06bc91),
                (0x5b97fa06,0x160,2,0x66bd247b),(0x3d131607,0x168,2,0x4ef1dd7e)]
        self.node=self.stu(0x860ee5fc,528,fields)
        self.speed=self.stu(0xf8cc195d,32)
        self.path_storage,self.path_items=self.array(self.speed+0x10,[0,0x0d800000000018e0],16)
        self.lifetime=self.number(5);self.range=self.number(100.,True)
        self.count=self.number(1);self.rate=self.number(1)
        for at,obj in [(0x140,self.speed),(0x128,self.lifetime),(0x130,self.range),(0x190,self.count),(0x198,self.rate)]:
            self.memory.put(self.node+at,'<Q',obj)
        self.motion_storage,self.motion_items=self.array(self.node+0x100,[],8)
        self.direct=self.number(50)
        self.direct_health=self.stu(0x06a06f4e,216,[(0xc43222bc,0x38,2,scalar)])
        self.memory.put(self.direct_health+0x38,'<Q',self.direct)
        self.impact=self.stu(0x4ef1dd7e,64,[(0x89174668,0x38,2,0x06a06f4e)])
        self.memory.put(self.impact+0x38,'<Q',self.direct_health);self.memory.put(self.node+0x168,'<Q',self.impact)
        self.blast_amount=self.number(140)
        self.blast_health=self.stu(0x06a06f4e,216,[(0xc43222bc,0x38,2,scalar)])
        self.memory.put(self.blast_health+0x38,'<Q',self.blast_amount)
        self.explosion=self.stu(0x66bd247b,120,[(0xee107893,8,5,0xf91c284f),(0x89174668,0x60,2,0x06a06f4e)])
        self.memory.put(self.explosion+0x60,'<Q',self.blast_health);self.memory.put(self.node+0x160,'<Q',self.explosion)
        self.rings=[self.number(1),self.number(1),self.number(4),self.number(.3,True)]
        self.ring_storage,self.ring_items=self.array(self.explosion+8,self.rings,16)
        self.graph=self.alloc(0x80)
        nodes=[0]*29;nodes[25]=self.node;states=[0]*22;states[19]=self.node
        self.node_storage,self.node_items=self.array(self.graph+0x50,nodes,8)
        self.state_storage,self.state_items=self.array(self.graph+0x60,states,8)
        self.bag=self.alloc(0x400);self.speed_primitive=self.alloc(0xb0);entry=self.alloc(16)
        self.memory.put(self.speed_primitive,'<Q',self.memory.base+0x1608248)
        self.memory.put(self.speed_primitive+0xa0,'<QII',60,0,2)
        self.memory.put(entry,'<QQ',0x0d800000000018e0,self.speed_primitive)
        self.memory.put(self.bag+0xa0,'<Qii',entry,1,1)
        self.damage=self.reader.bindings.impact_damage(self.node)

    def alloc(self,size):
        at=self.cursor;self.cursor+=(size+63)&~63
        if self.cursor>self.memory.base+len(self.memory.data):raise ValueError('Fixture allocation bound')
        return at

    def stu(self,kind,size,fields=()):
        obj=self.alloc(size);vt=self.alloc(0x80);getter=self.alloc(32);info=self.alloc(0x80)
        self.memory.meta(obj,vt,getter,info,kind,size);self.infos[obj]=info
        if fields:
            args=self.alloc(len(fields)*0xa0);self.memory.put(info+0x28,'<Q',args);self.memory.put(info+0x54,'<i',len(fields))
            for i,(key,offset,category,declared) in enumerate(fields):
                constraint=self.alloc(0x40);cvt=self.alloc(0x80);fn=self.alloc(32)
                self.memory.put(args+i*0xa0+8,'<IiQ',key,offset,constraint)
                self.memory.put(constraint,'<Q',cvt);self.memory.put(cvt+0x30,'<Q',fn)
                self.memory.raw(fn,b'\x48\xb8'+struct.pack('<Q',(category<<32)|declared)+b'\xc3'+bytes(21))
                self.constraints[obj,key]=fn
        return obj

    def number(self,value,floating=False):
        kind=0x7b13a0d4 if floating else 0x3ae7427e
        declared=0x8fa75a30 if floating else 0x954a3bab
        obj=self.stu(kind,24,[(0x5180e750,16,0,declared)])
        self.memory.put(obj+16,'<f' if floating else '<i',value)
        return obj

    def array(self,at,values,stride):
        storage=self.alloc(16);items=self.alloc(max(8,len(values)*8));count=len(values)*8//stride
        self.memory.put(at,'<QQ',storage,self.flag)
        self.memory.put(storage,'<QQ',*((items,count) if self.flag==1 else (count,items)))
        for i,value in enumerate(values):self.memory.put(items+i*8,'<Q',value)
        return storage,items

    def profile(self,**changes):
        args=dict(hero=0x02e0000000000015,script=0x058000000000024f,index=25,graph=self.graph,
                  node=self.node,bag=self.bag,damage=self.damage,gravity=0.)
        args.update(changes)
        return bastion_tank_profile(self.reader,**args)


class TankBindingTests(unittest.TestCase):
    def test_actual_typed_damage_rings_and_both_stu_layouts(self):
        for flag in (1,2):
            with self.subTest(flag=flag):
                f=TankFixture(flag);profile=f.profile()
                self.assertEqual((profile['splash'],profile['inner'],profile['outer']),(140,1,4))
                self.assertEqual(profile['outerScale'],struct.unpack('<f',struct.pack('<f',.3))[0])

    def test_resource_is_added_only_alongside_bastion_primaries(self):
        self.assertEqual(PRIMARY_RESOURCES[0x15],{0x0400000000000205,0x0400000000000207,0x04000000000003ce})
        for hero,resources in PRIMARY_RESOURCES.items():
            if hero!=0x15:self.assertNotIn(0x04000000000003ce,resources)

    def test_other_hero_script_node_and_nonzero_gravity_are_refused(self):
        for changes in [dict(hero=0x02e0000000000008),dict(script=0x058000000000012e),dict(index=24),dict(gravity=.01)]:
            with self.subTest(changes=changes),self.assertRaises(ValueError):TankFixture().profile(**changes)

    def test_changed_direct_and_blast_sources_are_refused(self):
        for target,value in [('direct',49),('blast_amount',139),('lifetime',6),('count',2),('rate',2)]:
            with self.subTest(target=target):
                f=TankFixture();f.memory.put(getattr(f,target)+16,'<i',value)
                if target=='direct':f.damage=f.reader.bindings.impact_damage(f.node)
                with self.assertRaises(ValueError):f.profile()
        f=TankFixture();f.memory.put(f.range+16,'<f',99.)
        with self.assertRaises(ValueError):f.profile()

    def test_changed_blast_rings_do_not_inherit_other_rocket_defaults(self):
        for index,fmt,value in [(0,'<i',0),(1,'<i',0),(2,'<i',3),(3,'<f',.125),(3,'<f',float('nan'))]:
            with self.subTest(index=index,value=value):
                f=TankFixture();f.memory.put(f.rings[index]+16,fmt,value)
                with self.assertRaises(ValueError):f.profile()

    def test_numeric_lookalikes_of_wrong_type_are_refused(self):
        for target in ['direct','lifetime','blast_amount']:
            with self.subTest(target=target):
                f=TankFixture();obj=getattr(f,target);f.memory.put(f.infos[obj]+0x50,'<I',0x7b13a0d4)
                f.memory.put(obj+16,'<f',50. if target=='direct' else 5. if target=='lifetime' else 140.)
                with self.assertRaises(ValueError):f.profile()

    def test_speed_requires_the_original_unique_typed_script_variable(self):
        for field,fmt,value in [('speed_primitive','<I',59),('speed_primitive','<I',61)]:
            f=TankFixture();f.memory.put(getattr(f,field)+0xa0,fmt,value)
            with self.assertRaises(ValueError):f.profile()
        f=TankFixture();f.memory.put(f.speed_primitive+0xa0,'<QII',struct.unpack('<I',struct.pack('<f',60.))[0],0,3)
        with self.assertRaises(ValueError):f.profile()
        f=TankFixture();f.memory.put(f.path_items+8,'<Q',0x0d800000000018e1)
        with self.assertRaises(ValueError):f.profile()
        f=TankFixture(2);f.memory.put(f.speed+0x18,'<Q',3)
        with self.assertRaises(ValueError):f.profile()

    def test_graph_membership_and_empty_motion_are_verified(self):
        f=TankFixture();f.memory.put(f.state_items+19*8,'<Q',0)
        with self.assertRaises(ValueError):f.profile()
        f=TankFixture();f.memory.put(f.node_items+25*8,'<Q',0)
        with self.assertRaises(ValueError):f.profile()
        f=TankFixture();f.memory.put(f.motion_storage+8,'<Q',1);f.memory.put(f.motion_items,'<Q',f.node)
        with self.assertRaises(ValueError):f.profile()

    def test_reflection_category_is_checked_before_reading_the_config(self):
        f=TankFixture();fn=f.constraints[f.node,0x5257be73]
        f.memory.raw(fn,b'\x48\xb8'+struct.pack('<Q',(3<<32)|0xbfd9aadd)+b'\xc3'+bytes(21))
        with self.assertRaises(ValueError):f.profile()


if __name__=='__main__':unittest.main()
