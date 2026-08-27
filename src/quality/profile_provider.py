"""Profile CMS Provider MVP snapshots and emit auditable QA evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import pandas as pd

from src.common.cms_provider import PROVIDER_DATASETS, sha256_file, write_json


SUPPRESSION_TOKENS = {
    "not available",
    "not applicable",
    "too few to report",
    "number of cases too small",
    "n/a",
    "na",
    "--",
}

DATE_NAME_PATTERN = re.compile(r"(start|end|measurement|release).*date", re.I)
NUMERIC_NAME_PATTERN = re.compile(
    r"(score|rate|ratio|estimate|rating|discharge|readmission|payment)",
    re.I,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path(__file__).resolve().parents[2],
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        help="Provider snapshot manifest. Defaults to the latest snapshot.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Output directory. Defaults to outputs/provider_phase1/<date>.",
    )
    return parser.parse_args()


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def latest_manifest(project_root: Path) -> Path:
    manifests = sorted(
        (project_root / "data" / "raw" / "provider").glob(
            "*/provider_snapshot_manifest.json"
        )
    )
    if not manifests:
        raise FileNotFoundError("No provider snapshot manifest found")
    return manifests[-1]


def normalized_text(series: pd.Series) -> pd.Series:
    return series.astype("string").fillna("").str.strip()


def suppression_mask(series: pd.Series) -> pd.Series:
    normalized = normalized_text(series).str.casefold()
    return normalized.isin(SUPPRESSION_TOKENS)


def numeric_parse(series: pd.Series) -> pd.Series:
    cleaned = (
        normalized_text(series)
        .str.replace(",", "", regex=False)
        .str.replace("%", "", regex=False)
        .str.replace("$", "", regex=False)
    )
    return pd.to_numeric(cleaned, errors="coerce")


def resolve_alias(component: str, columns: Iterable[str]) -> str | None:
    by_casefold = {column.casefold(): column for column in columns}
    for alias in component.split("|"):
        match = by_casefold.get(alias.casefold())
        if match is not None:
            return match
    return None


def resolve_candidate_key(
    dataset_id: str, columns: list[str]
) -> tuple[list[str], list[str]]:
    configs = PROVIDER_DATASETS[dataset_id].get("candidate_key_aliases", [])
    for candidate in configs:
        resolved: list[str] = []
        missing: list[str] = []
        for component in candidate:
            actual = resolve_alias(component, columns)
            if actual is None:
                missing.append(component)
            else:
                resolved.append(actual)
        if not missing:
            return resolved, []
    expected = configs[0] if configs else []
    return [], [
        component
        for component in expected
        if resolve_alias(component, columns) is None
    ]


def append_check(
    checks: list[dict[str, Any]],
    *,
    run_id: str,
    dataset_id: str,
    check_name: str,
    expected: Any,
    actual: Any,
    status: str,
    severity: str,
    details: str,
    checked_at: str,
) -> None:
    stable = hashlib.sha1(
        f"{dataset_id}|{check_name}".encode("utf-8")
    ).hexdigest()[:10]
    checks.append(
        {
            "check_id": f"provider_{stable}",
            "run_id": run_id,
            "table_name": dataset_id,
            "check_name": check_name,
            "expected_value": expected,
            "actual_value": actual,
            "status": status,
            "severity": severity,
            "details": details,
            "checked_at": checked_at,
        }
    )


def profile_column(
    dataset_id: str, column: str, series: pd.Series
) -> dict[str, Any]:
    text = normalized_text(series)
    blank_mask = text.eq("")
    suppressed = suppression_mask(series)
    reportable = ~(blank_mask | suppressed)
    reportable_count = int(reportable.sum())
    numeric = numeric_parse(series)
    numeric_success = int((numeric.notna() & reportable).sum())
    numeric_rate = (
        numeric_success / reportable_count if reportable_count else None
    )
    if DATE_NAME_PATTERN.search(column):
        parsed_dates = pd.to_datetime(
            text.where(reportable), format="%m/%d/%Y", errors="coerce"
        )
        date_success = int((parsed_dates.notna() & reportable).sum())
        date_rate = (
            date_success / reportable_count if reportable_count else None
        )
    else:
        date_success = 0
        date_rate = None

    if DATE_NAME_PATTERN.search(column) and date_rate is not None:
        inferred_type = "date-like" if date_rate >= 0.98 else "string"
    elif NUMERIC_NAME_PATTERN.search(column) and numeric_rate is not None:
        inferred_type = "numeric-like" if numeric_rate >= 0.98 else "string"
    else:
        inferred_type = "string"

    top_values = [
        {"value": value, "count": int(count)}
        for value, count in text[text.ne("")].value_counts().head(5).items()
    ]
    return {
        "dataset_id": dataset_id,
        "column_name": column,
        "physical_ingest_type": "string",
        "inferred_semantic_type": inferred_type,
        "row_count": int(len(series)),
        "blank_count": int(blank_mask.sum()),
        "blank_rate": float(blank_mask.mean()) if len(series) else 0.0,
        "suppressed_token_count": int(suppressed.sum()),
        "distinct_nonblank_count": int(text[text.ne("")].nunique()),
        "numeric_parse_success_count": numeric_success,
        "numeric_parse_eligible_count": reportable_count,
        "numeric_parse_success_rate": numeric_rate,
        "date_parse_success_count": date_success,
        "date_parse_eligible_count": reportable_count,
        "date_parse_success_rate": date_rate,
        "top_values_json": json.dumps(top_values, ensure_ascii=False),
    }


def measurement_period_rows(
    dataset_id: str, frame: pd.DataFrame
) -> tuple[list[dict[str, Any]], int, list[str]]:
    start_column = resolve_alias(
        "Measure Start Date|Start Date|Measurement Start Date", frame.columns
    )
    end_column = resolve_alias(
        "Measure End Date|End Date|Measurement End Date", frame.columns
    )
    if not start_column or not end_column:
        return [], 0, [
            name
            for name, value in (
                ("start date", start_column),
                ("end date", end_column),
            )
            if value is None
        ]

    pairs = (
        frame[[start_column, end_column]]
        .fillna("")
        .astype(str)
        .value_counts(dropna=False)
        .reset_index(name="row_count")
    )
    rows = [
        {
            "dataset_id": dataset_id,
            "start_date_column": start_column,
            "end_date_column": end_column,
            "measurement_start_date": row[start_column],
            "measurement_end_date": row[end_column],
            "row_count": int(row["row_count"]),
        }
        for _, row in pairs.iterrows()
    ]
    starts = pd.to_datetime(
        frame[start_column], format="%m/%d/%Y", errors="coerce"
    )
    ends = pd.to_datetime(
        frame[end_column], format="%m/%d/%Y", errors="coerce"
    )
    violations = int(((starts.notna() & ends.notna()) & (starts > ends)).sum())
    return rows, violations, []


def collect_measures(
    dataset_id: str, frame: pd.DataFrame
) -> list[dict[str, Any]]:
    measure_id_column = resolve_alias("Measure ID", frame.columns)
    measure_name_column = resolve_alias("Measure Name", frame.columns)
    if not measure_id_column and not measure_name_column:
        return []

    group_columns = [
        column
        for column in (measure_id_column, measure_name_column)
        if column is not None
    ]
    start_column = resolve_alias(
        "Measure Start Date|Start Date|Measurement Start Date", frame.columns
    )
    end_column = resolve_alias(
        "Measure End Date|End Date|Measurement End Date", frame.columns
    )
    footnote_columns = [
        column for column in frame.columns if "footnote" in column.casefold()
    ]
    score_columns = [
        column for column in frame.columns if NUMERIC_NAME_PATTERN.search(column)
    ]

    rows: list[dict[str, Any]] = []
    for key, group in frame.groupby(group_columns, dropna=False):
        if not isinstance(key, tuple):
            key = (key,)
        key_values = dict(zip(group_columns, key, strict=False))
        footnoted = (
            int(
                group[footnote_columns]
                .apply(lambda col: normalized_text(col).ne(""))
                .any(axis=1)
                .sum()
            )
            if footnote_columns
            else 0
        )
        suppressed = int(
            group.apply(lambda col: suppression_mask(col)).any(axis=1).sum()
        )
        rows.append(
            {
                "dataset_id": dataset_id,
                "measure_id": (
                    key_values.get(measure_id_column, "")
                    if measure_id_column
                    else ""
                ),
                "measure_name": (
                    key_values.get(measure_name_column, "")
                    if measure_name_column
                    else ""
                ),
                "row_count": int(len(group)),
                "measurement_start_dates": (
                    "|".join(sorted(group[start_column].astype(str).unique()))
                    if start_column
                    else ""
                ),
                "measurement_end_dates": (
                    "|".join(sorted(group[end_column].astype(str).unique()))
                    if end_column
                    else ""
                ),
                "footnoted_row_count": footnoted,
                "suppressed_row_count": suppressed,
                "source_numeric_fields": "|".join(score_columns),
            }
        )
    return rows


def profile_dataset(
    *,
    project_root: Path,
    manifest_row: dict[str, Any],
    run_id: str,
    checked_at: str,
    checks: list[dict[str, Any]],
) -> tuple[
    dict[str, Any],
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    dict[str, Any],
]:
    dataset_id = manifest_row["dataset_id"]
    raw_path = project_root / manifest_row["raw_path"]
    frame = pd.read_csv(
        raw_path,
        dtype=str,
        keep_default_na=False,
        na_filter=False,
        encoding="utf-8-sig",
    )
    columns = list(frame.columns)
    candidate_key, missing_key_parts = resolve_candidate_key(
        dataset_id, columns
    )
    exact_duplicate_rows = int(frame.duplicated(keep=False).sum())

    if candidate_key:
        key_blank_rows = int(
            frame[candidate_key]
            .apply(lambda col: normalized_text(col).eq(""))
            .any(axis=1)
            .sum()
        )
        duplicate_key_rows = int(
            frame.duplicated(subset=candidate_key, keep=False).sum()
        )
        duplicate_key_groups = int(
            (
                frame.groupby(candidate_key, dropna=False)
                .size()
                .gt(1)
                .sum()
            )
        )
    else:
        key_blank_rows = 0
        duplicate_key_rows = 0
        duplicate_key_groups = 0

    id_columns = [
        column
        for column in columns
        if column.casefold() in {"facility id", "ccn"}
    ]
    invalid_facility_ids = 0
    alternative_facility_ids = 0
    leading_zero_facility_ids = 0
    for column in id_columns:
        values = normalized_text(frame[column])
        nonblank = values.ne("")
        invalid_facility_ids += int(
            (nonblank & ~values.str.fullmatch(r"[A-Za-z0-9]{6}")).sum()
        )
        alternative_facility_ids += int(
            (
                nonblank
                & values.str.fullmatch(r"[A-Za-z0-9]{6}")
                & ~values.str.fullmatch(r"\d{6}")
            ).sum()
        )
        leading_zero_facility_ids += int(
            (nonblank & values.str.startswith("0")).sum()
        )

    footnote_columns = [
        column for column in columns if "footnote" in column.casefold()
    ]
    footnoted_rows = (
        int(
            frame[footnote_columns]
            .apply(lambda col: normalized_text(col).ne(""))
            .any(axis=1)
            .sum()
        )
        if footnote_columns
        else 0
    )
    token_counter: Counter[str] = Counter()
    for column in columns:
        normalized = normalized_text(frame[column]).str.casefold()
        token_counter.update(
            value
            for value in normalized[normalized.isin(SUPPRESSION_TOKENS)]
            if value
        )

    periods, period_order_violations, missing_period_parts = (
        measurement_period_rows(dataset_id, frame)
    )
    fiscal_year_column = resolve_alias("Fiscal Year", columns)
    fiscal_year_values = (
        sorted(normalized_text(frame[fiscal_year_column]).unique())
        if fiscal_year_column
        else []
    )
    fiscal_year_blank_rows = (
        int(normalized_text(frame[fiscal_year_column]).eq("").sum())
        if fiscal_year_column
        else 0
    )
    column_profiles = [
        profile_column(dataset_id, column, frame[column])
        for column in columns
    ]
    measures = collect_measures(dataset_id, frame)
    actual_hash = sha256_file(raw_path)

    append_check(
        checks,
        run_id=run_id,
        dataset_id=dataset_id,
        check_name="source_hash_matches_manifest",
        expected=manifest_row["sha256"],
        actual=actual_hash,
        status="PASS" if actual_hash == manifest_row["sha256"] else "FAIL",
        severity="Critical",
        details="Raw file SHA-256 is recalculated before profiling.",
        checked_at=checked_at,
    )
    append_check(
        checks,
        run_id=run_id,
        dataset_id=dataset_id,
        check_name="source_release_date_recorded",
        expected="nonblank",
        actual=manifest_row.get("source_release_date", ""),
        status=(
            "PASS" if manifest_row.get("source_release_date") else "FAIL"
        ),
        severity="High",
        details="Catalog release date is distinct from measurement period.",
        checked_at=checked_at,
    )
    append_check(
        checks,
        run_id=run_id,
        dataset_id=dataset_id,
        check_name="row_count_reconciles_to_manifest",
        expected=int(manifest_row["row_count"]),
        actual=int(len(frame)),
        status=(
            "PASS"
            if int(manifest_row["row_count"]) == int(len(frame))
            else "FAIL"
        ),
        severity="Critical",
        details="CSV data rows exclude the header.",
        checked_at=checked_at,
    )
    append_check(
        checks,
        run_id=run_id,
        dataset_id=dataset_id,
        check_name="column_count_reconciles_to_manifest",
        expected=int(manifest_row["column_count"]),
        actual=int(len(columns)),
        status=(
            "PASS"
            if int(manifest_row["column_count"]) == int(len(columns))
            else "FAIL"
        ),
        severity="Critical",
        details="Column names are preserved exactly as published.",
        checked_at=checked_at,
    )
    append_check(
        checks,
        run_id=run_id,
        dataset_id=dataset_id,
        check_name="exact_duplicate_rows",
        expected=0,
        actual=exact_duplicate_rows,
        status="PASS" if exact_duplicate_rows == 0 else "FAIL",
        severity="High",
        details="Counts every row participating in an exact duplicate.",
        checked_at=checked_at,
    )
    append_check(
        checks,
        run_id=run_id,
        dataset_id=dataset_id,
        check_name="candidate_grain_resolved",
        expected="all candidate key columns present",
        actual=(
            " + ".join(candidate_key)
            if candidate_key
            else f"missing: {', '.join(missing_key_parts)}"
        ),
        status="PASS" if candidate_key else "REVIEW",
        severity="High",
        details="Candidate grain must be confirmed before fact modeling.",
        checked_at=checked_at,
    )
    if candidate_key:
        append_check(
            checks,
            run_id=run_id,
            dataset_id=dataset_id,
            check_name="candidate_grain_unique",
            expected=0,
            actual=duplicate_key_rows,
            status="PASS" if duplicate_key_rows == 0 else "FAIL",
            severity="Critical",
            details=(
                f"Candidate key: {' + '.join(candidate_key)}; "
                f"duplicate groups: {duplicate_key_groups}."
            ),
            checked_at=checked_at,
        )
        append_check(
            checks,
            run_id=run_id,
            dataset_id=dataset_id,
            check_name="candidate_key_complete",
            expected=0,
            actual=key_blank_rows,
            status="PASS" if key_blank_rows == 0 else "FAIL",
            severity="Critical",
            details="Blank means an empty source string, not a suppressed score.",
            checked_at=checked_at,
        )
    if id_columns:
        append_check(
            checks,
            run_id=run_id,
            dataset_id=dataset_id,
            check_name="facility_id_six_character_string",
            expected=0,
            actual=invalid_facility_ids,
            status="PASS" if invalid_facility_ids == 0 else "FAIL",
            severity="Critical",
            details=(
                "Facility IDs were ingested as strings; "
                f"{leading_zero_facility_ids} row values begin with zero and "
                f"{alternative_facility_ids} row values are six-character "
                "federal VA/DoD identifiers rather than numeric CCNs."
            ),
            checked_at=checked_at,
        )
    append_check(
        checks,
        run_id=run_id,
        dataset_id=dataset_id,
        check_name="suppression_text_preserved",
        expected="raw text retained; never coerced to zero",
        actual=json.dumps(token_counter, ensure_ascii=False, sort_keys=True),
        status="PASS",
        severity="Critical",
        details="All raw fields were ingested as strings with NA coercion disabled.",
        checked_at=checked_at,
    )
    append_check(
        checks,
        run_id=run_id,
        dataset_id=dataset_id,
        check_name="footnote_columns_preserved",
        expected=(
            "source footnote columns retained"
            if PROVIDER_DATASETS[dataset_id]["footnote_expected"]
            else "no footnote field expected in published schema"
        ),
        actual=(
            f"{len(footnote_columns)} columns; {footnoted_rows} rows"
            if footnote_columns
            else "no footnote-named column in source schema"
        ),
        status=(
            "PASS"
            if (
                footnote_columns
                or not PROVIDER_DATASETS[dataset_id]["footnote_expected"]
            )
            else "FAIL"
        ),
        severity="Medium",
        details=(
            "Expected presence is based on the April 2026 CMS Hospital "
            "Downloadable Database Data Dictionary."
        ),
        checked_at=checked_at,
    )
    period_role = PROVIDER_DATASETS[dataset_id]["period_role"]
    if period_role == "source_release_version":
        period_status = (
            "PASS" if manifest_row.get("source_release_date") else "FAIL"
        )
        period_actual: Any = manifest_row.get("source_release_date", "")
        period_details = (
            "This source is a release-versioned facility dimension. Its "
            "overall rating summarizes underlying measures with differing "
            "collection periods; no row-level measurement dates are published."
        )
    elif period_role == "fiscal_year":
        period_status = (
            "PASS"
            if fiscal_year_column
            and not fiscal_year_blank_rows
            and fiscal_year_values
            else "FAIL"
        )
        period_actual = "|".join(fiscal_year_values)
        period_details = (
            "HVBP TPS is keyed by Fiscal Year; the source does not publish "
            "start/end measurement dates in this file."
        )
    else:
        period_status = (
            "PASS"
            if not missing_period_parts and period_order_violations == 0
            else ("REVIEW" if missing_period_parts else "FAIL")
        )
        period_actual = period_order_violations
        period_details = (
            "Validated parsed start date <= parsed end date. HRRP fiscal year "
            "is also carried as program context from the official file name."
        )
    append_check(
        checks,
        run_id=run_id,
        dataset_id=dataset_id,
        check_name="measurement_period_order",
        expected=(
            "valid source release"
            if period_role == "source_release_version"
            else ("nonblank fiscal year" if period_role == "fiscal_year" else 0)
        ),
        actual=period_actual,
        status=period_status,
        severity="High",
        details=period_details,
        checked_at=checked_at,
    )

    numeric_fields_reviewed = 0
    numeric_parse_failures = 0
    for profile in column_profiles:
        if not NUMERIC_NAME_PATTERN.search(profile["column_name"]):
            continue
        eligible = profile["numeric_parse_eligible_count"]
        rate = profile["numeric_parse_success_rate"]
        if eligible and rate is not None and rate > 0:
            numeric_fields_reviewed += 1
            if rate < 0.98:
                numeric_parse_failures += 1
    append_check(
        checks,
        run_id=run_id,
        dataset_id=dataset_id,
        check_name="numeric_field_parse_profile",
        expected="reviewable numeric candidates profiled",
        actual=(
            f"{numeric_fields_reviewed} candidates; "
            f"{numeric_parse_failures} below 98% reportable parse rate"
        ),
        status="PASS" if numeric_parse_failures == 0 else "REVIEW",
        severity="Medium",
        details=(
            "Suppression tokens and blanks are excluded from the denominator; "
            "no value is replaced with zero."
        ),
        checked_at=checked_at,
    )

    summary = {
        "dataset_id": dataset_id,
        "title": manifest_row["title"],
        "raw_path": manifest_row["raw_path"],
        "row_count": int(len(frame)),
        "column_count": int(len(columns)),
        "file_size_bytes": int(raw_path.stat().st_size),
        "sha256": actual_hash,
        "source_release_date": manifest_row.get("source_release_date", ""),
        "source_modified_date": manifest_row.get("source_modified_date", ""),
        "candidate_key": " + ".join(candidate_key),
        "candidate_key_blank_rows": key_blank_rows,
        "candidate_key_duplicate_rows": duplicate_key_rows,
        "candidate_key_duplicate_groups": duplicate_key_groups,
        "exact_duplicate_rows": exact_duplicate_rows,
        "facility_id_columns": "|".join(id_columns),
        "invalid_facility_id_count": invalid_facility_ids,
        "alternative_facility_id_row_count": alternative_facility_ids,
        "leading_zero_facility_id_count": leading_zero_facility_ids,
        "footnote_columns": "|".join(footnote_columns),
        "footnoted_row_count": footnoted_rows,
        "suppression_token_count": int(sum(token_counter.values())),
        "suppression_tokens_json": json.dumps(
            token_counter, ensure_ascii=False, sort_keys=True
        ),
        "measurement_period_variant_count": len(periods),
        "measurement_period_order_violations": period_order_violations,
    }
    schema = {
        "dataset_id": dataset_id,
        "columns": columns,
        "column_count": len(columns),
        "source_release_date": manifest_row.get("source_release_date", ""),
        "sha256": actual_hash,
    }
    return summary, column_profiles, periods, measures, schema


def write_markdown_report(
    path: Path,
    *,
    manifest: dict[str, Any],
    summaries: pd.DataFrame,
    checks: pd.DataFrame,
) -> None:
    statuses = checks["status"].value_counts().to_dict()
    total_rows = int(summaries["row_count"].sum())
    total_bytes = int(summaries["file_size_bytes"].sum())
    lines = [
        "# Provider Phase 1 Source Profiling",
        "",
        f"- Snapshot date: `{manifest['snapshot_date']}`",
        f"- Catalog release date(s): "
        f"`{', '.join(sorted(set(summaries['source_release_date'])))}`",
        f"- Datasets: `{len(summaries)}`",
        f"- Source rows across files: `{total_rows:,}`",
        f"- Raw CSV bytes: `{total_bytes:,}`",
        f"- QA status counts: `{json.dumps(statuses, sort_keys=True)}`",
        "",
        "These are public, aggregate CMS provider-quality files. They are not "
        "patient-level claims or EHR records. Suppressed and missing values "
        "remain text or null semantics and are never converted to zero.",
        "",
        "## Dataset and candidate-grain summary",
        "",
        "| Dataset | Rows | Columns | Candidate key | Duplicate key rows | "
        "Suppression tokens | Footnoted rows |",
        "|---|---:|---:|---|---:|---:|---:|",
    ]
    for _, row in summaries.iterrows():
        lines.append(
            f"| `{row['dataset_id']}` | {int(row['row_count']):,} | "
            f"{int(row['column_count'])} | "
            f"{row['candidate_key'] or 'Needs program-year interpretation'} | "
            f"{int(row['candidate_key_duplicate_rows']):,} | "
            f"{int(row['suppression_token_count']):,} | "
            f"{int(row['footnoted_row_count']):,} |"
        )
    lines.extend(
        [
            "",
            "## Non-pass checks",
            "",
            "| Dataset | Check | Status | Severity | Actual | Details |",
            "|---|---|---|---|---|---|",
        ]
    )
    non_pass = checks[checks["status"] != "PASS"]
    if non_pass.empty:
        lines.append("| — | — | — | — | — | No non-pass checks. |")
    else:
        for _, row in non_pass.iterrows():
            lines.append(
                f"| `{row['table_name']}` | {row['check_name']} | "
                f"{row['status']} | {row['severity']} | "
                f"{str(row['actual_value']).replace('|', '/')} | "
                f"{str(row['details']).replace('|', '/')} |"
            )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- A `REVIEW` result is not silently treated as a pass. It identifies "
            "a schema or program-specific rule that must be resolved before "
            "Gold modeling.",
            "- Candidate-key checks validate the proposed source grain only. "
            "The final fact grain must also include the source release and the "
            "relevant measurement or fiscal/program period.",
            "- Numeric parse rates exclude blank and recognized suppression "
            "tokens. Official score fields are preserved separately from any "
            "future project-derived benchmark.",
            "",
            "## Evidence files",
            "",
            "- `dataset_summary.csv`",
            "- `column_profile.csv`",
            "- `measurement_periods.csv`",
            "- `measure_catalog.csv`",
            "- `quality_checks.csv`",
            "- `schema_snapshot.json`",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    project_root = args.project_root.resolve()
    manifest_path = (
        args.manifest.resolve()
        if args.manifest
        else latest_manifest(project_root)
    )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    snapshot_date = manifest["snapshot_date"]
    output_dir = (
        args.output_dir.resolve()
        if args.output_dir
        else project_root / "outputs" / "provider_phase1" / snapshot_date
    )
    output_dir.mkdir(parents=True, exist_ok=True)

    checked_at = utc_now_iso()
    run_id = f"provider_profile_{snapshot_date}_{checked_at[:19]}"
    checks: list[dict[str, Any]] = []
    summaries: list[dict[str, Any]] = []
    columns: list[dict[str, Any]] = []
    periods: list[dict[str, Any]] = []
    measures: list[dict[str, Any]] = []
    schemas: list[dict[str, Any]] = []

    for manifest_row in manifest["datasets"]:
        summary, column_rows, period_rows, measure_rows, schema = (
            profile_dataset(
                project_root=project_root,
                manifest_row=manifest_row,
                run_id=run_id,
                checked_at=checked_at,
                checks=checks,
            )
        )
        summaries.append(summary)
        columns.extend(column_rows)
        periods.extend(period_rows)
        measures.extend(measure_rows)
        schemas.append(schema)

    baseline_path = (
        project_root / "data" / "reference" / "provider_schema_baseline.json"
    )
    if baseline_path.exists():
        baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
        baseline_by_id = {
            item["dataset_id"]: item for item in baseline["datasets"]
        }
        for schema in schemas:
            prior = baseline_by_id.get(schema["dataset_id"])
            if prior is None:
                status = "REVIEW"
                actual = "dataset not present in baseline"
                details = "A new dataset requires explicit schema approval."
            else:
                prior_columns = prior["columns"]
                current_columns = schema["columns"]
                added = [
                    column
                    for column in current_columns
                    if column not in prior_columns
                ]
                removed = [
                    column
                    for column in prior_columns
                    if column not in current_columns
                ]
                reordered = (
                    not added
                    and not removed
                    and prior_columns != current_columns
                )
                status = (
                    "PASS"
                    if not added and not removed and not reordered
                    else "REVIEW"
                )
                actual = json.dumps(
                    {
                        "added": added,
                        "removed": removed,
                        "reordered": reordered,
                    },
                    ensure_ascii=False,
                    sort_keys=True,
                )
                details = (
                    "Column names and order are compared with the accepted "
                    "Provider schema baseline."
                )
            append_check(
                checks,
                run_id=run_id,
                dataset_id=schema["dataset_id"],
                check_name="schema_matches_baseline",
                expected="no added, removed, or reordered columns",
                actual=actual,
                status=status,
                severity="High",
                details=details,
                checked_at=checked_at,
            )

    summary_frame = pd.DataFrame(summaries).sort_values("dataset_id")
    column_frame = pd.DataFrame(columns).sort_values(
        ["dataset_id", "column_name"]
    )
    period_frame = pd.DataFrame(periods)
    measure_frame = pd.DataFrame(measures)
    check_frame = pd.DataFrame(checks).sort_values(
        ["status", "severity", "table_name", "check_name"]
    )

    summary_frame.to_csv(
        output_dir / "dataset_summary.csv", index=False, encoding="utf-8-sig"
    )
    column_frame.to_csv(
        output_dir / "column_profile.csv", index=False, encoding="utf-8-sig"
    )
    period_frame.to_csv(
        output_dir / "measurement_periods.csv",
        index=False,
        encoding="utf-8-sig",
    )
    measure_frame.to_csv(
        output_dir / "measure_catalog.csv",
        index=False,
        encoding="utf-8-sig",
    )
    check_frame.to_csv(
        output_dir / "quality_checks.csv",
        index=False,
        encoding="utf-8-sig",
    )
    schema_payload = {
        "schema_version": 1,
        "run_id": run_id,
        "checked_at": checked_at,
        "snapshot_date": snapshot_date,
        "datasets": schemas,
    }
    write_json(output_dir / "schema_snapshot.json", schema_payload)

    if baseline_path.exists():
        baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
        write_json(output_dir / "schema_baseline_used.json", baseline)
    else:
        write_json(baseline_path, schema_payload)

    write_markdown_report(
        output_dir / "profiling_report.md",
        manifest=manifest,
        summaries=summary_frame,
        checks=check_frame,
    )
    print(
        json.dumps(
            {
                "run_id": run_id,
                "output_dir": str(output_dir),
                "datasets": len(summary_frame),
                "rows": int(summary_frame["row_count"].sum()),
                "qa_status_counts": check_frame["status"]
                .value_counts()
                .to_dict(),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
