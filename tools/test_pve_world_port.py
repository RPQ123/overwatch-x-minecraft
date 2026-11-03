"""Fixtures for bounded inspection and deliberately partial private conversion."""
from __future__ import annotations

import gzip
import hashlib
import io
import json
from pathlib import Path
import struct
import tempfile
import unittest
import zipfile
import zlib

from pve_arena_port import PACKS, build_candidate, deterministic_zip, migrate_json, renamed_path, transform_pack
from pve_world_audit import Findings, bounded_inflate, parse_nbt, region_chunks, scan_nbt


def nbt_string(value: str) -> bytes:
    raw = value.encode("utf-8")
    return struct.pack(">H", len(raw)) + raw


def compound(values: list[tuple[int, str, bytes]]) -> bytes:
    return b"".join(bytes([tag]) + nbt_string(name) + payload for tag, name, payload in values) + b"\0"


def root_nbt(values) -> bytes:
    return b"\x0a\0\0" + compound(values)


def region(raw: bytes, *, padding=True) -> bytes:
    payload = zlib.compress(raw)
    chunk = struct.pack(">I", len(payload) + 1) + b"\x02" + payload
    count = (len(chunk) + 4095) // 4096
    header = struct.pack(">I", (2 << 8) | count) + bytes(8192 - 4)
    return header + chunk + (bytes(count * 4096 - len(chunk)) if padding else b"")


class AuditTests(unittest.TestCase):
    def test_stream_retains_commands_and_skips_array_values(self):
        raw = root_nbt([(11, "array", struct.pack(">i", 3) + bytes(12)),
                        (8, "Command", nbt_string("give @s stick{CustomModelData:1}")),
                        (3, "DataVersion", struct.pack(">i", 3700))])
        report = Findings()
        scan_nbt(raw, report, "fixture")
        self.assertEqual(report.report()["unique_commands"], 1)
        self.assertEqual(report.report()["risk_occurrences"]["legacy_item_command"], 1)
        self.assertEqual(report.versions["3700"], 1)

    def test_modified_utf8_surrogates_and_nul(self):
        text = b"\xc0\x80\xed\xa0\xbd\xed\xb8\x80"
        raw = root_nbt([(8, "name", struct.pack(">H", len(text)) + text)])
        self.assertEqual(parse_nbt(raw)["name"], "\0\U0001f600")

    def test_duplicate_compound_fails_closed(self):
        with self.assertRaises(ValueError):
            scan_nbt(root_nbt([(1, "a", b"\0"), (1, "a", b"\0")]), Findings(), "fixture")

    def test_negative_array_rejected(self):
        with self.assertRaises(ValueError):
            scan_nbt(root_nbt([(11, "array", struct.pack(">i", -1))]), Findings(), "fixture")

    def test_large_structure_list_is_streamed(self):
        # Exceeds the small level.dat reader's list budget without making 100k dicts.
        raw = root_nbt([(9, "blocks", b"\x01" + struct.pack(">i", 100_001) + bytes(100_001)),
                       (8, "Command", nbt_string("say after_large_list"))])
        f = Findings()
        scan_nbt(raw, f, "structure")
        self.assertEqual(f.report()["unique_commands"], 1)

    def test_region_padded_and_unpadded_read_same_payload(self):
        raw = root_nbt([(8, "Command", nbt_string("say fixture"))])
        self.assertEqual(list(region_chunks(region(raw)))[0][1], raw)
        self.assertEqual(list(region_chunks(region(raw, padding=False)))[0][1], raw)
        self.assertEqual(list(region_chunks(b"")), [])

    def test_region_overlap_external_and_truncation_rejected(self):
        original = region(root_nbt([]))
        overlap = bytearray(original)
        overlap[4:8] = overlap[0:4]
        external = bytearray(original)
        external[8196] = 130
        for value in (bytes(overlap), bytes(external), original[:8197]):
            with self.assertRaises(ValueError):
                list(region_chunks(value))

    def test_inflate_budget_and_trailing_data(self):
        for raw in (zlib.compress(b"x" * 100), zlib.compress(b"ok") + b"tail"):
            with self.assertRaises(ValueError):
                bounded_inflate(raw, 2, limit=16)

    def test_nested_chat_run_command_recorded(self):
        f = Findings()
        f.walk(json.dumps({"text": "Go", "clickEvent": {"action": "run_command", "value": "/function demo:start"}}), "sign")
        self.assertEqual(f.report()["counts"]["json_click_command"], 1)


