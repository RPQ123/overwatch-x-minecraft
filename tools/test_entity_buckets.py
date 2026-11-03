"""Entity hash collisions caused long-session hero rebinding to miss live owners."""
import struct,unittest
from observe_overwatch import PoseReader

class Memory:
    def __init__(self,entries):self.entries=entries
    def read(self,address,size):
        if address==0x100000:return self.entries[:size]
        raise OSError('unmapped fixture')

class EntityBuckets(unittest.TestCase):
    def test_controller_after_low12_id_collision_is_not_skipped(self):
        table=bytearray(65536);identifier=0x80001039
        struct.pack_into('<Qii',table,(identifier&4095)*16,0x100000,3,0)
        entries=b''.join(struct.pack('<IIQ',i,0,p) for i,p in [(0x80000039,0x110000),(identifier,0x120000),(0x80002039,0x130000)])
        reader=PoseReader(Memory(entries));self.assertEqual(reader.entity(table,identifier),0x120000)
        self.assertEqual(reader.entity(table,0x80002039),0x130000)
    def test_missing_and_corrupt_counts_fail_closed(self):
        table=bytearray(65536);struct.pack_into('<Qii',table,16,0x100000,1,0)
        reader=PoseReader(Memory(struct.pack('<IIQ',1,0,0x110000)))
        with self.assertRaises(ValueError):reader.entity(table,2)
        struct.pack_into('<i',table,24,4097)
        with self.assertRaises(ValueError):reader.entity(table,1)

if __name__=='__main__':unittest.main()
