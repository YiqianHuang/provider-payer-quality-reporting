# Provider Model QA Report

- Created at: `2026-08-26T23:57:24+00:00`
- Database: `data/processed/provider_quality.sqlite`
- Database SHA-256: `c7aa86c0dcaa0386ac516034dc0498875e510f4219a885bff7bae8be58bfffb8`
- Model QA: `{"PASS": 33}`

The model contains public, aggregate CMS Provider results. It does not contain patient-level claims or EHR records and does not recalculate formal HEDIS measures.

## Table row counts

| Table | Rows |
|---|---:|
| `dim_facility` | 5,440 |
| `dim_geography` | 56 |
| `dim_measure` | 29 |
| `dim_reporting_period` | 8 |
| `dim_source_release` | 6 |
| `fact_provider_hrrp_measure` | 18,330 |
| `fact_provider_measure` | 67,060 |
| `fact_provider_national_benchmark` | 14 |
| `fact_provider_program_score` | 2,455 |
| `fact_provider_state_benchmark` | 784 |
| `fact_quality_check` | 115 |

## Non-pass checks

| Table | Check | Status | Severity | Actual | Details |
|---|---|---|---|---|---|
| - | - | - | - | - | No non-pass model checks. |
