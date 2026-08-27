# Provider MVP Implementation Plan

## Delivery sequence

### Phase 0 - Charter and source verification

Status: **complete for Provider scope**

The 2026-08-26 freshness audit found CMS release `2026-08-13`, replacing the
initial `2026-07-29` catalog release. A new immutable
`data/raw/provider/2026-08-26/` partition was created and all downstream
profiling/model checks were rerun.

1. Treat `Provider_Payer_Quality_Reporting_Project_Starter.md` as the project
   charter and highest-priority execution standard.
2. Confirm the workspace is independent from
   `behavioral-health-resource-analysis`.
3. Verify the six required CMS dataset IDs, catalog metadata, CSV
   distributions, and hospital data dictionary.
4. Record licensing and interpretation boundaries.

Exit criteria:

- official source access is confirmed or a blocker is documented;
- Provider, Payer, and synthetic scopes are separated;
- no restricted HEDIS specification is required.

### Phase 1 - Provider ingestion and source profiling

Status: **complete**

1. Download the six required CSVs to
   `data/raw/provider/<download-date>/<dataset-id>/`.
2. Save catalog metadata beside each file and the CMS dictionary under
   `data/reference/`.
3. Calculate SHA-256, file size, row count, column count, and header.
4. Ingest every raw field as a string.
5. Profile column types, blanks, cardinality, numeric/date parsability,
   suppression values, footnotes, candidate grain, duplicates, and periods.
6. Establish the first accepted schema baseline.
7. Save a rerunnable profiling report and machine-readable QA results.

Exit criteria:

- no unresolved critical/high source check;
- every file reconciles to its manifest;
- each candidate grain is unique and complete;
- alternate federal Facility IDs are preserved, not forced into numeric CCNs;
- missing and suppression semantics are not converted to zero.

### Phase 2 - Provider model, transformations, and SQL

Status: **complete**

1. Load source-shaped Bronze tables.
2. Build typed Silver tables with separate raw and numeric score fields.
3. Create release-versioned dimensions:
   `dim_facility`, `dim_measure`, `dim_reporting_period`,
   `dim_source_release`, and `dim_geography`.
4. Create facts:
   `fact_provider_measure`, `fact_provider_program_score`,
   `fact_provider_state_benchmark`, `fact_provider_national_benchmark`, and
   `fact_quality_check`.
5. Implement SQL views for facility performance, official comparisons,
   suppression coverage, and source reconciliation.
6. Add automated model-level QA for uniqueness, orphan coverage, safe numeric
   parsing, period alignment, range/order rules, and join expansion.

Exit criteria:

- all declared fact grains are unique;
- no unexplained orphan or many-to-many expansion;
- numeric parsing excludes missing/suppressed values;
- lower/score/higher ordering is valid where applicable;
- state/national joins reconcile to the official files.

### Phase 3 - Power BI semantic model

Status: **semantic contract and TMDL model item implemented; headless and TMDL
round-trip validation complete; Power BI Desktop processing remains**

1. Define a star schema and relationship directions.
2. Hide technical and unsafe-to-sum raw numeric columns.
3. define explicit DAX measures for reportable facility/measure counts,
   suppression counts, comparison categories, HRRP/HVBP scores, and source
   freshness.
4. Make release date, measurement period, and fiscal year visible as separate
   concepts.
5. Test that blanks and suppression never render as zero.
6. Create report pages only after the semantic-model QA gate passes.

Exit criteria:

- model relationships and measures are documented;
- all headline values reconcile to SQL;
- direction and period are visible;
- no dashboard inference exceeds the published aggregate data.

### Phase 4 - Payer module

Status: **blocked by design until Provider MVP QA is complete**

The Payer phase starts only after the Provider model, SQL views, automated QA,
and Power BI semantic model pass their gates.

## Reproducible commands

```powershell
python -m src.download.download_provider `
  --project-root . `
  --snapshot-date 2026-08-26

python -m src.quality.profile_provider `
  --project-root .

python -m src.transform.build_provider_model `
  --project-root . `
  --snapshot-date 2026-08-26

python -m src.quality.validate_semantic_model `
  --project-root .

python -m src.powerbi.export_powerbi_tables `
  --project-root .

powershell.exe -NoProfile -ExecutionPolicy Bypass `
  -File src\powerbi\build_tmdl_semantic_model.ps1 `
  -ProjectRoot .

python -m unittest discover -s tests -v
```

For an existing immutable snapshot, the downloader refuses overwrite. Use
`--reuse-existing` only to revalidate the exact local files.

## Change control

Every future release must:

1. receive a new snapshot partition;
2. capture fresh catalog metadata;
3. compare schema with the accepted baseline;
4. compare row counts, periods, measure IDs, suppression rates, and score
   distributions with the prior release;
5. document whether differences come from the source, code, or business logic.
