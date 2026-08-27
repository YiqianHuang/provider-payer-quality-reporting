# CMS Provider Source Freshness Check

- As of date: **2026-08-26**
- Checked at UTC: `2026-08-26T23:47:38+00:00`
- Compared snapshot: `2026-07-29`
- Overall status: **REVIEW**
- Status counts: `{"CHANGED": 6}`

The check reads current CMS catalog metadata and compares release date, modified date, selected CSV URL, local file existence, and local snapshot SHA-256. It does not overwrite or redownload the immutable snapshot.

| Dataset | Status | Current release | Snapshot release | Current modified | Snapshot modified | URL changed | Local hash |
|---|---|---|---|---|---|---|---|
| `xubh-q36u` | CHANGED | 2026-08-13 | 2026-05-13 | 2026-07-22 | 2026-04-28 | True | True |
| `632h-zaca` | CHANGED | 2026-08-13 | 2026-05-13 | 2026-07-22 | 2026-04-28 | True | True |
| `4gkm-5ypv` | CHANGED | 2026-08-13 | 2026-05-13 | 2026-07-22 | 2026-04-21 | True | True |
| `cvcs-xecj` | CHANGED | 2026-08-13 | 2026-05-13 | 2026-07-22 | 2026-04-21 | True | True |
| `9n3s-kdb3` | CHANGED | 2026-08-13 | 2026-05-13 | 2026-01-26 | 2026-01-26 | False | True |
| `ypbt-wvdk` | CHANGED | 2026-08-13 | 2026-05-13 | 2026-01-26 | 2026-01-26 | False | True |

## Decision

At least one source differs from the accepted snapshot. Create a new date-partitioned snapshot and rerun profiling/model QA before downstream use.

## Evidence

- `freshness_check.json`
- `freshness_check.csv`
