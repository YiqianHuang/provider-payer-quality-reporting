# Provider Model QA Report

- Created at: `2026-07-29T22:43:36+00:00`
- Database: `data/processed/provider_quality.sqlite`
- Database SHA-256: `fd45d7dd2e2748a8b3ed3cab7b6d06d51d1cc534a3a5f76909eba281359bff2d`
- Model QA: `{"PASS": 33}`

The model contains public, aggregate CMS Provider results. It does not contain patient-level claims or EHR records and does not recalculate formal HEDIS measures.

## Table row counts

| Table | Rows |
|---|---:|
| `dim_facility` | 5,443 |
| `dim_geography` | 56 |
| `dim_measure` | 29 |
| `dim_reporting_period` | 7 |
| `dim_source_release` | 6 |
| `fact_provider_hrrp_measure` | 18,330 |
| `fact_provider_measure` | 67,088 |
| `fact_provider_national_benchmark` | 14 |
| `fact_provider_program_score` | 2,455 |
| `fact_provider_state_benchmark` | 784 |
| `fact_quality_check` | 115 |

## Non-pass checks

| Table | Check | Status | Severity | Actual | Details |
|---|---|---|---|---|---|
| - | - | - | - | - | No non-pass model checks. |
