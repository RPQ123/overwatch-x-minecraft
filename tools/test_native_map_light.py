"""Real Win64 private-buffer light writes, never a game-process fixture."""
import ctypes,os,struct,unittest
from unittest.mock import patch
from native_map_light import temporary_light,checked_vector

@unittest.skipUnless(os.name=='nt','Win64 private allocation')
class LightTests(unittest.TestCase):
    def setUp(self):
        self.kernel=ctypes.WinDLL('kernel32',use_last_error=True)
        self.kernel.OpenProcess.argtypes=[ctypes.c_uint32,ctypes.c_int,ctypes.c_uint32];self.kernel.OpenProcess.restype=ctypes.c_void_p
        self.kernel.CloseHandle.argtypes=[ctypes.c_void_p]
        self.handle=self.kernel.OpenProcess(0x410,False,os.getpid())
        self.buffer=ctypes.create_string_buffer(bytes([0x72])*0x180);self.address=ctypes.addressof(self.buffer)
        ctypes.memmove(self.address+0x14c,struct.pack('<3f',0,-1,0),12);ctypes.memmove(self.address+0x158,struct.pack('<3f',3,2,1),12)
        self.original=self.buffer.raw
    def tearDown(self):self.kernel.CloseHandle(self.handle)
    def read(self,address,size):
        if not self.address<=address<address+size<=self.address+len(self.buffer):raise ValueError('Fixture range')
        return ctypes.string_at(address,size)
    def binding(self,*args):return {'node':0x10000,'data':self.address,'direction':struct.unpack('<3f',self.read(self.address+0x14c,12)),'color':struct.unpack('<3f',self.read(self.address+0x158,12))}
    def test_exact_light_bytes_and_exception_restoration(self):
        with patch('native_map_light.locate',side_effect=self.binding):
            with self.assertRaisesRegex(RuntimeError,'capture failed'):
                with temporary_light(self,os.getpid(),color=(0,0,0)):
                    self.assertEqual(self.buffer.raw,self.original[:0x158]+bytes(12)+self.original[0x164:]);raise RuntimeError('capture failed')
        self.assertEqual(self.buffer.raw,self.original)
    def test_normalized_direction_has_no_camera_or_neighbor_writes(self):
        with patch('native_map_light.locate',side_effect=self.binding):
            with temporary_light(self,os.getpid(),direction=(1,0,0)):
                self.assertEqual(self.buffer.raw,self.original[:0x14c]+struct.pack('<3f',1,0,0)+self.original[0x158:])
        self.assertEqual(self.buffer.raw,self.original)
    def test_invalid_vectors_refuse_before_open_or_write(self):
        for value,direction in [((float('nan'),0,0),False),((9,0,0),False),((-1,0,0),False),((0,0,0),True),((2,0,0),True),((1,2),False)]:
            with self.subTest(value=value,direction=direction),self.assertRaises(ValueError):checked_vector(value,direction)
        self.assertEqual(self.buffer.raw,self.original)
    def test_external_edit_is_not_overwritten(self):
        with patch('native_map_light.locate',side_effect=self.binding):
            with self.assertRaisesRegex(ValueError,'changed externally'):
                with temporary_light(self,os.getpid(),color=(0,0,0)):ctypes.memmove(self.address+0x158,struct.pack('<3f',.5,.5,.5),12)
        self.assertEqual(self.read(self.address+0x158,12),struct.pack('<3f',.5,.5,.5))

if __name__=='__main__':unittest.main()
