"""Regression tests for the CMS Provider freshness record."""

from __future__ import annotations

import csv
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "outputs" / "provider_freshness" / "2026-08-26"


class ProviderFreshnessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.payload = json.loads((OUTPUT / "freshness_check.json").read_text(encoding="utf-8"))

    def test_freshness_audit_passes(self) -> None:
        self.assertEqual("REVIEW", self.payload["status"])
        self.assertEqual({"CHANGED": 6}, self.payload["status_counts"])
        self.assertEqual(6, len(self.payload["datasets"]))

    def test_all_local_hashes_match(self) -> None:
        self.assertTrue(all(row["local_hash_matches"] for row in self.payload["datasets"]))
        self.assertTrue(all(row["release_changed"] for row in self.payload["datasets"]))
        self.assertTrue(any(row["modified_changed"] for row in self.payload["datasets"]))
        self.assertTrue(any(row["csv_url_changed"] for row in self.payload["datasets"]))

    def test_csv_record_matches_json_record(self) -> None:
        with (OUTPUT / "freshness_check.csv").open("r", encoding="utf-8-sig", newline="") as source:
            rows = list(csv.DictReader(source))
        self.assertEqual(6, len(rows))
        self.assertEqual({row["dataset_id"] for row in self.payload["datasets"]}, {row["dataset_id"] for row in rows})


if __name__ == "__main__":
    unittest.main()
