"""Synthetic fixtures: exact particle syntax edits, NBT byte preservation and guards."""
import hashlib
import gzip
import json
from pathlib import Path
import struct
import tempfile
import unittest
import zipfile
import zlib

from pve_arena_particles import (build_particle_candidate, command_spans, convert_dust,
    encode_modified_utf8, masked_nbt, particle_index, patch_nbt, patch_region, tokens)
from pve_arena_port import deterministic_zip
from pve_world_audit import region_chunks
from test_pve_world_port import compound, nbt_string, root_nbt, region


def command_nbt(text, owner="minecraft:command_block"):
    # Deliberately put id after Command, with types and opaque arrays to preserve.
    return root_nbt([(8, "Command", nbt_string(text)),
        (11, "opaque", struct.pack(">i", 3) + struct.pack(">iii", -1, 0, 2147483647)),
        (1, "Invulnerable", b"\x01"), (3, "BossPhase", struct.pack(">i", 7)),
        (8, "id", nbt_string(owner))])


class CommandTests(unittest.TestCase):
    def test_plain_dust_keeps_suffix_and_numbers(self):
        before = "particle minecraft:dust 0.310 1.000 0.494 1 ~ ~1 ~ 1 3 1 0 10 force @a[tag=Boss]"
        after, detail = convert_dust(before)
        self.assertEqual(after, "particle minecraft:dust{color:[0.310f,1.000f,0.494f],scale:1f} ~ ~1 ~ 1 3 1 0 10 force @a[tag=Boss]")
        self.assertEqual(detail["original_numeric_tokens"], ["0.310", "1.000", "0.494", "1"])

    def test_execute_score_preserves_phase_selector_prefix(self):
        prefix = "execute if score Boss Phase matches 2.. at @e[tag=Boss,nbt={Invulnerable:1b}] run "
        after, _ = convert_dust(prefix + "particle dust 1 0 0 2 ~ ~ ~ 0 0 0 0 4 force")
        self.assertTrue(after.startswith(prefix + "particle dust{"))

    def test_score_holder_named_run_particle_not_subcommand(self):
        before = "execute if score run particle matches 1 run say particle dust 1 0 0 1"
        after, _ = convert_dust(before)
        self.assertEqual(after, before)

    def test_nested_execute_is_supported(self):
        before = "execute as @e[tag=Boss] run execute positioned ~ ~1 ~ unless block ~ ~ ~ stone run particle dust 0 1 0 1 ~ ~ ~"
        after, _ = convert_dust(before)
        self.assertIn("run particle dust{color:[0f,1f,0f],scale:1f}", after)

    def test_transition_old_argument_order(self):
        after, _ = convert_dust("particle dust_color_transition 1 0 .5 .25 0 1 0 ~ ~ ~")
        self.assertEqual(after, "particle dust_color_transition{from_color:[1f,0f,.5f],scale:.25f,to_color:[0f,1f,0f]} ~ ~ ~")

    def test_quoted_json_and_snbt_not_commands(self):
        for before in ('tellraw @a {"text":"particle dust 1 0 0 1"}',
                       'setblock ~ ~ ~ command_block{Command:"particle dust 1 0 0 1"}',
                       'say particle dust 1 0 0 1'):
            self.assertEqual(convert_dust(before)[0], before)

    def test_target_options_are_idempotent(self):
        first, _ = convert_dust("particle dust 1 0 0 1 ~ ~ ~")
        self.assertEqual(convert_dust(first), (first, None))

    def test_bad_numbers_unknown_execute_and_out_of_range_unchanged(self):
        for before in ("particle dust nan 0 0 1", "particle dust 2 0 0 1", "particle dust 1 0 0 0",
                       "particle dust 1e-2 0 0 1", "particle dust 1 0 0 1f",
                       "execute store result score x y run particle dust 1 0 0 1"):
            after, detail = convert_dust(before)
            self.assertEqual(after, before)
            self.assertIn("blocked", detail)

    def test_opaque_tokens_and_unbalanced_fail_closed(self):
        self.assertEqual(tokens('execute as @e[nbt={CustomName:\'{"text":"run particle"}\'}] run say ok')[2][0],
                         '@e[nbt={CustomName:\'{"text":"run particle"}\'}]')
        self.assertEqual(convert_dust('particle dust 1 0 0 1 @e[broken')[0], 'particle dust 1 0 0 1 @e[broken')


