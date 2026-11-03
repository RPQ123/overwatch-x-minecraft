"""Fixtures only: archive rejection and catalog admission, never launches Minecraft."""
import gzip
import json
from pathlib import Path
import stat
import struct
import tempfile
import unittest
import zipfile

from pve_map_catalog import ACCEPTANCE, challenge_ready, level_metadata, load_catalog, preflight, safe_member


def text(value):
    value = value.encode("utf-8")
    return struct.pack(">H", len(value)) + value


def named(tag, name, value):
    return bytes([tag]) + text(name) + value


def level(data_version=3955, version_name="1.21.1"):
    version = named(8, "Name", text(version_name)) + b"\0"
    data = (named(3, "DataVersion", struct.pack(">i", data_version))
            + named(8, "LevelName", text("Fixture only"))
            + named(10, "Version", version) + b"\0")
    return gzip.compress(b"\x0a\x00\x00" + named(10, "Data", data) + b"\0")


class MapPreflightTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def archive(self, members):
        target = self.root / "fixture.zip"
        with zipfile.ZipFile(target, "w") as z:
            for name, value in members:
                z.writestr(name, value)
        return target

    def test_metadata_does_not_claim_gameplay(self):
        path = self.archive([("World/level.dat", level()), ("World/region/r.0.0.mca", b"fixture")])
        before = sorted(str(p) for p in self.root.rglob("*"))
        result = preflight(path)
        self.assertTrue(result["archive_preflight"])
        self.assertEqual(result["level"]["version_name"], "1.21.1")
        self.assertEqual(result["level"]["data_version"], 3955)
        self.assertFalse(any(result[key] for key in ("installed", "world_load", "boss_fight", "reset_replay")))
        self.assertEqual(before, sorted(str(p) for p in self.root.rglob("*")))

    def test_pack_and_instructions_inventory(self):
        path = self.archive([("level.dat", level()), ("resources.zip", b"uninspected nested zip"),
                             ("datapacks/custom/pack.mcmeta", b"{}"), ("README.txt", b"text")])
        result = preflight(path)
        self.assertTrue(result["archive_preflight"])
        self.assertEqual(result["resource_packs"], ["resources.zip"])
        self.assertEqual(result["data_pack_entries"], ["datapacks/custom/pack.mcmeta"])
        self.assertEqual(result["readme_entries"], ["README.txt"])

    def test_actual_newer_nbt_is_not_replaced_by_target_version(self):
        path = self.archive([("level.dat", level(4189, "1.21.4"))])
        result = preflight(path)
        self.assertTrue(result["archive_preflight"])
        self.assertEqual(result["level"]["data_version"], 4189)
        self.assertEqual(result["level"]["version_name"], "1.21.4")
        self.assertFalse(result["world_load"])

    def test_windows_unsafe_names(self):
        for name in ("../escape", "/absolute", "C:/world", "world\\..\\escape", "W/CON.txt",
                     "W/LPT1", "W/a.", "W/a ", "W//x", "W/./x", "W/f:stream", "W/a?", "W/a\x01", ""):
            with self.subTest(name=name), self.assertRaises(ValueError):
                safe_member(name)

    def test_alias_rejected(self):
        path = self.archive([("World/level.dat", level()), ("WORLD/LEVEL.DAT", level())])
        self.assertFalse(preflight(path)["archive_preflight"])

    def test_symlink_rejected(self):
        link = zipfile.ZipInfo("World/link")
        link.create_system = 3
        link.external_attr = (stat.S_IFLNK | 0o777) << 16
        path = self.archive([("World/level.dat", level()), (link, "../../outside")])
        self.assertFalse(preflight(path)["archive_preflight"])

    def test_installer_and_mod_jar_rejected(self):
        for name in ("Setup.exe", "World/mods/mod.jar", "World/fix.cmd", "World/run.ps1"):
            with self.subTest(name=name):
                path = self.archive([("World/level.dat", level()), (name, b"no execution")])
                self.assertFalse(preflight(path)["archive_preflight"])

    def test_expanded_budget_rejected(self):
        path = self.archive([("World/level.dat", level()), ("World/data.bin", b"x" * 100)])
        self.assertFalse(preflight(path, max_total_bytes=10)["archive_preflight"])
        self.assertFalse(preflight(path, max_entry_bytes=10)["archive_preflight"])
        self.assertFalse(preflight(path, max_files=1)["archive_preflight"])

    def test_multiple_worlds_rejected(self):
        path = self.archive([("One/level.dat", level()), ("Two/level.dat", level())])
        self.assertFalse(preflight(path)["archive_preflight"])

    def test_missing_or_malformed_level_rejected(self):
        for members in ([("readme.txt", b"not a world")], [("level.dat", b"not gzip")],
                        [("level.dat", gzip.compress(b"\x0a\x00\x00\x00"))]):
            with self.subTest(members=members):
                self.assertFalse(preflight(self.archive(members))["archive_preflight"])

    def test_corrupt_nbt_lengths_rejected(self):
        bad = b"\x0a\x00\x00" + named(10, "Data", named(7, "bad", struct.pack(">i", -1)) + b"\0") + b"\0"
        with self.assertRaises(ValueError):
            level_metadata(gzip.compress(bad))

    def test_readiness_requires_all_actual_gates(self):
        row = {"compatibility": {"status": "accepted"}, "acceptance": dict.fromkeys(ACCEPTANCE, True)}
        self.assertTrue(challenge_ready(row))
        for key in ACCEPTANCE:
            partial = {**row, "acceptance": {**row["acceptance"], key: False}}
            self.assertFalse(challenge_ready(partial))
        for status in ("pending", "incompatible"):
            self.assertFalse(challenge_ready({**row, "compatibility": {"status": status}}))

    def test_catalog_cannot_label_candidate_ready(self):
        path = self.root / "catalog.json"
        path.write_text(json.dumps({"schema_version": 1, "maps": [{"id": "one", "source_url": "https://author.example/map", "status": "ready"}]}), encoding="utf-8")
        with self.assertRaises(ValueError):
            load_catalog(path)

    def test_production_metadata_admission_is_consistent(self):
        catalog = load_catalog()
        self.assertEqual(len(catalog["maps"]), 5)
        for row in catalog["maps"]:
            if row["status"] == "ready":
                self.assertTrue(challenge_ready(row))


if __name__ == "__main__":
    unittest.main()
