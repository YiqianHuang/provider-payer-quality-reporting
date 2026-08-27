# CMS Provider Source Freshness Check

- As of date: **2026-08-26**
- Checked at UTC: `2026-08-26T23:56:11+00:00`
- Compared snapshot: `2026-08-26`
- Overall status: **PASS**
- Status counts: `{"UNCHANGED": 6}`

The check reads current CMS catalog metadata and compares release date, modified date, selected CSV URL, local file existence, and local snapshot SHA-256. It does not overwrite or redownload the immutable snapshot.

| Dataset | Status | Current release | Snapshot release | Current modified | Snapshot modified | URL changed | Local hash |
|---|---|---|---|---|---|---|---|
| `xubh-q36u` | UNCHANGED | 2026-08-13 | 2026-08-13 | 2026-07-22 | 2026-07-22 | False | True |
| `632h-zaca` | UNCHANGED | 2026-08-13 | 2026-08-13 | 2026-07-22 | 2026-07-22 | False | True |
| `4gkm-5ypv` | UNCHANGED | 2026-08-13 | 2026-08-13 | 2026-07-22 | 2026-07-22 | False | True |
| `cvcs-xecj` | UNCHANGED | 2026-08-13 | 2026-08-13 | 2026-07-22 | 2026-07-22 | False | True |
| `9n3s-kdb3` | UNCHANGED | 2026-08-13 | 2026-08-13 | 2026-01-26 | 2026-01-26 | False | True |
| `ypbt-wvdk` | UNCHANGED | 2026-08-13 | 2026-08-13 | 2026-01-26 | 2026-01-26 | False | True |

## Decision

No new raw snapshot is required by this audit. Continue using the immutable `2026-08-26` snapshot and existing profiling/model QA outputs. A `CHANGED` row would require a new date-partitioned snapshot and a full rerun before downstream use.

## Evidence

- `freshness_check.json`
- `freshness_check.csv`
