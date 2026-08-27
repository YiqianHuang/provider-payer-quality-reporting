"""Record a non-destructive CMS Provider source-freshness check."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import date
from pathlib import Path
from typing import Any

from src.common.cms_provider import (
    PROVIDER_DATASETS,
    fetch_dataset_metadata,
    sha256_file,
    utc_now_iso,
    write_json,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--as-of-date", default=date.today().isoformat())
    parser.add_argument("--snapshot-date", default="2026-07-29")
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Optional output directory for this audit record.",
    )
    return parser.parse_args()


def load_manifest(project_root: Path, snapshot_date: str) -> dict[str, dict[str, Any]]:
    path = project_root / "data" / "raw" / "provider" / snapshot_date / "provider_snapshot_manifest.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    return {row["dataset_id"]: row for row in payload["datasets"]}


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fields = [
        "dataset_id", "title", "status", "current_released", "snapshot_released",
        "current_modified", "snapshot_modified", "current_csv_url", "snapshot_csv_url",
        "release_changed", "modified_changed", "csv_url_changed", "local_file_exists",
        "local_hash_matches", "local_row_count", "local_column_count", "api_url", "checked_at_utc",
    ]
    with path.open("w", encoding="utf-8-sig", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    args = parse_args()
    project_root = args.project_root.resolve()
    snapshot_rows = load_manifest(project_root, args.snapshot_date)
    checked_at_utc = utc_now_iso()
    rows: list[dict[str, Any]] = []

    for dataset_id in PROVIDER_DATASETS:
        snapshot = snapshot_rows[dataset_id]
        api_url = "https://data.cms.gov/provider-data/api/1/metastore/schemas/dataset/items/" + dataset_id
        metadata = fetch_dataset_metadata(dataset_id)
        current_csv_url = metadata["_selected_distribution"]["downloadURL"]
        raw_path = project_root / snapshot["raw_path"]
        local_exists = raw_path.is_file()
        local_hash_matches = local_exists and sha256_file(raw_path) == snapshot["sha256"]
        release_changed = metadata.get("released", "") != snapshot["source_release_date"]
        modified_changed = metadata.get("modified", "") != snapshot["source_modified_date"]
        csv_url_changed = current_csv_url != snapshot["download_url"]
        changed = any([release_changed, modified_changed, csv_url_changed, not local_exists, not local_hash_matches])
        rows.append({
            "dataset_id": dataset_id,
            "title": metadata.get("title", ""),
            "status": "CHANGED" if changed else "UNCHANGED",
            "current_released": metadata.get("released", ""),
            "snapshot_released": snapshot["source_release_date"],
            "current_modified": metadata.get("modified", ""),
            "snapshot_modified": snapshot["source_modified_date"],
            "current_csv_url": current_csv_url,
            "snapshot_csv_url": snapshot["download_url"],
            "release_changed": release_changed,
            "modified_changed": modified_changed,
            "csv_url_changed": csv_url_changed,
            "local_file_exists": local_exists,
            "local_hash_matches": local_hash_matches,
            "local_row_count": snapshot["row_count"],
            "local_column_count": snapshot["column_count"],
            "api_url": api_url,
            "checked_at_utc": checked_at_utc,
        })

    status_counts: dict[str, int] = {}
    for row in rows:
        status_counts[row["status"]] = status_counts.get(row["status"], 0) + 1
    overall_status = "PASS" if status_counts == {"UNCHANGED": 6} else "REVIEW"
    output_dir = args.output_dir or (
        project_root / "outputs" / "provider_freshness" / args.as_of_date
    )
    if not output_dir.is_absolute():
        output_dir = project_root / output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "audit_type": "cms_provider_freshness",
        "as_of_date": args.as_of_date,
        "checked_at_utc": checked_at_utc,
        "snapshot_date": args.snapshot_date,
        "snapshot_manifest": "data/raw/provider/%s/provider_snapshot_manifest.json" % args.snapshot_date,
        "metadata_api_template": "https://data.cms.gov/provider-data/api/1/metastore/schemas/dataset/items/<dataset-id>",
        "status": overall_status,
        "status_counts": status_counts,
        "datasets": rows,
    }
    write_json(output_dir / "freshness_check.json", payload)
    write_csv(output_dir / "freshness_check.csv", rows)
    lines = [
        "# CMS Provider Source Freshness Check", "",
        "- As of date: **%s**" % args.as_of_date,
        "- Checked at UTC: `%s`" % checked_at_utc,
        "- Compared snapshot: `%s`" % args.snapshot_date,
        "- Overall status: **%s**" % overall_status,
        "- Status counts: `%s`" % json.dumps(status_counts, sort_keys=True), "",
        "The check reads current CMS catalog metadata and compares release date, modified date, selected CSV URL, local file existence, and local snapshot SHA-256. It does not overwrite or redownload the immutable snapshot.", "",
        "| Dataset | Status | Current release | Snapshot release | Current modified | Snapshot modified | URL changed | Local hash |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for row in rows:
        lines.append("| `%s` | %s | %s | %s | %s | %s | %s | %s |" % (
            row["dataset_id"], row["status"], row["current_released"], row["snapshot_released"],
            row["current_modified"], row["snapshot_modified"], row["csv_url_changed"], row["local_hash_matches"],
        ))
    lines.extend([
        "", "## Decision", "",
        ("No new raw snapshot is required by this audit. Continue using the immutable `%s` snapshot and existing profiling/model QA outputs. A `CHANGED` row would require a new date-partitioned snapshot and a full rerun before downstream use." % args.snapshot_date if overall_status == "PASS" else "At least one source differs from the accepted snapshot. Create a new date-partitioned snapshot and rerun profiling/model QA before downstream use."),
        "", "## Evidence", "", "- `freshness_check.json`", "- `freshness_check.csv`",
    ])
    (output_dir / "freshness_check.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"status": overall_status, "status_counts": status_counts}, indent=2))
    return 0 if overall_status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
