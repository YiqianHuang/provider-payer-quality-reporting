"""Utilities for traceable CMS Provider Data Catalog snapshots."""

from __future__ import annotations

import csv
import hashlib
import json
import os
import shutil
import tempfile
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


CMS_METADATA_BASE = (
    "https://data.cms.gov/provider-data/api/1/"
    "metastore/schemas/dataset/items"
)

HOSPITAL_DICTIONARY_URL = (
    "https://data.cms.gov/provider-data/sites/default/files/"
    "data_dictionaries/hospital/HOSPITAL_Data_Dictionary.pdf"
)

PROVIDER_DATASETS: dict[str, dict[str, Any]] = {
    "xubh-q36u": {
        "expected_title": "Hospital General Information",
        "role": "facility_dimension_source",
        "period_role": "source_release_version",
        "footnote_expected": True,
        "candidate_key_aliases": [
            ["Facility ID"],
        ],
    },
    "632h-zaca": {
        "expected_title": "Unplanned Hospital Visits - Hospital",
        "role": "facility_measure_fact_source",
        "period_role": "measurement_dates",
        "footnote_expected": True,
        "candidate_key_aliases": [
            [
                "Facility ID",
                "Measure ID",
                "Measure Start Date|Start Date",
                "Measure End Date|End Date",
            ],
        ],
    },
    "4gkm-5ypv": {
        "expected_title": "Unplanned Hospital Visits - State",
        "role": "state_measure_benchmark_source",
        "period_role": "measurement_dates",
        "footnote_expected": True,
        "candidate_key_aliases": [
            [
                "State",
                "Measure ID",
                "Measure Start Date|Start Date",
                "Measure End Date|End Date",
            ],
        ],
    },
    "cvcs-xecj": {
        "expected_title": "Unplanned Hospital Visits - National",
        "role": "national_measure_benchmark_source",
        "period_role": "measurement_dates",
        "footnote_expected": True,
        "candidate_key_aliases": [
            [
                "Measure ID",
                "Measure Start Date|Start Date",
                "Measure End Date|End Date",
            ],
        ],
    },
    "9n3s-kdb3": {
        "expected_title": "Hospital Readmissions Reduction Program",
        "role": "hrrp_facility_measure_fact_source",
        "period_role": "measurement_dates_and_fiscal_year",
        "footnote_expected": True,
        "candidate_key_aliases": [
            [
                "Facility ID",
                "Measure Name|Measure ID",
                "Start Date|Measure Start Date",
                "End Date|Measure End Date",
            ],
        ],
    },
    "ypbt-wvdk": {
        "expected_title": (
            "Hospital Value-Based Purchasing (HVBP) - "
            "Total Performance Score"
        ),
        "role": "hvbp_facility_program_score_source",
        "period_role": "fiscal_year",
        "footnote_expected": False,
        "candidate_key_aliases": [
            ["Facility ID", "Fiscal Year"],
        ],
    },
}


def utc_now_iso() -> str:
    """Return a second-precision UTC timestamp."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def fetch_json(url: str) -> dict[str, Any]:
    """Fetch JSON from a public URL without authentication."""
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "provider-payer-quality-reporting/0.1"},
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.load(response)


def fetch_dataset_metadata(dataset_id: str) -> dict[str, Any]:
    """Fetch and minimally validate CMS catalog metadata."""
    metadata = fetch_json(f"{CMS_METADATA_BASE}/{dataset_id}")
    if metadata.get("identifier") != dataset_id:
        raise ValueError(
            f"CMS metadata identifier mismatch for {dataset_id}: "
            f"{metadata.get('identifier')!r}"
        )
    if metadata.get("accessLevel") != "public":
        raise ValueError(f"Dataset {dataset_id} is not marked public")
    distributions = metadata.get("distribution") or []
    csv_distributions = [
        item
        for item in distributions
        if item.get("mediaType") == "text/csv" and item.get("downloadURL")
    ]
    if not csv_distributions:
        raise ValueError(f"Dataset {dataset_id} has no CSV distribution")
    metadata["_selected_distribution"] = csv_distributions[0]
    return metadata


def download_immutable(url: str, destination: Path) -> None:
    """Download to a temporary file, then atomically create destination."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        raise FileExistsError(
            f"Immutable raw target already exists: {destination}"
        )

    request = urllib.request.Request(
        url,
        headers={"User-Agent": "provider-payer-quality-reporting/0.1"},
    )
    file_descriptor, temporary_name = tempfile.mkstemp(
        prefix=f"{destination.name}.",
        suffix=".part",
        dir=destination.parent,
    )
    os.close(file_descriptor)
    temporary_path = Path(temporary_name)
    try:
        with urllib.request.urlopen(request, timeout=180) as response:
            with temporary_path.open("wb") as output:
                shutil.copyfileobj(response, output)
        temporary_path.replace(destination)
    finally:
        if temporary_path.exists():
            temporary_path.unlink()


def sha256_file(path: Path) -> str:
    """Calculate the SHA-256 digest of a file."""
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def csv_shape(path: Path) -> tuple[int, int, list[str]]:
    """Return data-row count, column count, and header for a CSV file."""
    with path.open("r", encoding="utf-8-sig", newline="") as source:
        reader = csv.reader(source)
        try:
            header = next(reader)
        except StopIteration as exc:
            raise ValueError(f"CSV is empty: {path}") from exc
        row_count = sum(1 for _ in reader)
    return row_count, len(header), header


def write_json(path: Path, payload: Any) -> None:
    """Write deterministic UTF-8 JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as output:
        json.dump(payload, output, indent=2, ensure_ascii=False, sort_keys=True)
        output.write("\n")