class PortTests(unittest.TestCase):
    def pack(self):
        return deterministic_zip({
            "pack.mcmeta": b'{"pack":{"pack_format":10,"description":"fixture"}}',
            "data/demo/functions/start.mcfunction": b"say fixture\n",
            "data/minecraft/tags/functions/load.json": b'{"values":["demo:start"]}'})

    def test_only_registry_directory_segments_renamed(self):
        self.assertEqual(renamed_path("data/demo/tags/entity_types/boss.json"), "data/demo/tags/entity_type/boss.json")
        self.assertEqual(renamed_path("assets/demo/functions/recipes.png"), "assets/demo/functions/recipes.png")
        self.assertEqual(renamed_path("data/demo/function/my_functions.mcfunction"), "data/demo/function/my_functions.mcfunction")

    def test_recipe_context_does_not_rewrite_ingredient_items(self):
        original = {"type": "minecraft:crafting_shapeless", "ingredients": [{"item": "minecraft:stone"}], "result": {"item": "minecraft:button", "count": 1}}
        result, rules, blockers = migrate_json("data/demo/recipe/button.json", original)
        self.assertEqual(result["ingredients"], original["ingredients"])
        self.assertEqual(result["result"], {"id": "minecraft:button", "count": 1})
        self.assertIn("item", original["result"])
        self.assertFalse(blockers)

    def test_custom_head_nbt_never_discarded(self):
        original = {"display": {"icon": {"item": "minecraft:player_head", "nbt": "{SkullOwner:'fixture'}"}}}
        result, rules, blockers = migrate_json("data/demo/advancement/root.json", original)
        self.assertEqual(result, original)
        self.assertTrue(blockers)
        self.assertFalse(rules)

    def test_loot_exact_function_context(self):
        value = {"pools": [{"entries": [{"functions": [{"function": "minecraft:looting_enchant", "count": {"min": 0, "max": 1}}]}]}], "text": "minecraft:looting_enchant"}
        result, rules, blockers = migrate_json("data/demo/loot_table/x.json", value)
        function = result["pools"][0]["entries"][0]["functions"][0]
        self.assertEqual(function["function"], "minecraft:enchanted_count_increase")
        self.assertEqual(function["enchantment"], "minecraft:looting")
        self.assertEqual(result["text"], value["text"])
        self.assertFalse(blockers)

    def test_path_collision_rejected(self):
        raw = deterministic_zip({"pack.mcmeta": b'{"pack":{"pack_format":10}}',
            "data/demo/functions/a.mcfunction": b"say old", "data/demo/function/a.mcfunction": b"say new"})
        with self.assertRaises(ValueError):
            transform_pack(raw)

    def test_unexpected_pack_format_rejected(self):
        with self.assertRaises(ValueError):
            transform_pack(deterministic_zip({"pack.mcmeta": b'{"pack":{"pack_format":48}}'}))

    def test_nested_installer_and_path_traversal_rejected(self):
        for path in ("run.cmd", "../escape.json"):
            raw = deterministic_zip({"pack.mcmeta": b'{"pack":{"pack_format":10}}', path: b"ignored"})
            with self.assertRaises(ValueError):
                transform_pack(raw)

    def test_transform_deterministic_and_command_bytes_retained(self):
        a, report = transform_pack(self.pack())
        b, _ = transform_pack(self.pack())
        self.assertEqual(a, b)
        with zipfile.ZipFile(io.BytesIO(a)) as z:
            self.assertEqual(z.read("data/demo/function/start.mcfunction"), b"say fixture\n")
            self.assertEqual(json.loads(z.read("pack.mcmeta"))["pack"]["pack_format"], 48)

    def test_private_candidate_guards_and_world_payload_retained(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            level = root_nbt([(10, "Data", compound([(3, "DataVersion", struct.pack(">i", 3700))]))])
            files = {"level.dat": gzip.compress(level, mtime=0), "region/r.0.0.mca": region(root_nbt([])),
                     "resources.zip": b"opaque resource fixture", **{name: self.pack() for name in PACKS}}
            source = root / "original.zip"
            source.write_bytes(deterministic_zip(files))
            sha = hashlib.sha256(source.read_bytes()).hexdigest()
            private = root / "private"
            output = private / "candidate.zip"
            with self.assertRaises(ValueError):
                build_candidate(source, root / "outside.zip", expected_sha256=sha, private_root=private)
            with self.assertRaises(ValueError):
                build_candidate(source, output, expected_sha256="0" * 64, private_root=private)
            self.assertFalse(output.exists())
            report = build_candidate(source, output, expected_sha256=sha, private_root=private)
            with zipfile.ZipFile(output) as z:
                for name in ("level.dat", "region/r.0.0.mca", "resources.zip"):
                    self.assertEqual(z.read(name), files[name])
            self.assertFalse(report["compatibility"]["installable"])
            self.assertFalse(report["acceptance"]["world_load"])
            self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(), sha)
            with self.assertRaises(FileExistsError):
                build_candidate(source, output, expected_sha256=sha, private_root=private)
            output2 = private / "candidate2.zip"
            second = build_candidate(source, output2, expected_sha256=sha, private_root=private)
            self.assertEqual(report["output_sha256"], second["output_sha256"])


if __name__ == "__main__":
    unittest.main()
