"""Build the Provider MVP SQLite star schema and run model-level QA."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from src.common.cms_provider import sha256_file, write_json
from src.common.provider_measure_metadata import measure_dimension_rows


SUPPRESSION_MAP = {
    "": "Missing",
    "not available": "Not available",
    "not applicable": "Not applicable",
    "too few to report": "Too few to report",
    "number of cases too small": "Number of cases too small",
    "n/a": "Not available",
    "na": "Not available",
    "--": "Not available",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path(__file__).resolve().parents[2],
    )
    parser.add_argument(
        "--snapshot-date",
        default="2026-07-29",
    )
    return parser.parse_args()


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def normalized(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def safe_float(value: Any) -> float | None:
    text = normalized(value)
    if text.casefold() in SUPPRESSION_MAP:
        return None
    cleaned = text.replace(",", "").replace("%", "").replace("$", "")
    try:
        return float(cleaned)
    except ValueError:
        return None


def safe_int(value: Any) -> int | None:
    number = safe_float(value)
    if number is None:
        return None
    if not float(number).is_integer():
        return None
    return int(number)


def suppression_reason(*values: Any) -> str | None:
    for value in values:
        key = normalized(value).casefold()
        if key in SUPPRESSION_MAP:
            return SUPPRESSION_MAP[key]
    return None


def normalize_comparison(value: Any) -> str:
    text = normalized(value)
    key = re.sub(r"\s+", " ", text.casefold())
    mapping = {
        "better than the national rate": "Better than national rate",
        "no different than the national rate": (
            "No different than national rate"
        ),
        "worse than the national rate": "Worse than national rate",
        "better than expected": "Better than expected",
        "no different than expected": "No different than expected",
        "worse than expected": "Worse than expected",
        "fewer days than average per 100 discharges": (
            "Fewer days than average"
        ),
        "average days per 100 discharges": "Average days",
        "more days than average per 100 discharges": (
            "More days than average"
        ),
        "not available": "Not reportable",
        "number of cases too small": "Not reportable",
    }
    return mapping.get(key, text)


def read_source(project_root: Path, manifest_by_id: dict[str, Any], dataset_id: str) -> pd.DataFrame:
    path = project_root / manifest_by_id[dataset_id]["raw_path"]
    return pd.read_csv(
        path,
        dtype=str,
        keep_default_na=False,
        na_filter=False,
        encoding="utf-8-sig",
    )


def insert_frame(
    connection: sqlite3.Connection, table_name: str, frame: pd.DataFrame
) -> None:
    frame.to_sql(
        table_name,
        connection,
        if_exists="append",
        index=False,
        chunksize=5000,
    )


def insert_source_releases(
    connection: sqlite3.Connection, manifest: dict[str, Any]
) -> dict[str, int]:
    rows = []
    for item in manifest["datasets"]:
        rows.append(
            {
                "dataset_id": item["dataset_id"],
                "dataset_title": item["title"],
                "source_issued_date": item["source_issued_date"],
                "source_modified_date": item["source_modified_date"],
                "source_release_date": item["source_release_date"],
                "snapshot_date": item["download_date"],
                "downloaded_at_utc": item["downloaded_at_utc"],
                "file_name": item["file_name"],
                "raw_path": item["raw_path"],
                "download_url": item["download_url"],
                "sha256": item["sha256"],
                "row_count": item["row_count"],
                "column_count": item["column_count"],
                "file_size_bytes": item["file_size_bytes"],
            }
        )
    insert_frame(connection, "dim_source_release", pd.DataFrame(rows))
    return {
        row[1]: int(row[0])
        for row in connection.execute(
            "SELECT source_release_key, dataset_id FROM dim_source_release"
        )
    }


def insert_geographies(
    connection: sqlite3.Connection,
    general: pd.DataFrame,
    state_benchmark: pd.DataFrame,
) -> dict[str, int]:
    states = sorted(
        {
            normalized(value)
            for value in pd.concat(
                [general["State"], state_benchmark["State"]]
            ).unique()
            if normalized(value)
        }
    )
    rows = [
        {
            "geography_type": "state",
            "state_code": state,
            "geography_name": state,
        }
        for state in states
    ]
    insert_frame(connection, "dim_geography", pd.DataFrame(rows))
    return {
        row[1]: int(row[0])
        for row in connection.execute(
            "SELECT geography_key, state_code FROM dim_geography"
        )
    }


def insert_periods(
    connection: sqlite3.Connection,
    manifest: dict[str, Any],
    snapshot_date: str,
    *period_sources: pd.DataFrame,
) -> dict[tuple[str, str, str, int], int]:
    release_date = manifest["datasets"][0]["source_release_date"]
    rows = [
        {
            "period_role": "source_release_version",
            "measurement_start_date": "",
            "measurement_end_date": "",
            "fiscal_year": 0,
            "source_release_date": release_date,
            "snapshot_date": snapshot_date,
            "period_label": f"Catalog release {release_date}",
        }
    ]
    observed_periods: set[tuple[str, str]] = set()
    for source in period_sources:
        if "Start Date" not in source.columns or "End Date" not in source.columns:
            continue
        for start, end in zip(source["Start Date"], source["End Date"], strict=True):
            observed_periods.add(
                (
                    pd.to_datetime(start, format="%m/%d/%Y").date().isoformat(),
                    pd.to_datetime(end, format="%m/%d/%Y").date().isoformat(),
                )
            )
    for start, end in sorted(observed_periods):
        rows.append(
            {
                "period_role": "measurement",
                "measurement_start_date": start,
                "measurement_end_date": end,
                "fiscal_year": 0,
                "source_release_date": "",
                "snapshot_date": snapshot_date,
                "period_label": f"{start} to {end}",
            }
        )
    rows.extend(
        [
            {
                "period_role": "measurement_and_fiscal_year",
                "measurement_start_date": "2021-07-01",
                "measurement_end_date": "2024-06-30",
                "fiscal_year": 2026,
                "source_release_date": "",
                "snapshot_date": snapshot_date,
                "period_label": (
                    "FY 2026 HRRP; measurement 2021-07-01 to 2024-06-30"
                ),
            },
            {
                "period_role": "fiscal_year",
                "measurement_start_date": "",
                "measurement_end_date": "",
                "fiscal_year": 2026,
                "source_release_date": "",
                "snapshot_date": snapshot_date,
                "period_label": "FY 2026 HVBP",
            },
        ]
    )
    insert_frame(connection, "dim_reporting_period", pd.DataFrame(rows))
    return {
        (row[1], row[2], row[3], int(row[4])): int(row[0])
        for row in connection.execute(
            """
            SELECT
                reporting_period_key,
                period_role,
                measurement_start_date,
                measurement_end_date,
                fiscal_year
            FROM dim_reporting_period
            """
        )
    }


def insert_measures(
    connection: sqlite3.Connection,
    *period_sources: pd.DataFrame,
) -> dict[tuple[str, str], int]:
    rows = measure_dimension_rows()
    observed_periods: dict[str, tuple[str, str]] = {}
    for source in period_sources:
        if "Measure ID" not in source.columns:
            continue
        for measure_id, start, end in zip(
            source["Measure ID"],
            source["Start Date"],
            source["End Date"],
            strict=True,
        ):
            observed_periods[normalized(measure_id)] = (
                pd.to_datetime(start, format="%m/%d/%Y").date().isoformat(),
                pd.to_datetime(end, format="%m/%d/%Y").date().isoformat(),
            )
    for row in rows:
        if row["source_family"] != "unplanned_visits":
            continue
        period = observed_periods.get(str(row["measure_id"]))
        if period is not None:
            row["measurement_start_date"], row["measurement_end_date"] = period
    insert_frame(connection, "dim_measure", pd.DataFrame(rows))
    return {
        (row[1], row[2]): int(row[0])
        for row in connection.execute(
            "SELECT measure_key, source_family, measure_id FROM dim_measure"
        )
    }


def raw_and_int(
    source: pd.DataFrame, column: str, prefix: str, target: dict[str, Any]
) -> None:
    target[f"{prefix}_raw"] = source[column].map(normalized)
    target[prefix] = source[column].map(safe_int)


def insert_facilities(
    connection: sqlite3.Connection,
    general: pd.DataFrame,
    *,
    hrrp: pd.DataFrame,
    hvbp: pd.DataFrame,
    geography_map: dict[str, int],
    source_release_map: dict[str, int],
    source_release_key: int,
    snapshot_date: str,
) -> tuple[dict[str, int], int]:
    target: dict[str, Any] = {
        "facility_id": general["Facility ID"].map(normalized),
        "snapshot_date": snapshot_date,
        "source_release_key": source_release_key,
        "geography_key": general["State"].map(geography_map),
        "facility_record_source_dataset_id": "xubh-q36u",
        "is_current_general_info_match": 1,
        "facility_name": general["Facility Name"].map(normalized),
        "address_line_1": general["Address"].map(normalized),
        "city": general["City/Town"].map(normalized),
        "state_code": general["State"].map(normalized),
        "zip_code": general["ZIP Code"].map(normalized),
        "county_name": general["County/Parish"].map(normalized),
        "telephone_number": general["Telephone Number"].map(normalized),
        "hospital_type": general["Hospital Type"].map(normalized),
        "hospital_ownership": general["Hospital Ownership"].map(normalized),
        "emergency_services_raw": general["Emergency Services"].map(normalized),
        "birthing_friendly_raw": general[
            "Meets criteria for birthing friendly designation"
        ].map(normalized),
        "is_alternate_federal_id": general["Facility ID"].map(
            lambda value: int(
                bool(re.fullmatch(r"\d{5}[A-Za-z]", normalized(value)))
            )
        ),
        "overall_rating_raw": general["Hospital overall rating"].map(
            normalized
        ),
        "overall_rating_numeric": general["Hospital overall rating"].map(
            safe_float
        ),
        "overall_rating_footnote_code": general[
            "Hospital overall rating footnote"
        ].map(normalized),
    }
    raw_and_int(
        general, "MORT Group Measure Count", "mort_group_measure_count", target
    )
    raw_and_int(
        general,
        "Count of Facility MORT Measures",
        "mort_facility_measure_count",
        target,
    )
    raw_and_int(
        general, "Count of MORT Measures Better", "mort_better_count", target
    )
    raw_and_int(
        general,
        "Count of MORT Measures No Different",
        "mort_no_different_count",
        target,
    )
    raw_and_int(
        general, "Count of MORT Measures Worse", "mort_worse_count", target
    )
    target["mort_group_footnote_code"] = general[
        "MORT Group Footnote"
    ].map(normalized)

    raw_and_int(
        general,
        "Safety Group Measure Count",
        "safety_group_measure_count",
        target,
    )
    raw_and_int(
        general,
        "Count of Facility Safety Measures",
        "safety_facility_measure_count",
        target,
    )
    raw_and_int(
        general,
        "Count of Safety Measures Better",
        "safety_better_count",
        target,
    )
    raw_and_int(
        general,
        "Count of Safety Measures No Different",
        "safety_no_different_count",
        target,
    )
    raw_and_int(
        general,
        "Count of Safety Measures Worse",
        "safety_worse_count",
        target,
    )
    target["safety_group_footnote_code"] = general[
        "Safety Group Footnote"
    ].map(normalized)

    raw_and_int(
        general,
        "READM Group Measure Count",
        "readm_group_measure_count",
        target,
    )
    raw_and_int(
        general,
        "Count of Facility READM Measures",
        "readm_facility_measure_count",
        target,
    )
    raw_and_int(
        general,
        "Count of READM Measures Better",
        "readm_better_count",
        target,
    )
    raw_and_int(
        general,
        "Count of READM Measures No Different",
        "readm_no_different_count",
        target,
    )
    raw_and_int(
        general,
        "Count of READM Measures Worse",
        "readm_worse_count",
        target,
    )
    target["readm_group_footnote_code"] = general[
        "READM Group Footnote"
    ].map(normalized)

    raw_and_int(
        general,
        "Pt Exp Group Measure Count",
        "patient_experience_group_measure_count",
        target,
    )
    raw_and_int(
        general,
        "Count of Facility Pt Exp Measures",
        "patient_experience_facility_measure_count",
        target,
    )
    target["patient_experience_group_footnote_code"] = general[
        "Pt Exp Group Footnote"
    ].map(normalized)

    raw_and_int(
        general,
        "TE Group Measure Count",
        "timely_effective_group_measure_count",
        target,
    )
    raw_and_int(
        general,
        "Count of Facility TE Measures",
        "timely_effective_facility_measure_count",
        target,
    )
    target["timely_effective_group_footnote_code"] = general[
        "TE Group Footnote"
    ].map(normalized)

    insert_frame(connection, "dim_facility", pd.DataFrame(target))
    current_ids = set(general["Facility ID"].map(normalized))
    fallback_rows: list[dict[str, Any]] = []
    for dataset_id, source in [
        ("9n3s-kdb3", hrrp),
        ("ypbt-wvdk", hvbp),
    ]:
        source_unique = source.drop_duplicates(subset=["Facility ID"])
        for _, row in source_unique.iterrows():
            facility_id = normalized(row["Facility ID"])
            if facility_id in current_ids:
                continue
            fallback_rows.append(
                {
                    "facility_id": facility_id,
                    "snapshot_date": snapshot_date,
                    "source_release_key": source_release_map[dataset_id],
                    "geography_key": geography_map[
                        normalized(row.get("State", ""))
                    ],
                    "facility_record_source_dataset_id": dataset_id,
                    "is_current_general_info_match": 0,
                    "facility_name": normalized(row["Facility Name"]),
                    "address_line_1": normalized(row.get("Address", "")),
                    "city": normalized(row.get("City/Town", "")),
                    "state_code": normalized(row.get("State", "")),
                    "zip_code": normalized(row.get("ZIP Code", "")),
                    "county_name": normalized(row.get("County/Parish", "")),
                    "is_alternate_federal_id": int(
                        bool(re.fullmatch(r"\d{5}[A-Za-z]", facility_id))
                    ),
                }
            )
            current_ids.add(facility_id)
    if fallback_rows:
        insert_frame(
            connection, "dim_facility", pd.DataFrame(fallback_rows)
        )

    facility_map = {
        row[1]: int(row[0])
        for row in connection.execute(
            "SELECT facility_key, facility_id FROM dim_facility"
        )
    }
    return facility_map, len(fallback_rows)


def insert_unplanned_facts(
    connection: sqlite3.Connection,
    source: pd.DataFrame,
    *,
    facility_map: dict[str, int],
    measure_map: dict[tuple[str, str], int],
    period_map: dict[tuple[str, str, str, int], int],
    source_release_key: int,
    snapshot_date: str,
) -> None:
    target = pd.DataFrame()
    target["facility_key"] = source["Facility ID"].map(facility_map)
    target["measure_key"] = source["Measure ID"].map(
        lambda value: measure_map[("unplanned_visits", normalized(value))]
    )
    target["reporting_period_key"] = [
        period_map[
            (
                "measurement",
                pd.to_datetime(start, format="%m/%d/%Y").date().isoformat(),
                pd.to_datetime(end, format="%m/%d/%Y").date().isoformat(),
                0,
            )
        ]
        for start, end in zip(
            source["Start Date"], source["End Date"], strict=True
        )
    ]
    target["source_release_key"] = source_release_key
    target["snapshot_date"] = snapshot_date
    target["comparison_category_raw"] = source["Compared to National"].map(
        normalized
    )
    target["comparison_category"] = source["Compared to National"].map(
        normalize_comparison
    )
    for source_column, target_prefix, parser in [
        ("Denominator", "denominator", safe_float),
        ("Score", "score", safe_float),
        ("Lower Estimate", "lower_estimate", safe_float),
        ("Higher Estimate", "upper_estimate", safe_float),
        ("Number of Patients", "patient_count", safe_int),
        ("Number of Patients Returned", "patients_returned", safe_int),
    ]:
        target[f"{target_prefix}_raw"] = source[source_column].map(normalized)
        target[target_prefix if target_prefix not in {"denominator", "score", "lower_estimate", "upper_estimate"} else f"{target_prefix}_numeric"] = source[
            source_column
        ].map(parser)
    target["footnote_code_raw"] = source["Footnote"].map(normalized)
    target["suppression_reason"] = [
        suppression_reason(score, comparison)
        for score, comparison in zip(
            source["Score"], source["Compared to National"], strict=True
        )
    ]
    target["is_reportable"] = target["score_numeric"].notna().astype(int)
    target["is_suppressed"] = target["suppression_reason"].notna().astype(int)
    insert_frame(connection, "fact_provider_measure", target)


def count_columns(
    source: pd.DataFrame,
    pairs: list[tuple[str, str]],
    target: pd.DataFrame,
) -> None:
    for source_column, target_prefix in pairs:
        target[f"{target_prefix}_raw"] = source[source_column].map(normalized)
        target[target_prefix] = source[source_column].map(safe_int)


def insert_state_benchmarks(
    connection: sqlite3.Connection,
    source: pd.DataFrame,
    *,
    geography_map: dict[str, int],
    measure_map: dict[tuple[str, str], int],
    period_map: dict[tuple[str, str, str, int], int],
    source_release_key: int,
    snapshot_date: str,
) -> None:
    target = pd.DataFrame()
    target["geography_key"] = source["State"].map(geography_map)
    target["measure_key"] = source["Measure ID"].map(
        lambda value: measure_map[("unplanned_visits", normalized(value))]
    )
    target["reporting_period_key"] = [
        period_map[
            (
                "measurement",
                pd.to_datetime(start, format="%m/%d/%Y").date().isoformat(),
                pd.to_datetime(end, format="%m/%d/%Y").date().isoformat(),
                0,
            )
        ]
        for start, end in zip(
            source["Start Date"], source["End Date"], strict=True
        )
    ]
    target["source_release_key"] = source_release_key
    target["snapshot_date"] = snapshot_date
    count_columns(
        source,
        [
            ("Number of Hospitals Worse", "hospitals_worse"),
            ("Number of Hospitals Same", "hospitals_same"),
            ("Number of Hospitals Better", "hospitals_better"),
            ("Number of Hospitals Too Few", "hospitals_too_few"),
            ("Number of Hospitals Fewer", "hospitals_fewer"),
            ("Number of Hospitals Average", "hospitals_average"),
            ("Number of Hospitals More", "hospitals_more"),
            ("Number of Hospitals Too Small", "hospitals_too_small"),
        ],
        target,
    )
    target["footnote_code_raw"] = source["Footnote"].map(normalized)
    insert_frame(connection, "fact_provider_state_benchmark", target)


def insert_national_benchmarks(
    connection: sqlite3.Connection,
    source: pd.DataFrame,
    *,
    measure_map: dict[tuple[str, str], int],
    period_map: dict[tuple[str, str, str, int], int],
    source_release_key: int,
    snapshot_date: str,
) -> None:
    target = pd.DataFrame()
    target["measure_key"] = source["Measure ID"].map(
        lambda value: measure_map[("unplanned_visits", normalized(value))]
    )
    target["reporting_period_key"] = [
        period_map[
            (
                "measurement",
                pd.to_datetime(start, format="%m/%d/%Y").date().isoformat(),
                pd.to_datetime(end, format="%m/%d/%Y").date().isoformat(),
                0,
            )
        ]
        for start, end in zip(
            source["Start Date"], source["End Date"], strict=True
        )
    ]
    target["source_release_key"] = source_release_key
    target["snapshot_date"] = snapshot_date
    target["national_rate_raw"] = source["National Rate"].map(normalized)
    target["national_rate_numeric"] = source["National Rate"].map(safe_float)
    count_columns(
        source,
        [
            ("Number of Hospitals Worse", "hospitals_worse"),
            ("Number of Hospitals Same", "hospitals_same"),
            ("Number of Hospitals Better", "hospitals_better"),
            ("Number of Hospitals Too Few", "hospitals_too_few"),
            ("Number of Hospitals Fewer", "hospitals_fewer"),
            ("Number of Hospitals Average", "hospitals_average"),
            ("Number of Hospitals More", "hospitals_more"),
            ("Number of Hospitals Too Small", "hospitals_too_small"),
        ],
        target,
    )
    target["footnote_code_raw"] = source["Footnote"].map(normalized)
    insert_frame(connection, "fact_provider_national_benchmark", target)


def insert_hrrp(
    connection: sqlite3.Connection,
    source: pd.DataFrame,
    *,
    facility_map: dict[str, int],
    measure_map: dict[tuple[str, str], int],
    period_key: int,
    source_release_key: int,
    snapshot_date: str,
) -> None:
    target = pd.DataFrame()
    target["facility_key"] = source["Facility ID"].map(facility_map)
    target["measure_key"] = source["Measure Name"].map(
        lambda value: measure_map[("hrrp", normalized(value))]
    )
    target["reporting_period_key"] = period_key
    target["source_release_key"] = source_release_key
    target["snapshot_date"] = snapshot_date
    for source_column, target_prefix, parser in [
        ("Number of Discharges", "discharge_count", safe_int),
        ("Excess Readmission Ratio", "excess_readmission_ratio", safe_float),
        (
            "Predicted Readmission Rate",
            "predicted_readmission_rate",
            safe_float,
        ),
        (
            "Expected Readmission Rate",
            "expected_readmission_rate",
            safe_float,
        ),
        ("Number of Readmissions", "readmission_count", safe_int),
    ]:
        target[f"{target_prefix}_raw"] = source[source_column].map(normalized)
        target[target_prefix] = source[source_column].map(parser)
    target["footnote_code_raw"] = source["Footnote"].map(normalized)
    target["suppression_reason"] = source[
        "Excess Readmission Ratio"
    ].map(suppression_reason)
    target["is_reportable"] = target[
        "excess_readmission_ratio"
    ].notna().astype(int)
    target["is_suppressed"] = target[
        "suppression_reason"
    ].notna().astype(int)
    insert_frame(connection, "fact_provider_hrrp_measure", target)


def insert_hvbp(
    connection: sqlite3.Connection,
    source: pd.DataFrame,
    *,
    facility_map: dict[str, int],
    period_key: int,
    source_release_key: int,
    snapshot_date: str,
) -> None:
    target = pd.DataFrame()
    target["facility_key"] = source["Facility ID"].map(facility_map)
    target["reporting_period_key"] = period_key
    target["source_release_key"] = source_release_key
    target["snapshot_date"] = snapshot_date
    target["fiscal_year"] = source["Fiscal Year"].map(safe_int)
    target["program_name"] = "Hospital Value-Based Purchasing"
    mappings = [
        (
            "Unweighted Normalized Clinical Outcomes Domain Score",
            "clinical_outcomes_unweighted",
        ),
        (
            "Weighted Normalized Clinical Outcomes Domain Score",
            "clinical_outcomes_weighted",
        ),
        (
            "Unweighted Person And Community Engagement Domain Score",
            "engagement_unweighted",
        ),
        (
            "Weighted Person And Community Engagement Domain Score",
            "engagement_weighted",
        ),
        (
            "Unweighted Normalized Safety Domain Score",
            "safety_unweighted",
        ),
        ("Weighted Safety Domain Score", "safety_weighted"),
        (
            "Unweighted Normalized Efficiency And Cost Reduction Domain Score",
            "efficiency_unweighted",
        ),
        (
            "Weighted Efficiency And Cost Reduction Domain Score",
            "efficiency_weighted",
        ),
        ("Total Performance Score", "total_performance_score"),
    ]
    for source_column, target_prefix in mappings:
        target[f"{target_prefix}_raw"] = source[source_column].map(normalized)
        target[target_prefix] = source[source_column].map(safe_float)
    target["is_tps_reportable"] = target[
        "total_performance_score"
    ].notna().astype(int)
    target["suppression_reason"] = source["Total Performance Score"].map(
        suppression_reason
    )
    insert_frame(connection, "fact_provider_program_score", target)


def insert_source_checks(
    connection: sqlite3.Connection,
    project_root: Path,
    snapshot_date: str,
) -> None:
    path = (
        project_root
        / "outputs"
        / "provider_phase1"
        / snapshot_date
        / "quality_checks.csv"
    )
    frame = pd.read_csv(path, dtype=str, keep_default_na=False)
    frame.insert(2, "phase", "source_profile")
    insert_frame(connection, "fact_quality_check", frame)


def append_model_check(
    rows: list[dict[str, Any]],
    *,
    run_id: str,
    table_name: str,
    check_name: str,
    expected: Any,
    actual: Any,
    severity: str,
    details: str,
    checked_at: str,
) -> None:
    check_id = hashlib.sha1(
        f"{table_name}|{check_name}".encode("utf-8")
    ).hexdigest()[:10]
    rows.append(
        {
            "check_id": f"model_{check_id}",
            "run_id": run_id,
            "phase": "provider_model",
            "table_name": table_name,
            "check_name": check_name,
            "expected_value": str(expected),
            "actual_value": str(actual),
            "status": "PASS" if str(actual) == str(expected) else "FAIL",
            "severity": severity,
            "details": details,
            "checked_at": checked_at,
        }
    )


def scalar(connection: sqlite3.Connection, sql: str) -> Any:
    return connection.execute(sql).fetchone()[0]


def run_model_checks(
    connection: sqlite3.Connection,
    *,
    expected_rows: dict[str, int],
    expected_geographies: int,
    expected_measures: int,
    expected_periods: int,
    expected_leading_zero_facilities: int,
    expected_alternate_facilities: int,
    expected_fallback_facilities: int,
    expected_footnote_29_exceptions: int,
) -> list[dict[str, Any]]:
    checked_at = utc_now_iso()
    run_id = f"provider_model_{checked_at[:19]}"
    rows: list[dict[str, Any]] = []

    for table_name, expected in {
        "dim_source_release": 6,
        "dim_geography": expected_geographies,
        "dim_reporting_period": expected_periods,
        "dim_facility": (
            expected_rows["xubh-q36u"] + expected_fallback_facilities
        ),
        "dim_measure": expected_measures,
        "fact_provider_measure": expected_rows["632h-zaca"],
        "fact_provider_state_benchmark": expected_rows["4gkm-5ypv"],
        "fact_provider_national_benchmark": expected_rows["cvcs-xecj"],
        "fact_provider_hrrp_measure": expected_rows["9n3s-kdb3"],
        "fact_provider_program_score": expected_rows["ypbt-wvdk"],
    }.items():
        append_model_check(
            rows,
            run_id=run_id,
            table_name=table_name,
            check_name="row_count_reconciliation",
            expected=expected,
            actual=scalar(connection, f"SELECT COUNT(*) FROM {table_name}"),
            severity="Critical",
            details="Modeled row count reconciles to source or expected dimension.",
            checked_at=checked_at,
        )

    duplicate_queries = {
        "fact_provider_measure": """
            SELECT COUNT(*) FROM (
                SELECT facility_key, measure_key, source_release_key
                FROM fact_provider_measure
                GROUP BY facility_key, measure_key, source_release_key
                HAVING COUNT(*) > 1
            )
        """,
        "fact_provider_state_benchmark": """
            SELECT COUNT(*) FROM (
                SELECT geography_key, measure_key, source_release_key
                FROM fact_provider_state_benchmark
                GROUP BY geography_key, measure_key, source_release_key
                HAVING COUNT(*) > 1
            )
        """,
        "fact_provider_national_benchmark": """
            SELECT COUNT(*) FROM (
                SELECT measure_key, source_release_key
                FROM fact_provider_national_benchmark
                GROUP BY measure_key, source_release_key
                HAVING COUNT(*) > 1
            )
        """,
        "fact_provider_hrrp_measure": """
            SELECT COUNT(*) FROM (
                SELECT facility_key, measure_key, source_release_key
                FROM fact_provider_hrrp_measure
                GROUP BY facility_key, measure_key, source_release_key
                HAVING COUNT(*) > 1
            )
        """,
        "fact_provider_program_score": """
            SELECT COUNT(*) FROM (
                SELECT facility_key, fiscal_year, program_name,
                       source_release_key
                FROM fact_provider_program_score
                GROUP BY facility_key, fiscal_year, program_name,
                         source_release_key
                HAVING COUNT(*) > 1
            )
        """,
    }
    for table_name, query in duplicate_queries.items():
        append_model_check(
            rows,
            run_id=run_id,
            table_name=table_name,
            check_name="declared_grain_duplicate_groups",
            expected=0,
            actual=scalar(connection, query),
            severity="Critical",
            details="Declared fact grain includes the dataset source release.",
            checked_at=checked_at,
        )

    query_checks = [
        (
            "dim_facility",
            "facility_id_length",
            0,
            "SELECT COUNT(*) FROM dim_facility WHERE length(facility_id) <> 6",
            "Critical",
            "Every Facility ID is stored as a six-character string.",
        ),
        (
            "dim_facility",
            "leading_zero_facility_count",
            expected_leading_zero_facilities,
            "SELECT COUNT(*) FROM dim_facility WHERE facility_id LIKE '0%'",
            "Critical",
            "Leading-zero Facility IDs reconcile to the source.",
        ),
        (
            "dim_facility",
            "alternate_federal_facility_count",
            expected_alternate_facilities,
            "SELECT COUNT(*) FROM dim_facility WHERE is_alternate_federal_id = 1",
            "High",
            "VA/DoD identifiers are preserved and not mislabeled as CCNs.",
        ),
        (
            "dim_facility",
            "source_specific_fallback_facility_count",
            expected_fallback_facilities,
            """
            SELECT COUNT(*) FROM dim_facility
            WHERE is_current_general_info_match = 0
            """,
            "High",
            "Program-source facilities missing from the current General "
            "Information release are retained and explicitly flagged.",
        ),
        (
            "fact_provider_measure",
            "reportable_score_parse_failures",
            0,
            """
            SELECT COUNT(*) FROM fact_provider_measure
            WHERE is_reportable = 1 AND score_numeric IS NULL
            """,
            "Critical",
            "Reportable scores must parse; suppressed values are excluded.",
        ),
        (
            "fact_provider_measure",
            "nonreportable_zero_coercions",
            0,
            """
            SELECT COUNT(*) FROM fact_provider_measure
            WHERE is_reportable = 0 AND score_numeric = 0
            """,
            "Critical",
            "Missing and suppressed scores must never become zero.",
        ),
        (
            "fact_provider_measure",
            "unexplained_interval_order_violations",
            0,
            """
            SELECT COUNT(*) FROM fact_provider_measure
            WHERE lower_estimate_numeric IS NOT NULL
              AND score_numeric IS NOT NULL
              AND upper_estimate_numeric IS NOT NULL
              AND instr(
                  ',' || replace(footnote_code_raw, ' ', '') || ',',
                  ',29,'
              ) = 0
              AND NOT (
                lower_estimate_numeric <= score_numeric
                AND score_numeric <= upper_estimate_numeric
              )
            """,
            "High",
            "Applicable lower/score/upper intervals are ordered after "
            "separating CMS Footnote 29 partial-period exceptions.",
        ),
        (
            "fact_provider_measure",
            "footnote_29_interval_exceptions",
            expected_footnote_29_exceptions,
            """
            SELECT COUNT(*) FROM fact_provider_measure
            WHERE lower_estimate_numeric IS NOT NULL
              AND score_numeric IS NOT NULL
              AND upper_estimate_numeric IS NOT NULL
              AND instr(
                  ',' || replace(footnote_code_raw, ' ', '') || ',',
                  ',29,'
              ) > 0
              AND NOT (
                lower_estimate_numeric <= score_numeric
                AND score_numeric <= upper_estimate_numeric
              )
            """,
            "Medium",
            "Known release-specific Footnote 29 interval exceptions are "
            "surfaced as documented exceptions rather than treated as "
            "ordinary intervals.",
        ),
        (
            "fact_provider_hrrp_measure",
            "reportable_ratio_parse_failures",
            0,
            """
            SELECT COUNT(*) FROM fact_provider_hrrp_measure
            WHERE is_reportable = 1
              AND excess_readmission_ratio IS NULL
            """,
            "Critical",
            "Reportable official HRRP ratios must parse.",
        ),
        (
            "fact_provider_program_score",
            "reportable_tps_parse_failures",
            0,
            """
            SELECT COUNT(*) FROM fact_provider_program_score
            WHERE is_tps_reportable = 1
              AND total_performance_score IS NULL
            """,
            "Critical",
            "Reportable official TPS values must parse.",
        ),
        (
            "fact_provider_program_score",
            "unexpected_fiscal_year_rows",
            0,
            """
            SELECT COUNT(*) FROM fact_provider_program_score
            WHERE fiscal_year <> 2026
            """,
            "High",
            "This snapshot is the FY 2026 HVBP file.",
        ),
        (
            "dim_measure",
            "incomplete_semantic_metadata",
            0,
            """
            SELECT COUNT(*) FROM dim_measure
            WHERE unit = ''
               OR direction = ''
               OR suppression_rule = ''
               OR business_interpretation = ''
               OR interpretation_limit = ''
               OR official_or_project_defined = ''
            """,
            "Critical",
            "Every measure requires unit, direction, period semantics, "
            "suppression, and interpretation limits.",
        ),
        (
            "vw_provider_measure_reporting",
            "view_row_reconciliation",
            expected_rows["632h-zaca"],
            "SELECT COUNT(*) FROM vw_provider_measure_reporting",
            "Critical",
            "Reporting view preserves one row per Provider measure fact.",
        ),
        (
            "vw_provider_benchmark_join_coverage",
            "missing_national_benchmark_rows",
            0,
            """
            SELECT provider_measure_rows - national_benchmark_matched_rows
            FROM vw_provider_benchmark_join_coverage
            """,
            "High",
            "Every Provider measure row matches an official national context row.",
        ),
        (
            "vw_provider_benchmark_join_coverage",
            "missing_state_benchmark_rows",
            0,
            """
            SELECT provider_measure_rows - state_benchmark_matched_rows
            FROM vw_provider_benchmark_join_coverage
            """,
            "High",
            "Every Provider measure row matches official state category context.",
        ),
        (
            "fact_quality_check",
            "source_profile_nonpass_checks",
            0,
            """
            SELECT COUNT(*) FROM fact_quality_check
            WHERE phase = 'source_profile' AND status <> 'PASS'
            """,
            "Critical",
            "Provider model is gated on a clean accepted source profile.",
        ),
    ]
    for table, name, expected, query, severity, details in query_checks:
        append_model_check(
            rows,
            run_id=run_id,
            table_name=table,
            check_name=name,
            expected=expected,
            actual=scalar(connection, query),
            severity=severity,
            details=details,
            checked_at=checked_at,
        )

    foreign_key_rows = connection.execute(
        "PRAGMA foreign_key_check"
    ).fetchall()
    append_model_check(
        rows,
        run_id=run_id,
        table_name="database",
        check_name="foreign_key_violations",
        expected=0,
        actual=len(foreign_key_rows),
        severity="Critical",
        details="SQLite foreign-key check across all modeled facts and dimensions.",
        checked_at=checked_at,
    )
    integrity_result = scalar(connection, "PRAGMA integrity_check")
    append_model_check(
        rows,
        run_id=run_id,
        table_name="database",
        check_name="sqlite_integrity_check",
        expected="ok",
        actual=integrity_result,
        severity="Critical",
        details="SQLite database structural integrity check.",
        checked_at=checked_at,
    )
    return rows


def write_model_outputs(
    output_dir: Path,
    *,
    database_path: Path,
    model_checks: list[dict[str, Any]],
    row_counts: list[tuple[str, int]],
    interval_exceptions: pd.DataFrame,
    created_at: str,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    check_path = output_dir / "model_quality_checks.csv"
    fields = [
        "check_id",
        "run_id",
        "phase",
        "table_name",
        "check_name",
        "expected_value",
        "actual_value",
        "status",
        "severity",
        "details",
        "checked_at",
    ]
    with check_path.open("w", encoding="utf-8-sig", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=fields)
        writer.writeheader()
        writer.writerows(model_checks)

    with (output_dir / "table_row_counts.csv").open(
        "w", encoding="utf-8-sig", newline=""
    ) as output:
        writer = csv.writer(output)
        writer.writerow(["table_name", "row_count"])
        writer.writerows(row_counts)
    interval_exceptions.to_csv(
        output_dir / "interval_order_exceptions.csv",
        index=False,
        encoding="utf-8-sig",
    )

    statuses: dict[str, int] = {}
    for row in model_checks:
        statuses[row["status"]] = statuses.get(row["status"], 0) + 1
    manifest = {
        "created_at": created_at,
        "database_path": database_path.as_posix(),
        "database_size_bytes": database_path.stat().st_size,
        "database_sha256": sha256_file(database_path),
        "model_check_status_counts": statuses,
        "table_row_counts": dict(row_counts),
    }
    write_json(output_dir / "model_manifest.json", manifest)

    lines = [
        "# Provider Model QA Report",
        "",
        f"- Created at: `{created_at}`",
        f"- Database: `{database_path.as_posix()}`",
        f"- Database SHA-256: `{manifest['database_sha256']}`",
        f"- Model QA: `{json.dumps(statuses, sort_keys=True)}`",
        "",
        "The model contains public, aggregate CMS Provider results. It does "
        "not contain patient-level claims or EHR records and does not "
        "recalculate formal HEDIS measures.",
        "",
        "## Table row counts",
        "",
        "| Table | Rows |",
        "|---|---:|",
    ]
    for table, count in row_counts:
        lines.append(f"| `{table}` | {count:,} |")
    lines.extend(
        [
            "",
            "## Non-pass checks",
            "",
            "| Table | Check | Status | Severity | Actual | Details |",
            "|---|---|---|---|---|---|",
        ]
    )
    nonpass = [row for row in model_checks if row["status"] != "PASS"]
    if not nonpass:
        lines.append("| - | - | - | - | - | No non-pass model checks. |")
    else:
        for row in nonpass:
            lines.append(
                f"| `{row['table_name']}` | {row['check_name']} | "
                f"{row['status']} | {row['severity']} | "
                f"{row['actual_value']} | {row['details']} |"
            )
    (output_dir / "model_qa_report.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )


def main() -> int:
    args = parse_args()
    project_root = args.project_root.resolve()
    snapshot_date = args.snapshot_date
    manifest_path = (
        project_root
        / "data"
        / "raw"
        / "provider"
        / snapshot_date
        / "provider_snapshot_manifest.json"
    )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest_by_id = {
        item["dataset_id"]: item for item in manifest["datasets"]
    }

    general = read_source(project_root, manifest_by_id, "xubh-q36u")
    unplanned = read_source(project_root, manifest_by_id, "632h-zaca")
    state_benchmark = read_source(project_root, manifest_by_id, "4gkm-5ypv")
    national_benchmark = read_source(
        project_root, manifest_by_id, "cvcs-xecj"
    )
    hrrp = read_source(project_root, manifest_by_id, "9n3s-kdb3")
    hvbp = read_source(project_root, manifest_by_id, "ypbt-wvdk")

    processed_dir = project_root / "data" / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)
    database_path = processed_dir / "provider_quality.sqlite"
    temporary_path = processed_dir / "provider_quality.sqlite.part"
    if temporary_path.exists():
        temporary_path.unlink()

    connection = sqlite3.connect(temporary_path)
    try:
        connection.execute("PRAGMA foreign_keys = ON")
        ddl = (
            project_root / "sql" / "ddl" / "001_provider_schema.sql"
        ).read_text(encoding="utf-8")
        connection.executescript(ddl)

        source_release_map = insert_source_releases(connection, manifest)
        geography_map = insert_geographies(
            connection, general, state_benchmark
        )
        period_map = insert_periods(
            connection,
            manifest,
            snapshot_date,
            unplanned,
            state_benchmark,
            national_benchmark,
        )
        measure_map = insert_measures(connection, unplanned)
        facility_map, fallback_facility_count = insert_facilities(
            connection,
            general,
            hrrp=hrrp,
            hvbp=hvbp,
            geography_map=geography_map,
            source_release_map=source_release_map,
            source_release_key=source_release_map["xubh-q36u"],
            snapshot_date=snapshot_date,
        )
        insert_unplanned_facts(
            connection,
            unplanned,
            facility_map=facility_map,
            measure_map=measure_map,
            period_map=period_map,
            source_release_key=source_release_map["632h-zaca"],
            snapshot_date=snapshot_date,
        )
        insert_state_benchmarks(
            connection,
            state_benchmark,
            geography_map=geography_map,
            measure_map=measure_map,
            period_map=period_map,
            source_release_key=source_release_map["4gkm-5ypv"],
            snapshot_date=snapshot_date,
        )
        insert_national_benchmarks(
            connection,
            national_benchmark,
            measure_map=measure_map,
            period_map=period_map,
            source_release_key=source_release_map["cvcs-xecj"],
            snapshot_date=snapshot_date,
        )
        insert_hrrp(
            connection,
            hrrp,
            facility_map=facility_map,
            measure_map=measure_map,
            period_key=period_map[
                (
                    "measurement_and_fiscal_year",
                    "2021-07-01",
                    "2024-06-30",
                    2026,
                )
            ],
            source_release_key=source_release_map["9n3s-kdb3"],
            snapshot_date=snapshot_date,
        )
        insert_hvbp(
            connection,
            hvbp,
            facility_map=facility_map,
            period_key=period_map[("fiscal_year", "", "", 2026)],
            source_release_key=source_release_map["ypbt-wvdk"],
            snapshot_date=snapshot_date,
        )
        insert_source_checks(connection, project_root, snapshot_date)
        views = (
            project_root
            / "sql"
            / "views"
            / "001_provider_reporting_views.sql"
        ).read_text(encoding="utf-8")
        connection.executescript(views)

        expected_rows = {
            dataset_id: int(item["row_count"])
            for dataset_id, item in manifest_by_id.items()
        }
        model_checks = run_model_checks(
            connection,
            expected_rows=expected_rows,
            expected_geographies=len(geography_map),
            expected_measures=len(measure_dimension_rows()),
            expected_periods=len(period_map),
            expected_leading_zero_facilities=sum(
                facility_id.startswith("0") for facility_id in facility_map
            ),
            expected_alternate_facilities=sum(
                bool(re.fullmatch(r"\d{5}[A-Za-z]", facility_id))
                for facility_id in facility_map
            ),
            expected_fallback_facilities=fallback_facility_count,
            expected_footnote_29_exceptions=(
                2 if manifest["datasets"][0]["source_release_date"] == "2026-05-13" else 0
            ),
        )
        insert_frame(
            connection, "fact_quality_check", pd.DataFrame(model_checks)
        )
        connection.commit()

        table_names = [
            row[0]
            for row in connection.execute(
                """
                SELECT name
                FROM sqlite_master
                WHERE type = 'table' AND name NOT LIKE 'sqlite_%'
                ORDER BY name
                """
            )
        ]
        row_counts = [
            (table, int(scalar(connection, f"SELECT COUNT(*) FROM {table}")))
            for table in table_names
        ]
        interval_exceptions = pd.read_sql_query(
            """
            SELECT
                f.facility_id,
                f.facility_name,
                m.measure_id,
                m.measure_name,
                x.score_raw,
                x.lower_estimate_raw,
                x.upper_estimate_raw,
                x.comparison_category_raw,
                x.footnote_code_raw,
                m.measurement_start_date,
                m.measurement_end_date,
                x.snapshot_date
            FROM fact_provider_measure AS x
            JOIN dim_facility AS f
              ON f.facility_key = x.facility_key
            JOIN dim_measure AS m
              ON m.measure_key = x.measure_key
            WHERE x.lower_estimate_numeric IS NOT NULL
              AND x.score_numeric IS NOT NULL
              AND x.upper_estimate_numeric IS NOT NULL
              AND instr(
                  ',' || replace(x.footnote_code_raw, ' ', '') || ',',
                  ',29,'
              ) > 0
              AND NOT (
                x.lower_estimate_numeric <= x.score_numeric
                AND x.score_numeric <= x.upper_estimate_numeric
              )
            ORDER BY f.facility_id, m.measure_id
            """,
            connection,
        )
    finally:
        connection.close()

    os.replace(temporary_path, database_path)
    created_at = utc_now_iso()
    output_dir = (
        project_root / "outputs" / "provider_model" / snapshot_date
    )
    write_model_outputs(
        output_dir,
        database_path=database_path.relative_to(project_root),
        model_checks=model_checks,
        row_counts=row_counts,
        interval_exceptions=interval_exceptions,
        created_at=created_at,
    )
    statuses: dict[str, int] = {}
    for row in model_checks:
        statuses[row["status"]] = statuses.get(row["status"], 0) + 1
    print(
        json.dumps(
            {
                "database": str(database_path),
                "table_row_counts": dict(row_counts),
                "model_qa_status_counts": statuses,
                "output_dir": str(output_dir),
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0 if set(statuses) == {"PASS"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
