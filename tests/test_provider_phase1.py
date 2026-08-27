"""Regression tests for the accepted Provider Phase 1 snapshot."""

from __future__ import annotations

import csv
import hashlib
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = ROOT / "data" / "raw" / "provider" / "2026-07-29"
OUTPUT = ROOT / "outputs" / "provider_phase1" / "2026-07-29"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


class ProviderPhase1Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = json.loads(
            (SNAPSHOT / "provider_snapshot_manifest.json").read_text(
                encoding="utf-8"
            )
        )

    def test_required_dataset_ids_are_present(self) -> None:
        expected = {
            "xubh-q36u",
            "632h-zaca",
            "4gkm-5ypv",
            "cvcs-xecj",
            "9n3s-kdb3",
            "ypbt-wvdk",
        }
        actual = {row["dataset_id"] for row in self.manifest["datasets"]}
        self.assertEqual(expected, actual)

    def test_raw_files_match_manifest_hash_and_shape(self) -> None:
        for row in self.manifest["datasets"]:
            with self.subTest(dataset_id=row["dataset_id"]):
                path = ROOT / row["raw_path"]
                self.assertTrue(path.is_file())
                self.assertEqual(row["sha256"], sha256(path))
                self.assertEqual(row["file_size_bytes"], path.stat().st_size)
                with path.open(
                    "r", encoding="utf-8-sig", newline=""
                ) as source:
                    reader = csv.reader(source)
                    header = next(reader)
                    data_rows = sum(1 for _ in reader)
                self.assertEqual(row["column_count"], len(header))
                self.assertEqual(row["row_count"], data_rows)

    def test_catalog_dates_are_recorded(self) -> None:
        for row in self.manifest["datasets"]:
            with self.subTest(dataset_id=row["dataset_id"]):
                self.assertTrue(row["source_modified_date"])
                self.assertEqual("2026-05-13", row["source_release_date"])
                self.assertEqual("2026-07-29", row["download_date"])

    def test_quality_checks_have_no_nonpass_status(self) -> None:
        with (OUTPUT / "quality_checks.csv").open(
            "r", encoding="utf-8-sig", newline=""
        ) as source:
            rows = list(csv.DictReader(source))
        self.assertGreaterEqual(len(rows), 80)
        nonpass = [row for row in rows if row["status"] != "PASS"]
        self.assertEqual([], nonpass)

    def test_candidate_grains_are_unique_and_complete(self) -> None:
        with (OUTPUT / "dataset_summary.csv").open(
            "r", encoding="utf-8-sig", newline=""
        ) as source:
            rows = list(csv.DictReader(source))
        self.assertEqual(6, len(rows))
        for row in rows:
            with self.subTest(dataset_id=row["dataset_id"]):
                self.assertTrue(row["candidate_key"])
                self.assertEqual("0", row["candidate_key_blank_rows"])
                self.assertEqual("0", row["candidate_key_duplicate_rows"])
                self.assertEqual("0", row["exact_duplicate_rows"])

    def test_measure_dictionary_covers_observed_measure_ids(self) -> None:
        dictionary_text = (
            ROOT / "docs" / "measure_dictionary.md"
        ).read_text(encoding="utf-8")
        observed: set[str] = set()
        with (OUTPUT / "measure_catalog.csv").open(
            "r", encoding="utf-8-sig", newline=""
        ) as source:
            for row in csv.DictReader(source):
                observed.add(row["measure_id"] or row["measure_name"])
        missing = sorted(
            measure for measure in observed if measure not in dictionary_text
        )
        self.assertEqual([], missing)

    def test_required_governance_documents_exist(self) -> None:
        names = {
            "business_requirements.md",
            "source_inventory.md",
            "source_to_target_mapping.md",
            "measure_dictionary.md",
            "data_quality_plan.md",
            "limitations.md",
            "provider_mvp_implementation_plan.md",
        }
        for name in names:
            with self.subTest(name=name):
                path = ROOT / "docs" / name
                self.assertTrue(path.is_file())
                self.assertGreater(path.stat().st_size, 500)


if __name__ == "__main__":
    unittest.main()

