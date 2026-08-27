"""Regression tests for the Provider relational and semantic models."""

from __future__ import annotations

import csv
import hashlib
import json
import sqlite3
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATABASE = ROOT / "data" / "processed" / "provider_quality.sqlite"
MODEL_OUTPUT = ROOT / "outputs" / "provider_model" / "2026-08-26"
SEMANTIC_OUTPUT = ROOT / "outputs" / "powerbi"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


class ProviderModelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = json.loads(
            (MODEL_OUTPUT / "model_manifest.json").read_text(encoding="utf-8")
        )
        cls.connection = sqlite3.connect(DATABASE)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.connection.close()

    def test_database_matches_manifest(self) -> None:
        self.assertTrue(DATABASE.is_file())
        self.assertEqual(self.manifest["database_sha256"], sha256(DATABASE))
        self.assertEqual(
            self.manifest["database_size_bytes"], DATABASE.stat().st_size
        )

    def test_expected_table_counts(self) -> None:
        expected = {
            "dim_facility": 5440,
            "dim_geography": 56,
            "dim_measure": 29,
            "dim_reporting_period": 8,
            "dim_source_release": 6,
            "fact_provider_hrrp_measure": 18330,
            "fact_provider_measure": 67060,
            "fact_provider_national_benchmark": 14,
            "fact_provider_program_score": 2455,
            "fact_provider_state_benchmark": 784,
            "fact_quality_check": 115,
        }
        self.assertEqual(expected, self.manifest["table_row_counts"])
        for table, expected_count in expected.items():
            with self.subTest(table=table):
                actual = self.connection.execute(
                    f'SELECT COUNT(*) FROM "{table}"'
                ).fetchone()[0]
                self.assertEqual(expected_count, actual)

    def test_all_model_quality_checks_pass(self) -> None:
        with (MODEL_OUTPUT / "model_quality_checks.csv").open(
            "r", encoding="utf-8-sig", newline=""
        ) as source:
            rows = list(csv.DictReader(source))
        self.assertEqual(33, len(rows))
        self.assertEqual([], [row for row in rows if row["status"] != "PASS"])

    def test_unmatched_facility_versions_are_preserved(self) -> None:
        count = self.connection.execute(
            """
            SELECT COUNT(*)
            FROM dim_facility
            WHERE is_current_general_info_match = 0
            """
        ).fetchone()[0]
        self.assertEqual(21, count)

    def test_interval_exceptions_are_only_footnote_29(self) -> None:
        with (MODEL_OUTPUT / "interval_order_exceptions.csv").open(
            "r", encoding="utf-8-sig", newline=""
        ) as source:
            rows = list(csv.DictReader(source))
        self.assertEqual(0, len(rows))

    def test_benchmark_join_coverage_reconciles(self) -> None:
        row = self.connection.execute(
            """
            SELECT
                provider_measure_rows,
                state_benchmark_matched_rows,
                national_benchmark_matched_rows
            FROM vw_provider_benchmark_join_coverage
            """
        ).fetchone()
        self.assertEqual((67060, 67060, 67060), row)

    def test_required_reporting_views_exist(self) -> None:
        expected = {
            "vw_provider_measure_reporting",
            "vw_provider_hrrp_reporting",
            "vw_provider_hvbp_reporting",
            "vw_provider_suppression_summary",
            "vw_provider_benchmark_join_coverage",
            "vw_provider_data_quality_summary",
        }
        actual = {
            row[0]
            for row in self.connection.execute(
                """
                SELECT name
                FROM sqlite_master
                WHERE type = 'view'
                """
            )
        }
        self.assertTrue(expected.issubset(actual))

    def test_semantic_model_validation_passes(self) -> None:
        payload = json.loads(
            (SEMANTIC_OUTPUT / "semantic_model_validation.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual({"PASS": 106}, payload["status_counts"])
        self.assertTrue(
            all(check["status"] == "PASS" for check in payload["checks"])
        )

    def test_power_bi_contract_artifacts_exist(self) -> None:
        paths = [
            ROOT / "powerbi" / "semantic_model.json",
            ROOT / "powerbi" / "model_spec.md",
            ROOT / "powerbi" / "dax_measures.md",
            ROOT
            / "powerbi"
            / "ProviderQuality.SemanticModel"
            / "definition.pbism",
        ]
        for path in paths:
            with self.subTest(path=path.name):
                self.assertTrue(path.is_file())
                self.assertGreater(path.stat().st_size, 50)

    def test_power_bi_import_exports_match_model(self) -> None:
        manifest = json.loads(
            (
                ROOT
                / "data"
                / "processed"
                / "powerbi_import"
                / "export_manifest.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(11, len(manifest["exports"]))
        self.assertEqual(
            self.manifest["database_sha256"],
            manifest["source_database_sha256"],
        )
        self.assertEqual(
            94297, sum(item["row_count"] for item in manifest["exports"])
        )
        for item in manifest["exports"]:
            with self.subTest(table=item["semantic_table"]):
                path = ROOT / item["path"]
                self.assertTrue(path.is_file())
                self.assertEqual(item["sha256"], sha256(path))
                self.assertEqual(item["file_size_bytes"], path.stat().st_size)
                self.assertEqual(
                    self.manifest["table_row_counts"][item["source_object"]],
                    item["row_count"],
                )

    def test_tmdl_round_trip_validation_passes(self) -> None:
        payload = json.loads(
            (SEMANTIC_OUTPUT / "tmdl_validation.json").read_text(
                encoding="utf-8-sig"
            )
        )
        self.assertEqual("PASS", payload["status"])
        self.assertEqual(11, payload["table_count"])
        self.assertEqual(19, payload["relationship_count"])
        self.assertEqual(15, payload["measure_count"])
        definition = (
            ROOT
            / "powerbi"
            / "ProviderQuality.SemanticModel"
            / "definition"
        )
        self.assertEqual(
            11, len(list((definition / "tables").glob("*.tmdl")))
        )


if __name__ == "__main__":
    unittest.main()
