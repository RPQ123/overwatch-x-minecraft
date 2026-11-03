"""Synthetic memory-layout tests; these fixtures aren't original game captures."""
from pathlib import Path
import math
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.observe_overwatch import PoseReader


class FakeMemory:
    base = 0x10000000
    def __init__(self):
        self.blocks = {}
    def put(self, address, data):
        self.blocks[address] = data
    def read(self, address, size):
        for start, data in self.blocks.items():
            if start <= address and address + size <= start + len(data):
                return data[address - start:address - start + size]
        raise OSError("Unmapped synthetic address")


class MemoryTests(unittest.TestCase):
    def setUp(self):
        self.memory = FakeMemory()
        self.reader = PoseReader(self.memory)
        self.memory.put(self.memory.base + 0x17b7f90, struct.pack("<Q", 0x20000000))
        admin = bytearray(0x230)
        struct.pack_into("<Q", admin, 0x10, 0x21000000)
        struct.pack_into("<I", admin, 0x220, 1)
        self.memory.put(0x20000000, admin)
        table = bytearray(65536)
        struct.pack_into("<Qii", table, 0, 0x22000000, 1, 8)
        struct.pack_into("<Qii", table, 16, 0x22001000, 1, 8)
        self.memory.put(0x21000000, table)
        self.memory.put(0x22000000, struct.pack("<IIQ", 1, 0, 0x23000000))
        self.memory.put(0x22001000, struct.pack("<IIQ", 2, 0, 0x23001000))
        for entity, pointers, component in ((0x23000000, 0x24000000, 0x25000000),
                                            (0x23001000, 0x24001000, 0x25001000)):
            data = bytearray(0xA0)
            struct.pack_into("<Qii", data, 0x50, pointers, 2, 2)
            self.memory.put(entity, data)
            self.memory.put(pointers, struct.pack("<Q", component))
        reference = bytearray(0xA0)
        struct.pack_into("<Q", reference, 8, 0x23000000)
        reference[0x10] = 0x20
        struct.pack_into("<I", reference, 0x94, 2)
        self.memory.put(0x25000000, reference)
        movement = bytearray(0xA50 + 0x270)
        struct.pack_into("<Q", movement, 8, 0x23001000)
        movement[0x10] = 0x15
        struct.pack_into("<i", movement, 0xA50 + 0x1A0, 42)
        struct.pack_into("<ffff", movement, 0xA50 + 0x220, 12.5, -3, 42, 1)
        self.memory.put(0x25001000, movement)

    def test_original_layout_pointer_chain(self):
        self.assertEqual(self.reader.sample(), {"transport": "read-only-process-memory", "upstreamTick": 42,
                                                "position": {"x": 12.5, "y": -3, "z": 42}})

    def test_wrong_component_owner_rejected(self):
        struct.pack_into("<Q", self.memory.blocks[0x25001000], 8, 0x23000000)
        with self.assertRaises(ValueError):
            self.reader.sample()

    def test_absent_entity_or_pointer_rejected(self):
        struct.pack_into("<I", self.memory.blocks[0x20000000], 0x220, 999)
        with self.assertRaises(ValueError):
            self.reader.sample()
        self.memory.put(self.memory.base + 0x17b7f90, struct.pack("<Q", 0))
        with self.assertRaises(ValueError):
            self.reader.sample()

    def test_invalid_component_count_rejected(self):
        struct.pack_into("<i", self.memory.blocks[0x23000000], 0x58, 10000)
        with self.assertRaises(ValueError):
            self.reader.sample()

    def test_invalid_movement_state_rejected(self):
        state = self.memory.blocks[0x25001000]
        for invalid in (math.nan, math.inf, 1e8):
            struct.pack_into("<f", state, 0xA50 + 0x220, invalid)
            with self.assertRaises(ValueError):
                self.reader.sample()
        struct.pack_into("<f", state, 0xA50 + 0x220, 12.5)
        struct.pack_into("<i", state, 0xA50 + 0x1A0, -1)
        with self.assertRaises(ValueError):
            self.reader.sample()


if __name__ == "__main__":
    unittest.main()
