"""Semantic ledger and acquisition-gate checks; no games/build/network."""
import copy
import json
import unittest

import classify_voice_catalog as base
import review_voice_catalog_round2 as review


class SemanticReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = review.read(base.DEFAULT / "catalog.json")
        existing, _ = base.local_assets(base.PRIVATE)
        cls.first = base.classify_catalog(cls.catalog, existing)
        cls.second = review.apply_review(cls.first)
        cls.by_hash = {row["hash"]: row for rows in cls.second.values() for row in rows}

    def test_all_reviewed_batches_are_complete(self):
        ledger = review.read(review.LEDGER)
        source = review.read(review.SOURCE)
        self.assertEqual(7511, sum(map(len, source.values())))
        self.assertEqual(8087, len(ledger["decisions"]))
        self.assertEqual(66, len(ledger["batches"]))
        self.assertTrue(all(batch["count"] <= 150 for batch in ledger["batches"].values()))
        self.assertTrue(all(row["hash"] in ledger["decisions"] for rows in source.values() for row in rows))

    def test_original_catalogue_fields_and_count_preserved(self):
        self.assertEqual(11361, sum(map(len, self.second.values())))
        for hero, rows in self.catalog.items():
            for original, after in zip(rows, self.second[hero]):
                self.assertEqual(original, {key: after[key] for key in original})
                self.assertFalse(after["deployment_allowed"])

    def test_empty_subtitles_are_not_invented(self):
        for rows in self.second.values():
            for row in rows:
                if review.empty(row):
                    self.assertEqual("uncertain", row["event"])
                    self.assertFalse(row["download_recommended"])

    def test_reapplication_is_stable(self):
        self.assertEqual(self.second, review.apply_review(self.second))

    def test_changed_subtitle_is_rejected(self):
        bad = copy.deepcopy(self.first)
        decided = next(iter(review.read(review.LEDGER)["decisions"]))
        row = next(row for rows in bad.values() for row in rows if row["hash"] == decided)
        row["text"] += " changed"
        with self.assertRaisesRegex(ValueError, "changed after review"):
            review.apply_review(bad)

    def test_download_gates_and_optional_schema(self):
        download = review.compact_download(self.second)
        self.assertTrue(download)
        self.assertEqual(len(download), len({row["hash"] for row in download}))
        for item in download:
            row = self.by_hash[item["hash"]]
            self.assertFalse(row["local_asset_verified"])
            self.assertFalse(row["needs_language_review"])
            self.assertNotIn(row["event"], {"comm", "healing_request", "skip", "uncertain", "effort", "select"})
            self.assertNotIn(row["connection"], {"missing_success_commit", "unreachable_counter_value"})
            optional_event = row["event"] in {"reload", "idle"} or row["event"].startswith("status:")
            self.assertEqual(optional_event, item.get("optional", False))
            self.assertEqual({"hero", "hash", "url", "event", *({"optional"} if optional_event else set())}, set(item))
        for row in self.second["symmetra"]:
            if row["event"] == "ability:teleporter_charges" and row["remaining_uses"] > 6:
                self.assertFalse(row["download_recommended"])
        for row in self.second["dva"]:
            if row["event"].startswith("ability:") or row["event"] == "ult_cast":
                self.assertFalse(row["download_recommended"])


if __name__ == "__main__":
    unittest.main()
