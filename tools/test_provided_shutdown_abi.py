"""ABI correction invariants and cold-write refusal; never touch installed DLL."""
import hashlib
import io
from pathlib import Path
import struct
import unittest
from unittest.mock import Mock, patch

import repair_provided_shutdown_abi as abi


class RelocationFixture:
    def __init__(self, block):
        self.data = bytearray(0x300)
        struct.pack_into("<I", self.data, 0x3c, 0x40)
        struct.pack_into("<II", self.data, 0x40 + 24 + 112 + 40, 0x2000, len(block))
        self.data[0x200:0x200 + len(block)] = block

    def file_offset(self, rva):
        if rva != 0x2000:
            raise ValueError("fixture RVA")
        return 0x200


class ShutdownAbiTests(unittest.TestCase):
    def test_changed_target_refused_before_any_write(self):
        stream = io.BytesIO(b"changed!")
        with self.assertRaisesRegex(ValueError, "changed"):
            abi.replace_slot(stream, b"original", b"new-slot", 0, lambda s: None)
        self.assertEqual(stream.getvalue(), b"changed!")

    def test_partial_write_restores_original_under_same_handle(self):
        class ShortOnce(io.BytesIO):
            first = True
            def write(self, value):
                if self.first:
                    self.first = False
                    return super().write(value[:3])
                return super().write(value)
        stream = ShortOnce(b"prefix--old-slot--suffix")
        with self.assertRaisesRegex(RuntimeError, "restored and verified"):
            abi.replace_slot(stream, stream.getvalue(), b"prefix--new-slot--suffix", 8, lambda s: None)
        self.assertEqual(stream.getvalue(), b"prefix--old-slot--suffix")

    def test_flush_failure_rolls_back_and_readback_verifies(self):
        stream = io.BytesIO(b"prefix--old-slot--suffix")
        calls = 0
        def fail_once(s):
            nonlocal calls
            calls += 1
            if calls == 1:
                raise OSError("fixture flush failure")
        with self.assertRaisesRegex(RuntimeError, "restored and verified"):
            abi.replace_slot(stream, stream.getvalue(), b"prefix--new-slot--suffix", 8, fail_once)
        self.assertEqual(stream.getvalue(), b"prefix--old-slot--suffix")

    def test_exact_slot_write_leaves_neighbors_unchanged(self):
        stream = io.BytesIO(b"prefix--old-slot--suffix")
        abi.replace_slot(stream, stream.getvalue(), b"prefix--new-slot--suffix", 8, lambda s: None)
        self.assertEqual(stream.getvalue(), b"prefix--new-slot--suffix")

    def test_readback_mismatch_restores_original(self):
        class CorruptOnce(io.BytesIO):
            writes = 0
            bad = False
            def write(self, value):
                self.writes += 1
                self.bad = self.writes == 1
                return super().write(value)
            def read(self, *args):
                value = super().read(*args)
                if self.bad:
                    self.bad = False
                    return b"!" + value[1:]
                return value
        stream = CorruptOnce(b"prefix--old-slot--suffix")
        with self.assertRaisesRegex(RuntimeError, "restored and verified"):
            abi.replace_slot(stream, stream.getvalue(), b"prefix--new-slot--suffix", 8, lambda s: None)
        self.assertEqual(stream.getvalue(), b"prefix--old-slot--suffix")

    def test_failed_rollback_explicitly_forbids_launch(self):
        class AlwaysShort(io.BytesIO):
            def write(self, value):
                return super().write(value[:3])
        stream = AlwaysShort(b"prefix--old-slot--suffix")
        with self.assertRaisesRegex(RuntimeError, "rollback failed; do not launch"):
            abi.replace_slot(stream, stream.getvalue(), b"prefix--new-slot--suffix", 8, lambda s: None)

    def test_relocations_keep_only_dir64_and_ignore_padding(self):
        image = RelocationFixture(struct.pack("<II4H", 0x271000, 16, 0xa840, 0, 0x3848, 0xa850))
        self.assertEqual(abi.dir64_relocations(image), {0x271840, 0x271850})

    def test_relocations_reject_truncated_or_infinite_blocks(self):
        for block in (b"1234", struct.pack("<II", 0x271000, 0),
                      struct.pack("<II", 0x271000, 12), struct.pack("<II", 0x271000, 9)):
            with self.subTest(block=block):
                with self.assertRaises(ValueError):
                    abi.dir64_relocations(RelocationFixture(block))

    def test_unknown_input_refused_before_interpretation(self):
        with self.assertRaisesRegex(ValueError, "Unrecognized"):
            abi.corrected_payload(b"unknown DLL", b"unknown PDB")

    def test_stage_outside_private_backup_refused_before_reading_game(self):
        with self.assertRaisesRegex(ValueError, "private"):
            abi.stage(Path.cwd() / "unsafe-stage")

    def test_install_outside_private_backup_refused(self):
        with self.assertRaisesRegex(ValueError, "private"):
            abi.install(Path.cwd() / "unsafe-install")

    def test_running_target_or_uncertain_same_name_refused(self):
        exe = (abi.GAME / "GameClientApp.patched.exe").resolve()
        for target in (str(exe), None):
            process = Mock(info={"name": exe.name, "exe": target})
            with self.subTest(target=target), patch.object(Path, "read_bytes", return_value=b"verified-exe"), \
                    patch.object(abi, "digest", return_value=abi.PATCHED_SHA256), \
                    patch.object(abi.psutil, "process_iter", return_value=[process]):
                with self.assertRaisesRegex(RuntimeError, "running"):
                    abi.require_cold()

    def test_wrong_offline_exe_refused(self):
        with patch.object(Path, "read_bytes", return_value=b"wrong"):
            with self.assertRaisesRegex(ValueError, "Offline"):
                abi.require_cold()

    def test_local_exact_binary_diff_and_aslr_oracle(self):
        # Optional local evidence, no supplied bytes enter this test source.
        if not abi.TARGET.exists():
            self.skipTest("private supplied binary is not installed")
        source = abi.TARGET.read_bytes()
        pdb = (abi.GAME / "prometheus.pdb").read_bytes()
        if abi.digest(source) == abi.CORRECTED:
            saved = Path.home() / ".universal-modder/backups/provided-shutdown-abi-20261023/inject.original.dll"
            if not saved.is_file():
                self.skipTest("original oracle is not present in this private checkout")
            source = saved.read_bytes()
        fixed = abi.corrected_payload(source, pdb)
        image, _ = abi.validate(source, pdb)
        offset = image.file_offset(abi.SLOT)
        self.assertEqual(len(source), len(fixed))
        self.assertEqual(source[:offset], fixed[:offset])
        self.assertEqual(source[offset + 8:], fixed[offset + 8:])
        self.assertEqual(sum(a != b for a, b in zip(source, fixed)), 2)
        self.assertEqual(hashlib.sha256(fixed).hexdigest(), abi.CORRECTED)
        self.assertEqual(abi.corrected_payload(fixed, pdb), fixed)
        self.assertIn(abi.SLOT, abi.dir64_relocations(image))
        old, = struct.unpack_from("<Q", source, offset)
        new, = struct.unpack_from("<Q", fixed, offset)
        for mapped_base in (0x180000000, 0x7ffd32000000, 0x7ffcef000000):
            delta = mapped_base - abi.IMAGE_BASE
            self.assertEqual(old + delta, mapped_base + abi.NOOP)
            self.assertEqual(new + delta, mapped_base + abi.ZERO)


if __name__ == "__main__":
    unittest.main()