class NbtTests(unittest.TestCase):
    def test_native_owner_and_all_other_nbt_bytes_preserved(self):
        raw = command_nbt("particle dust 1 0 0 1 ~ ~ ~")
        output, changes, blocked = patch_nbt(raw, "fixture")
        self.assertEqual(len(changes), 1)
        self.assertFalse(blocked)
        self.assertNotEqual(raw, output)
        self.assertEqual(masked_nbt(raw, command_spans(raw, "fixture")), masked_nbt(output, command_spans(output, "fixture")))

    def test_false_command_owner_is_never_modified(self):
        raw = command_nbt("particle dust 1 0 0 1", owner="demo:custom_data")
        output, changes, blocked = patch_nbt(raw, "fixture")
        self.assertEqual(output, raw)
        self.assertFalse(changes)
        self.assertEqual(blocked[0]["reason"], "owner_is_not_native_command_block_or_minecart")

    def test_damage_and_scoreboard_commands_preserved(self):
        before = root_nbt([(9, "children", b"\x0a" + struct.pack(">i", 3)
            + b"".join(compound([(8, "id", nbt_string("minecraft:command_block")),
                                (8, "Command", nbt_string(text))])
                for text in ("damage @e[tag=Boss,limit=1] 7 magic", "scoreboard players set Boss Phase 3", "particle dust 0 0 1 1")))])
        output, changes, _ = patch_nbt(before, "fixture")
        self.assertEqual(len(changes), 1)
        self.assertEqual([r["text"] for r in command_spans(output, "fixture")][:2],
                         ["damage @e[tag=Boss,limit=1] 7 magic", "scoreboard players set Boss Phase 3"])

    def test_utf8_modified_astral_and_nul_roundtrip(self):
        text = "say \0\U0001f600"
        raw = root_nbt([(8, "id", nbt_string("minecraft:command_block")),
                        (8, "Command", encode_modified_utf8(text))])
        self.assertEqual(command_spans(raw, "fixture")[0]["text"], text)

    def test_second_pass_has_no_mutation(self):
        raw = command_nbt("particle dust 1 0 0 1")
        one, _, _ = patch_nbt(raw, "fixture")
        two, changes, blocked = patch_nbt(one, "fixture")
        self.assertEqual(one, two)
        self.assertFalse(changes)
        self.assertFalse(blocked)

    def test_region_preserves_timestamps_and_other_chunk(self):
        raw0 = command_nbt("particle dust 1 0 0 1")
        raw2 = command_nbt("scoreboard players set Boss Phase 5")
        header, chunks = bytearray(8192), []
        header[4096:8192] = bytes([123]) * 4096
        offset = 2
        for slot, raw in ((0, raw0), (2, raw2)):
            blob = zlib.compress(raw)
            body = struct.pack(">I", len(blob) + 1) + b"\x02" + blob
            sectors = (len(body) + 4095) // 4096
            header[slot * 4:slot * 4 + 4] = struct.pack(">I", (offset << 8) | sectors)
            chunks.append(body.ljust(sectors * 4096, b"\0"))
            offset += sectors
        before = bytes(header) + b"".join(chunks)
        after, changes, blocked, count = patch_region(before, "fixture.mca")
        self.assertEqual(count, 2)
        self.assertEqual(len(changes), 1)
        self.assertEqual(after[4096:8192], before[4096:8192])
        self.assertEqual(dict(region_chunks(after))[2], raw2)

    def test_unchanged_region_byte_identical(self):
        raw = region(command_nbt("damage @s 1 magic"), padding=False)
        self.assertEqual(patch_region(raw, "fixture.mca")[0], raw)


class PackageTests(unittest.TestCase):
    def test_private_guards_atomic_publish_repeat_and_payloads(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            level = root_nbt([(10, "Data", compound([(3, "DataVersion", struct.pack(">i", 3700))]))])
            payloads = {"level.dat": gzip.compress(level, mtime=0),
                "region/r.0.0.mca": region(command_nbt("particle dust 1 0 0 1 ~ ~ ~")),
                "resources.zip": b"opaque original resource", "data/scoreboard.dat": gzip.compress(root_nbt([]), mtime=0)}
            source = root / "parent.zip"
            source.write_bytes(deterministic_zip(payloads))
            sha = hashlib.sha256(source.read_bytes()).hexdigest()
            private = root / "private"
            out = private / "dust.zip"
            with self.assertRaises(ValueError):
                build_particle_candidate(source, root / "outside.zip", expected_sha256=sha, private_root=private)
            with self.assertRaises(ValueError):
                build_particle_candidate(source, out, expected_sha256="0" * 64, private_root=private)
            report = build_particle_candidate(source, out, expected_sha256=sha, private_root=private)
            self.assertFalse(out.with_suffix(".building").exists())
            self.assertFalse(report["compatibility"]["installable"])
            self.assertEqual(report["converted_commands"], 1)
            with zipfile.ZipFile(out) as z:
                for name in ("level.dat", "resources.zip", "data/scoreboard.dat"):
                    self.assertEqual(z.read(name), payloads[name])
            with self.assertRaises(FileExistsError):
                build_particle_candidate(source, out, expected_sha256=sha, private_root=private)
            repeated = build_particle_candidate(source, private / "repeat.zip", expected_sha256=sha, private_root=private)
            self.assertEqual(report["output_sha256"], repeated["output_sha256"])
            self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(), sha)


if __name__ == "__main__":
    unittest.main()
