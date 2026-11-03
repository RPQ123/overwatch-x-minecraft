import struct
import unittest
from native_map_snapshot import snapshot_map,lookup_map

class Memory:
    def __init__(self,key_format='Q'):
        self.data=bytearray(0x1000);self.base=0x10000;self.key_format=key_format
        struct.pack_into('<QQ',self.data,0,0x10100,3)
        self.node(0x10100,0x10200,0x10300,0x10400,0,True)
        self.node(0x10300,0x10200,0x10100,0x10400,2)
        self.node(0x10200,0x10100,0x10300,0x10100,1)
        self.node(0x10400,0x10100,0x10300,0x10100,3)
    def node(self,address,left,parent,right,key,sentinel=False):
        offset=address-self.base;struct.pack_into('<QQQBB',self.data,offset,left,parent,right,0,int(sentinel))
        struct.pack_into('<'+self.key_format,self.data,offset+32,key)
    def read(self,address,size):
        if address<self.base or address+size>self.base+len(self.data):raise OSError('Unmapped fixture')
        return bytes(self.data[address-self.base:address-self.base+size])

class MapTests(unittest.TestCase):
    def test_exact_lookup_matches_snapshot_and_absence(self):
        for fmt in ('Q','i'):
            memory=Memory(fmt);expected=dict(snapshot_map(memory,0x10000,fmt))
            for key in (0,1,2,3,4):self.assertEqual(lookup_map(memory,0x10000,key,fmt),expected.get(key))
    def test_lookup_rejects_mutating_path_without_header_change(self):
        memory=Memory();original=memory.read;reads=0
        def read(address,size):
            nonlocal reads
            if address==0x10300 and size==40:
                reads+=1
                if reads==2:
                    value=bytearray(original(address,size));value[24]^=1;return bytes(value)
            return original(address,size)
        memory.read=read
        with self.assertRaisesRegex(ValueError,'path changed'):lookup_map(memory,0x10000,1)
    def test_lookup_rejects_parent_order_cycle_and_bound(self):
        for offset,value,key in [(0x208,0x10400,1),(0x300,0x10300,1),(0x220,5,1)]:
            with self.subTest(offset=offset),self.assertRaises(ValueError):
                memory=Memory();struct.pack_into('<Q',memory.data,offset,value);lookup_map(memory,0x10000,key)
        with self.assertRaises(ValueError):lookup_map(Memory(),0x10000,2,max_count=2)
    def test_both_observed_key_abis_and_payload_alignment(self):
        for fmt in ['Q','i']:
            memory=Memory(fmt)
            self.assertEqual(sorted(snapshot_map(memory,0x10000,fmt)),[(1,0x10228),(2,0x10328),(3,0x10428)])
    def test_empty_sentinel(self):
        memory=Memory();struct.pack_into('<QQ',memory.data,0,0x10100,0);struct.pack_into('<Q',memory.data,0x108,0x10100)
        self.assertEqual(snapshot_map(memory,0x10000,'Q'),[])
    def test_wrong_parent_cycle_count_or_order_refused(self):
        for offset,value in [(0x208,0x10400),(0x200,0x10300),(8,2),(0x220,5)]:
            with self.subTest(offset=offset),self.assertRaises(ValueError):
                memory=Memory();struct.pack_into('<Q',memory.data,offset,value);snapshot_map(memory,0x10000,'Q')
    def test_changed_header_during_read_refused(self):
        memory=Memory();original=memory.read;reads=0
        def read(address,size):
            nonlocal reads
            if address==0x10000:
                reads+=1
                if reads==2:return struct.pack('<QQ',0x10100,4)
            return original(address,size)
        memory.read=read
        with self.assertRaises(ValueError):snapshot_map(memory,0x10000,'Q')
    def test_bounds_and_unknown_abi(self):
        memory=Memory()
        with self.assertRaises(ValueError):snapshot_map(memory,0x10000,'Q',2)
        with self.assertRaises(ValueError):snapshot_map(memory,0x10000,'H')

if __name__=='__main__':unittest.main()
