"""Actual Win64 private-buffer writes/restoration, never a game process."""
import ctypes
import os
import unittest
from unittest.mock import patch
from native_runtime_settings import temporary_render_settings
from native_runtime_settings import RENDER_PROFILES


@unittest.skipUnless(os.name=='nt','Windows process-memory fixture')
class RuntimeSettingTests(unittest.TestCase):
    def setUp(self):
        self.kernel=ctypes.WinDLL('kernel32',use_last_error=True)
        self.kernel.OpenProcess.argtypes=[ctypes.c_uint32,ctypes.c_int,ctypes.c_uint32]
        self.kernel.OpenProcess.restype=ctypes.c_void_p
        self.kernel.CloseHandle.argtypes=[ctypes.c_void_p]
        self.handle=self.kernel.OpenProcess(0x400|0x10,False,os.getpid())
        self.assertTrue(self.handle)
        self.buffer=ctypes.create_string_buffer(bytes([1,0x91,0x82,0x73,0,0,0,0,0x64]))
        self.address=ctypes.addressof(self.buffer)
        self.registry={
            'Render.DynamicAmbient':{'type':1,'address':self.address},
            'Render.AADetail':{'type':2,'address':self.address+4},
        }

    def tearDown(self):
        self.kernel.CloseHandle(self.handle)

    def read(self,address,size):
        if not self.address<=address<address+size<=self.address+len(self.buffer):
            raise ValueError('Fixture read outside private allocation')
        return ctypes.string_at(address,size)

    def test_bool_write_preserves_adjacent_bytes_and_restores_on_error(self):
        original=self.buffer.raw
        with patch('native_runtime_settings.settings',return_value=self.registry):
            with self.assertRaisesRegex(RuntimeError,'capture failed'):
                with temporary_render_settings(self,os.getpid(),{'Render.DynamicAmbient':0}) as before:
                    self.assertEqual(before,{'Render.DynamicAmbient':1})
                    self.assertEqual(self.buffer.raw,bytes([0])+original[1:])
                    raise RuntimeError('capture failed')
        self.assertEqual(self.buffer.raw,original)

    def test_integer_setting_still_writes_exactly_four_bytes(self):
        original=self.buffer.raw
        with patch('native_runtime_settings.settings',return_value=self.registry):
            with temporary_render_settings(self,os.getpid(),{'Render.AADetail':3}):
                self.assertEqual(self.buffer.raw,original[:4]+bytes([3,0,0,0])+original[8:])
        self.assertEqual(self.buffer.raw,original)

    def test_invalid_boolean_refuses_before_any_write(self):
        original=self.buffer.raw
        with self.assertRaisesRegex(ValueError,'Unsupported'):
            with temporary_render_settings(self,os.getpid(),{'Render.DynamicAmbient':2}):
                self.fail('Invalid boolean was applied')
        self.assertEqual(self.buffer.raw,original)

    def test_low_profile_keeps_metal_material_lighting_pair(self):
        self.assertEqual(RENDER_PROFILES['low']['Render.DynamicAmbient'],1)
        self.assertEqual(RENDER_PROFILES['low']['Render.SinglePointAmbient'],0)


if __name__=='__main__':unittest.main()
