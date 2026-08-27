# Data Quality Plan

## Quality objective

Determine whether each CMS Provider source is trustworthy enough for modeling
and whether downstream results remain traceable to the exact public release.
Quality checks cover the raw source, typed model, reporting views, and
semantic model.

## Severity and gate rules

| Severity | Meaning | Gate effect |
|---|---|---|
| Critical | Breaks source integrity, grain, ID preservation, or reconciliation | Blocks progression |
| High | Materially risks wrong joins, periods, schema, or reporting | Blocks until resolved or explicitly redesigned |
| Medium | Program-specific or localized issue requiring documentation | May proceed only with written disposition |
| Low | Cosmetic or low-impact condition | Track and monitor |

`REVIEW` is not a pass. It requires evidence and a documented disposition.

## Phase 1 automated checks

For each of the six Provider sources, the current profiler records:

1. source SHA-256 matches the manifest;
2. source release date is present;
3. row count reconciles;
4. column count reconciles;
5. exact duplicate rows equal zero;
6. candidate-grain fields resolve;
7. candidate grain is unique;
8. candidate key is complete;
9. Facility ID is preserved as a valid six-character string where present;
10. suppression text is preserved and never coerced to zero;
11. expected footnote columns are preserved;
12. measurement start is not after measurement end, or the documented
    release/fiscal-year period role is present;
13. numeric-like fields have a parsability profile excluding blanks and
    suppression tokens;
14. current columns match the accepted schema baseline.

The profiler also writes, for every source column:

- physical ingest type;
- inferred semantic type;
- blank count and rate;
- distinct nonblank count;
- recognized suppression-token count;
- numeric/date parse eligible and success counts;
- a bounded top-value profile.

## Candidate source grains

| Source | Candidate grain validated in Phase 1 |
|---|---|
| Hospital General Information | Facility ID |
| Unplanned Visits - Hospital | Facility ID × Measure ID × Start Date × End Date |
| Unplanned Visits - State | State × Measure ID × Start Date × End Date |
| Unplanned Visits - National | Measure ID × Start Date × End Date |
| HRRP | Facility ID × Measure Name × Start Date × End Date; FY 2026 is program context |
| HVBP TPS | Facility ID × Fiscal Year |

Final fact grains add `source_release_id` so a new public release never
overwrites prior facts.

## Missingness, suppression, and footnotes

- Empty strings remain empty at raw ingestion.
- `Not Available`, `Not Applicable`, `Too Few to Report`,
  `Number of Cases Too Small`, `N/A`, and equivalent published text are
  recognized as nonnumeric states.
- The typed relational model stores `score_raw`, `score_numeric`,
  `is_suppressed`, `suppression_reason`, and `footnote_code` separately.
- A suppressed or missing score must yield SQL `NULL`/DAX `BLANK()`, never zero.
- Footnote codes are joined to the April 2026 CMS Footnote Crosswalk.
- Negative EDAC values are valid and must not be treated as outliers merely
  because they are below zero.

## Phase 2 model checks

The following checks are required before Provider modeling can pass:

- declared fact-grain uniqueness including source release;
- dimension business-key/version uniqueness;
- Facility ID join coverage by source and facility type;
- explicit retention and flagging of program-source facilities not present in
  the current General Information release;
- federal VA/DoD ID handling without false CCN assumptions;
- numeric parse success by measure and field;
- `Lower Estimate <= Score <= Higher Estimate`, where all three are
  applicable and reportable;
- `Start Date <= End Date`;
- nonblank unit, direction, official/project-defined status, period,
  suppression rule, and interpretation limit for every report measure;
- state and national benchmark join coverage;
- no fact-to-fact many-to-many relationship;
- source-to-Silver-to-Gold row reconciliation.

The accepted 2026-05-13 baseline contains two `Hybrid_HWR` interval-order
exceptions, both with CMS Footnote 29. QA therefore implements two rules:

1. unexplained interval-order violations must equal zero;
2. the two known Footnote 29 exceptions must remain separately enumerated.

A changed count in a future release triggers regression review.

## Phase 3 semantic-model checks

- relationships follow the documented star schema;
- raw rates, ratios, and scores are hidden from implicit summation;
- explicit DAX returns blank for missing/suppressed values;
- report filters expose measurement period separately from source release and
  fiscal year;
- every visible headline value can be recomputed from SQL/DAX;
- visible populations reconcile with Gold tables.

## Evidence

Phase 1 evidence is stored under:

`outputs/provider_phase1/2026-08-26/`

The authoritative files are:

- `dataset_summary.csv`;
- `column_profile.csv`;
- `measurement_periods.csv`;
- `measure_catalog.csv`;
- `quality_checks.csv`;
- `schema_snapshot.json`;
- `profiling_report.md`.

Model and semantic evidence is stored under:

- `outputs/provider_model/2026-08-26/`;
- `outputs/powerbi/`;
- `powerbi/ProviderQuality.SemanticModel/`.

Freshness evidence is stored under:

- `outputs/provider_freshness/2026-08-26/` for the release-change decision;
- `outputs/provider_freshness/2026-08-26_post_snapshot/` for the post-refresh
  unchanged check.
