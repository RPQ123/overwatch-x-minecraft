"""Synthetic structure checks; real host observations are a separate evidence file."""
from pathlib import Path
import math
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "tools"), str(ROOT / "bridge")]
from test_memory import FakeMemory
from probe_overwatch_camera import HostCameraReader

class HostCameraTests(unittest.TestCase):
    def setUp(self):
        self.memory = FakeMemory()
        self.memory.put(self.memory.base + 0x17b7f90, struct.pack("<Q", 0x20000000))
        admin = bytearray(0x230)
        struct.pack_into("<Q", admin, 0xB0, 0x21000000)
        self.memory.put(0x20000000, admin)
        iterators = bytearray(0x50 * 0x18)
        struct.pack_into("<Qii", iterators, 0x4F * 0x18, 0x22000000, 1, 1)
        self.memory.put(0x21000000, iterators)
        self.memory.put(0x22000000, struct.pack("<Q", 0x23000000))
        component = bytearray(0x50)
        component[0x10] = 0x4F
        struct.pack_into("<Q", component, 0x40, 0x24000000)
        self.memory.put(0x23000000, component)
        camera = bytearray(0x268)
        struct.pack_into("<Q", camera, 0x260, 0x25000000)
        self.memory.put(0x24000000, camera)
        view = bytearray(0x70)
        struct.pack_into("<12f", view, 0x10, 12.5, 1.6, 42, 0, 0, -.5, 0, 0, 0, 0, 0, 0)
        self.memory.put(0x25000000, view)
        self.reader = HostCameraReader(self.memory)

    def test_camera_chain_keeps_raw_rotation_without_claiming_projection(self):
        result = self.reader.sample()
        self.assertEqual(result["cameraPositionRaw"]["x"], 12.5)
        self.assertEqual(result["cameraRotationRaw"], [0, -.5, 0, 0])
        self.assertFalse(result["projectionVerified"])

    def test_wrong_component_rejected(self):
        self.memory.blocks[0x23000000][0x10] = 0x50
        with self.assertRaises(ValueError): self.reader.sample()

    def test_unavailable_view_rejected(self):
        struct.pack_into("<Q", self.memory.blocks[0x24000000], 0x260, 0)
        with self.assertRaises(ValueError): self.reader.sample()

    def test_nonfinite_position_rejected(self):
        struct.pack_into("<f", self.memory.blocks[0x25000000], 0x10, math.nan)
        with self.assertRaises(ValueError): self.reader.sample()

if __name__ == "__main__": unittest.main()
