"""Forensic parser bounds and register identity; no processes or game files."""
import struct
import tempfile
import unittest
from pathlib import Path
from observe_native_timer_lifetime import dump_registers

class DumpTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.path=Path(self.temp.name)/'fixture.dmp'
        self.raw=bytearray(512);self.raw[:4]=b'MDMP';struct.pack_into('<II',self.raw,8,1,32);struct.pack_into('<III',self.raw,32,6,168,64)
        struct.pack_into('<I',self.raw,64,123);struct.pack_into('<I',self.raw,72,0xc0000005);struct.pack_into('<II',self.raw,224,256,256)
        struct.pack_into('<I',self.raw,304,0x10000f)
        for offset,value in ((120,0x11223344),(128,0x55667788),(152,0x88776655),(176,0x1234567890),(248,0x1020304050)):
            struct.pack_into('<Q',self.raw,256+offset,value)
    def read(self):self.path.write_bytes(self.raw);return dump_registers(self.path)
    def test_rdi_script_candidate_is_not_rcx_or_rip(self):
        row=self.read();self.assertEqual(row['rdi'],0x1234567890);self.assertEqual(row['rcx'],0x55667788);self.assertEqual(row['rip'],0x1020304050);self.assertEqual(row['exception'],'0xc0000005');self.assertEqual(row['thread'],123)
    def test_bad_signature(self):
        self.raw[:4]=b'NONE'
        with self.assertRaises(ValueError):self.read()
    def test_missing_exception_stream(self):
        struct.pack_into('<I',self.raw,32,3)
        with self.assertRaises(ValueError):self.read()
    def test_truncated_context(self):
        self.raw=self.raw[:-1]
        with self.assertRaises(ValueError):self.read()
    def test_non_amd64_context(self):
        struct.pack_into('<I',self.raw,304,0x10007)
        with self.assertRaises(ValueError):self.read()
    def test_outside_directory(self):
        struct.pack_into('<I',self.raw,12,500)
        with self.assertRaises(ValueError):self.read()
    def test_ambiguous_exception_stream(self):
        struct.pack_into('<I',self.raw,8,2);struct.pack_into('<III',self.raw,44,6,168,64)
        with self.assertRaises(ValueError):self.read()

if __name__=='__main__':unittest.main()
