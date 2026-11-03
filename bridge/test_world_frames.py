import struct,unittest
import numpy as np
from world_frames import decode,HEADER,MAX_W,MAX_H,STRIDE

class FrameTests(unittest.TestCase):
    def fixture(self):
        header=bytearray(HEADER);header[:8]=b'OWMCFR01';struct.pack_into('<6I',header,8,2,HEADER,3,MAX_W,MAX_H,0)
        struct.pack_into('<QQiIQ',header,32,STRIDE,1,0,1234,77)
        descriptor=bytearray(256);struct.pack_into('<QQQIIfffI',descriptor,0,2,1,0,2,2,.05,256,70,2)
        struct.pack_into('<3d3fIQQQ',descriptor,48,.5,-58.4,.5,0,0,0,1,100,120,10000)
        struct.pack_into('<16f',descriptor,112,*np.eye(4).reshape(-1))
        rgba=bytes([255,0,0,255]*2+[0,0,255,255]*2);depth=struct.pack('<4f',.1,.2,.3,1)
        return header,descriptor,rgba+depth
    def test_real_wire_rows_and_source(self):
        h,d,p=self.fixture();f=decode(h,d,p,10010)
        self.assertEqual(f.rgba[0,0].tolist(),[0,0,255,255]);self.assertAlmostEqual(float(f.depth[0,0]),.3)
        self.assertEqual((f.source_pid,f.generation,f.host_frame),(1234,77,0))
    def test_incomplete_slot(self):
        h,d,p=self.fixture();struct.pack_into('<Q',d,0,3)
        with self.assertRaises(ValueError):decode(h,d,p,10010)
    def test_camera_ack_requires_session_and_frame(self):
        h,d,p=self.fixture();struct.pack_into('<Q',d,16,17)
        with self.assertRaises(ValueError):decode(h,d,p,10010)
        struct.pack_into('<Q',d,176,23)
        f=decode(h,d,p,10010)
        self.assertEqual((f.host_frame,f.host_generation),(17,23))
        struct.pack_into('<Q',d,16,0)
        with self.assertRaises(ValueError):decode(h,d,p,10010)
    def test_size_cap_before_allocation(self):
        h,d,p=self.fixture();struct.pack_into('<I',d,24,MAX_W+1)
        with self.assertRaises(ValueError):decode(h,d,p,10010)
    def test_payload_length(self):
        h,d,p=self.fixture()
        with self.assertRaises(ValueError):decode(h,d,p[:-1],10010)
    def test_color_only_full_hd_has_no_invented_depth(self):
        h,d,p=self.fixture();struct.pack_into('<III',d,24,1920,1080,0) # restore near below
        struct.pack_into('<f',d,32,.05);struct.pack_into('<I',d,44,1)
        rgba=bytes([17,31,79,255])*(1920*1080)
        f=decode(h,d,rgba,10010)
        self.assertEqual(f.rgba.shape,(1080,1920,4));self.assertIsNone(f.depth)
        self.assertEqual(f.rgba[500,800].tolist(),[17,31,79,255])
        with self.assertRaises(ValueError):decode(h,d,rgba+bytes(len(rgba)),10010)
    def test_unknown_payload_format_rejected(self):
        h,d,p=self.fixture();struct.pack_into('<I',d,44,3)
        with self.assertRaises(ValueError):decode(h,d,p,10010)
    def test_qhd_color_and_old_layout_refusal(self):
        h,d,p=self.fixture();struct.pack_into('<II',d,24,2560,1440);struct.pack_into('<I',d,44,1)
        pixels=bytes([17,31,79,255])*(2560*1440);f=decode(h,d,pixels,10010)
        self.assertEqual(f.rgba.shape,(1440,2560,4));self.assertEqual(f.rgba[-1,-1].tolist(),[17,31,79,255])
        struct.pack_into('<I',h,8,1)
        with self.assertRaises(ValueError):decode(h,d,pixels,10010)
    def test_stale_pixels(self):
        h,d,p=self.fixture()
        with self.assertRaises(ValueError):decode(h,d,p,12000)
    def test_projection_finite(self):
        h,d,p=self.fixture();struct.pack_into('<f',d,112,float('nan'))
        with self.assertRaises(ValueError):decode(h,d,p,10010)
    def test_depth_finite(self):
        h,d,p=self.fixture();p=p[:16]+struct.pack('<4f',float('nan'),.2,.3,1)
        with self.assertRaises(ValueError):decode(h,d,p,10010)
    def test_protocol_and_generation(self):
        h,d,p=self.fixture();h[:8]=b'MCPT0001'
        with self.assertRaises(ValueError):decode(h,d,p,10010)
        h[:8]=b'OWMCFR01';struct.pack_into('<Q',h,56,0)
        with self.assertRaises(ValueError):decode(h,d,p,10010)

if __name__=='__main__':unittest.main()
