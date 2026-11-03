"""Malformed-export regression tests; fixtures contain no Blizzard data."""
import struct
import tempfile
from pathlib import Path
import unittest
from owlib_projectile_assets import Reader, model, material, pack_projectile


class ExportBoundsTests(unittest.TestCase):
    def test_string_rejects_unbounded_prefix_and_truncation(self):
        for raw in (b'\x80'*5, b'\xff\x7f', b'\x04abc'):
            with self.assertRaises(ValueError): Reader(raw).string()

    def test_nan_geometry_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'nonfinite'):
            Reader(struct.pack('<3f', 0, float('nan'), 1)).array(1, 3)

    def test_model_wrong_version_and_material_unknown_kind(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'test.bin';p.write_bytes(struct.pack('<HH', 3, 0))
            with self.assertRaisesRegex(ValueError,'OWMDL'): model(p)
            p.write_bytes(struct.pack('<HHI', 3, 0, 19))
            with self.assertRaisesRegex(ValueError,'material type'): material(p)

    def test_game_assets_cannot_be_written_into_repository(self):
        with self.assertRaisesRegex(ValueError, 'outside the repository'):
            pack_projectile(Path(__file__).parent,Path(__file__).parent/'forbidden-game-data')


if __name__=='__main__': unittest.main()
