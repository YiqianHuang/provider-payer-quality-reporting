"""Download immutable CMS Provider MVP snapshots and build a manifest."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import date
from pathlib import Path
from typing import Any

from src.common.cms_provider import (
    HOSPITAL_DICTIONARY_URL,
    PROVIDER_DATASETS,
    csv_shape,
    download_immutable,
    fetch_dataset_metadata,
    sha256_file,
    utc_now_iso,
    write_json,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path(__file__).resolve().parents[2],
    )
    parser.add_argument(
        "--snapshot-date",
        default=date.today().isoformat(),
        help="Local download date in YYYY-MM-DD format.",
    )
    parser.add_argument(
        "--reuse-existing",
        action="store_true",
        help=(
            "Reuse an existing raw file only after validating its hash and "
            "shape. The file is never overwritten."
        ),
    )
    return parser.parse_args()


def select_csv(metadata: dict[str, Any]) -> dict[str, Any]:
    return metadata["_selected_distribution"]


def write_csv_manifest(path: Path, rows: list[dict[str, Any]]) -> None:
    fields = [
        "dataset_id",
        "title",
        "role",
        "landing_page",
        "download_url",
        "download_date",
        "downloaded_at_utc",
        "source_issued_date",
        "source_modified_date",
        "source_release_date",
        "raw_path",
        "file_name",
        "file_size_bytes",
        "sha256",
        "row_count",
        "column_count",
        "candidate_key",
        "measurement_period",
        "dictionary_url",
    ]
    with path.open("w", encoding="utf-8-sig", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    args = parse_args()
    project_root = args.project_root.resolve()
    snapshot_root = (
        project_root / "data" / "raw" / "provider" / args.snapshot_date
    )
    snapshot_root.mkdir(parents=True, exist_ok=True)
    downloaded_at_utc = utc_now_iso()
    manifest_rows: list[dict[str, Any]] = []

    for dataset_id, config in PROVIDER_DATASETS.items():
        metadata = fetch_dataset_metadata(dataset_id)
        expected_title = config["expected_title"]
        if metadata.get("title") != expected_title:
            raise ValueError(
                f"CMS title drift for {dataset_id}: expected "
                f"{expected_title!r}, received {metadata.get('title')!r}"
            )

        distribution = select_csv(metadata)
        file_name = Path(distribution["downloadURL"]).name
        dataset_dir = snapshot_root / dataset_id
        raw_path = dataset_dir / file_name
        metadata_path = dataset_dir / "catalog_metadata.json"

        if raw_path.exists():
            if not args.reuse_existing:
                raise FileExistsError(
                    f"Snapshot already exists; refusing overwrite: {raw_path}"
                )
        else:
            download_immutable(distribution["downloadURL"], raw_path)

        clean_metadata = {
            key: value
            for key, value in metadata.items()
            if key != "_selected_distribution"
        }
        if metadata_path.exists() and not args.reuse_existing:
            raise FileExistsError(
                f"Metadata snapshot already exists: {metadata_path}"
            )
        if not metadata_path.exists():
            write_json(metadata_path, clean_metadata)

        row_count, column_count, header = csv_shape(raw_path)
        candidate_key = " OR ".join(
            " + ".join(key)
            for key in config.get("candidate_key_aliases", [])
        )
        manifest_rows.append(
            {
                "dataset_id": dataset_id,
                "title": metadata["title"],
                "role": config["role"],
                "landing_page": metadata["landingPage"],
                "download_url": distribution["downloadURL"],
                "download_date": args.snapshot_date,
                "downloaded_at_utc": downloaded_at_utc,
                "source_issued_date": metadata.get("issued", ""),
                "source_modified_date": metadata.get("modified", ""),
                "source_release_date": metadata.get("released", ""),
                "raw_path": raw_path.relative_to(project_root).as_posix(),
                "file_name": file_name,
                "file_size_bytes": raw_path.stat().st_size,
                "sha256": sha256_file(raw_path),
                "row_count": row_count,
                "column_count": column_count,
                "candidate_key": candidate_key,
                "measurement_period": "Profile from source date columns",
                "dictionary_url": distribution.get(
                    "describedBy", HOSPITAL_DICTIONARY_URL
                ),
                "columns": header,
            }
        )

    dictionary_dir = project_root / "data" / "reference"
    dictionary_path = (
        dictionary_dir / "HOSPITAL_Data_Dictionary_April_2026.pdf"
    )
    if dictionary_path.exists():
        if not args.reuse_existing:
            raise FileExistsError(
                f"Reference already exists; refusing overwrite: "
                f"{dictionary_path}"
            )
    else:
        download_immutable(HOSPITAL_DICTIONARY_URL, dictionary_path)

    reference_manifest = {
        "title": "Hospital Downloadable Database Data Dictionary",
        "url": HOSPITAL_DICTIONARY_URL,
        "local_path": dictionary_path.relative_to(project_root).as_posix(),
        "download_date": args.snapshot_date,
        "downloaded_at_utc": downloaded_at_utc,
        "file_size_bytes": dictionary_path.stat().st_size,
        "sha256": sha256_file(dictionary_path),
        "document_release": "April 2026",
    }

    json_manifest_path = snapshot_root / "provider_snapshot_manifest.json"
    csv_manifest_path = snapshot_root / "provider_snapshot_manifest.csv"
    if (
        (json_manifest_path.exists() or csv_manifest_path.exists())
        and not args.reuse_existing
    ):
        raise FileExistsError("Provider snapshot manifest already exists")

    json_payload = {
        "manifest_version": 1,
        "snapshot_date": args.snapshot_date,
        "downloaded_at_utc": downloaded_at_utc,
        "datasets": manifest_rows,
        "references": [reference_manifest],
    }
    write_json(json_manifest_path, json_payload)
    write_csv_manifest(
        csv_manifest_path,
        [
            {key: value for key, value in row.items() if key != "columns"}
            for row in manifest_rows
        ],
    )
    write_json(dictionary_dir / "reference_manifest.json", reference_manifest)

    print(
        json.dumps(
            {
                "snapshot_root": str(snapshot_root),
                "dataset_count": len(manifest_rows),
                "total_rows": sum(row["row_count"] for row in manifest_rows),
                "total_bytes": sum(
                    row["file_size_bytes"] for row in manifest_rows
                ),
                "manifest": str(json_manifest_path),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

