"""Export the validated Provider model tables for driver-free Power BI import."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sqlite3
from pathlib import Path
from typing import Any

from src.common.cms_provider import write_json


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path(__file__).resolve().parents[2],
    )
    return parser.parse_args()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def serialized_value(value: Any, data_type: str) -> Any:
    if value is None:
        return ""
    if data_type == "Boolean":
        return "true" if bool(value) else "false"
    return value


def main() -> int:
    args = parse_args()
    project_root = args.project_root.resolve()
    spec = json.loads(
        (project_root / "powerbi" / "semantic_model.json").read_text(
            encoding="utf-8"
        )
    )
    database_path = project_root / spec["source_database"]
    output_dir = project_root / "data" / "processed" / "powerbi_import"
    output_dir.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(database_path)
    exports: list[dict[str, Any]] = []
    try:
        for table in spec["tables"]:
            source_object = table["source_object"]
            columns = [column["source"] for column in table["columns"]]
            data_types = {
                column["source"]: column["data_type"]
                for column in table["columns"]
            }
            column_sql = ", ".join(f'"{column}"' for column in columns)
            rows = connection.execute(
                f'SELECT {column_sql} FROM "{source_object}"'
            )
            output_path = output_dir / f"{source_object}.csv"
            row_count = 0
            with output_path.open(
                "w", encoding="utf-8-sig", newline=""
            ) as target:
                writer = csv.writer(target, lineterminator="\n")
                writer.writerow(columns)
                for row in rows:
                    writer.writerow(
                        [
                            serialized_value(value, data_types[column])
                            for column, value in zip(columns, row, strict=True)
                        ]
                    )
                    row_count += 1
            exports.append(
                {
                    "semantic_table": table["name"],
                    "source_object": source_object,
                    "path": output_path.relative_to(project_root).as_posix(),
                    "row_count": row_count,
                    "column_count": len(columns),
                    "file_size_bytes": output_path.stat().st_size,
                    "sha256": sha256(output_path),
                }
            )
    finally:
        connection.close()

    manifest = {
        "model_name": spec["model_name"],
        "model_version": spec["model_version"],
        "source_database": spec["source_database"],
        "source_database_sha256": sha256(database_path),
        "exports": exports,
    }
    write_json(output_dir / "export_manifest.json", manifest)
    print(json.dumps({"tables": len(exports), "rows": sum(
        item["row_count"] for item in exports
    )}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
