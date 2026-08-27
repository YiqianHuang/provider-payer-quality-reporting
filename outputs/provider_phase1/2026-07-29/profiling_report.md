# Provider Phase 1 Source Profiling

- Snapshot date: `2026-07-29`
- Catalog release date(s): `2026-05-13`
- Datasets: `6`
- Source rows across files: `94,103`
- Raw CSV bytes: `23,261,050`
- QA status counts: `{"PASS": 82}`

These are public, aggregate CMS provider-quality files. They are not patient-level claims or EHR records. Suppressed and missing values remain text or null semantics and are never converted to zero.

## Dataset and candidate-grain summary

| Dataset | Rows | Columns | Candidate key | Duplicate key rows | Suppression tokens | Footnoted rows |
|---|---:|---:|---|---:|---:|---:|
| `4gkm-5ypv` | 784 | 14 | State + Measure ID + Start Date + End Date | 0 | 3,360 | 56 |
| `632h-zaca` | 67,088 | 20 | Facility ID + Measure ID + Start Date + End Date | 0 | 276,791 | 32,592 |
| `9n3s-kdb3` | 18,330 | 12 | Facility ID + Measure Name + Start Date + End Date | 0 | 40,211 | 6,987 |
| `cvcs-xecj` | 14 | 14 | Measure ID + Start Date + End Date | 0 | 60 | 0 |
| `xubh-q36u` | 5,432 | 38 | Facility ID | 0 | 27,642 | 2,573 |
| `ypbt-wvdk` | 2,455 | 17 | Facility ID + Fiscal Year | 0 | 312 | 0 |

## Non-pass checks

| Dataset | Check | Status | Severity | Actual | Details |
|---|---|---|---|---|---|
| — | — | — | — | — | No non-pass checks. |

## Interpretation

- A `REVIEW` result is not silently treated as a pass. It identifies a schema or program-specific rule that must be resolved before Gold modeling.
- Candidate-key checks validate the proposed source grain only. The final fact grain must also include the source release and the relevant measurement or fiscal/program period.
- Numeric parse rates exclude blank and recognized suppression tokens. Official score fields are preserved separately from any future project-derived benchmark.

## Evidence files

- `dataset_summary.csv`
- `column_profile.csv`
- `measurement_periods.csv`
- `measure_catalog.csv`
- `quality_checks.csv`
- `schema_snapshot.json`
