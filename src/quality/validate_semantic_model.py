"""Validate the Power BI semantic-model contract against the Provider DB."""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.common.cms_provider import write_json


REFERENCE_PATTERN = re.compile(r"'([^']+)'\[([^\]]+)\]")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path(__file__).resolve().parents[2],
    )
    return parser.parse_args()


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def main() -> int:
    args = parse_args()
    project_root = args.project_root.resolve()
    spec_path = project_root / "powerbi" / "semantic_model.json"
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    database_path = project_root / spec["source_database"]
    connection = sqlite3.connect(database_path)
    checks: list[dict[str, Any]] = []

    def record(
        check: str,
        status: str,
        details: str,
        severity: str = "Critical",
    ) -> None:
        checks.append(
            {
                "check": check,
                "status": status,
                "severity": severity,
                "details": details,
                "checked_at": now_utc(),
            }
        )

    try:
        semantic_tables = {table["name"]: table for table in spec["tables"]}
        if len(semantic_tables) == len(spec["tables"]):
            record("unique_table_names", "PASS", "All semantic table names are unique.")
        else:
            record("unique_table_names", "FAIL", "Duplicate semantic table names found.")

        source_columns: dict[str, set[str]] = {}
        semantic_columns: dict[str, set[str]] = {}
        for table_name, table in semantic_tables.items():
            source_object = table["source_object"]
            rows = connection.execute(
                f"PRAGMA table_info('{source_object}')"
            ).fetchall()
            source_columns[table_name] = {row[1] for row in rows}
            semantic_columns[table_name] = {
                column["name"] for column in table["columns"]
            }
            missing = sorted(
                column["source"]
                for column in table["columns"]
                if column["source"] not in source_columns[table_name]
            )
            record(
                f"source_columns_{table_name}",
                "PASS" if rows and not missing else "FAIL",
                (
                    f"Source object {source_object}; missing columns: {missing}"
                ),
            )

        relationship_names: set[str] = set()
        for relationship in spec["relationships"]:
            name = relationship["name"]
            if name in relationship_names:
                record(
                    f"relationship_name_{name}",
                    "FAIL",
                    "Duplicate relationship name.",
                )
            relationship_names.add(name)
            from_table = relationship["from_table"]
            to_table = relationship["to_table"]
            valid = (
                from_table in semantic_tables
                and to_table in semantic_tables
                and relationship["from_column"]
                in semantic_columns.get(from_table, set())
                and relationship["to_column"]
                in semantic_columns.get(to_table, set())
            )
            record(
                f"relationship_references_{name}",
                "PASS" if valid else "FAIL",
                "Relationship table and column references resolve.",
            )
            if (
                semantic_tables[from_table]["kind"] == "fact"
                and semantic_tables[to_table]["kind"] == "fact"
            ):
                record(
                    f"no_fact_to_fact_{name}",
                    "FAIL",
                    "Fact-to-fact relationship is prohibited.",
                )
            else:
                record(
                    f"no_fact_to_fact_{name}",
                    "PASS",
                    "Relationship is dimension-to-dimension or dimension-to-fact.",
                )
            if relationship["cross_filter"] != "Single":
                record(
                    f"single_direction_{name}",
                    "FAIL",
                    "Bidirectional filtering is prohibited in this model.",
                    "High",
                )
            else:
                record(
                    f"single_direction_{name}",
                    "PASS",
                    "Relationship uses single-direction filtering.",
                    "High",
                )

            from_column_source = next(
                column["source"]
                for column in semantic_tables[from_table]["columns"]
                if column["name"] == relationship["from_column"]
            )
            source_object = semantic_tables[from_table]["source_object"]
            total, distinct_count = connection.execute(
                f"""
                SELECT COUNT(*), COUNT(DISTINCT "{from_column_source}")
                FROM "{source_object}"
                """
            ).fetchone()
            record(
                f"one_side_unique_{name}",
                "PASS" if total == distinct_count else "FAIL",
                f"One-side rows={total}; distinct keys={distinct_count}.",
                "Critical",
            )

        measures = spec["measures"]
        measure_names = [measure["name"] for measure in measures]
        record(
            "unique_measure_names",
            "PASS" if len(measure_names) == len(set(measure_names)) else "FAIL",
            f"Measure count: {len(measure_names)}.",
        )
        for measure in measures:
            name = measure["name"]
            home_table = measure["home_table"]
            references = REFERENCE_PATTERN.findall(measure["expression"])
            unresolved = [
                f"{table}[{column}]"
                for table, column in references
                if table not in semantic_tables
                or column not in semantic_columns[table]
            ]
            status = (
                "PASS"
                if home_table in semantic_tables and not unresolved
                else "FAIL"
            )
            record(
                f"dax_references_{name}",
                status,
                f"Home table={home_table}; unresolved={unresolved}.",
            )

        unsafe_summarization: list[str] = []
        for table in spec["tables"]:
            if table["kind"] != "fact":
                continue
            for column in table["columns"]:
                if column["data_type"] != "Double":
                    continue
                if column.get("summarize_by") != "None":
                    unsafe_summarization.append(
                        f"{table['name']}[{column['name']}]"
                    )
        record(
            "double_fact_fields_disable_implicit_sum",
            "PASS" if not unsafe_summarization else "FAIL",
            f"Unsafe fields: {unsafe_summarization}.",
        )

        source_release_to_facility = any(
            relationship["from_table"] == "Dim Source Release"
            and relationship["to_table"] == "Dim Facility"
            and relationship["active"]
            for relationship in spec["relationships"]
        )
        record(
            "no_active_release_to_facility_path",
            "PASS" if not source_release_to_facility else "FAIL",
            (
                "Facility and program facts may originate from different "
                "dataset releases; an active release-to-facility relationship "
                "would create misleading filtering."
            ),
            "High",
        )
    finally:
        connection.close()

    status_counts: dict[str, int] = {}
    for check in checks:
        status_counts[check["status"]] = (
            status_counts.get(check["status"], 0) + 1
        )
    payload = {
        "model_name": spec["model_name"],
        "model_version": spec["model_version"],
        "spec_path": spec_path.relative_to(project_root).as_posix(),
        "database_path": database_path.relative_to(project_root).as_posix(),
        "status_counts": status_counts,
        "checks": checks,
    }
    output_dir = project_root / "outputs" / "powerbi"
    output_dir.mkdir(parents=True, exist_ok=True)
    write_json(output_dir / "semantic_model_validation.json", payload)

    lines = [
        "# Power BI Semantic Model Validation",
        "",
        f"- Model: `{spec['model_name']}`",
        f"- Version: `{spec['model_version']}`",
        f"- Status counts: `{json.dumps(status_counts, sort_keys=True)}`",
        "",
        "| Check | Status | Severity | Details |",
        "|---|---|---|---|",
    ]
    for check in checks:
        lines.append(
            f"| {check['check']} | {check['status']} | "
            f"{check['severity']} | {check['details']} |"
        )
    (output_dir / "semantic_model_validation.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )
    print(json.dumps(payload["status_counts"], indent=2))
    return 0 if set(status_counts) == {"PASS"} else 1


if __name__ == "__main__":
    raise SystemExit(main())

