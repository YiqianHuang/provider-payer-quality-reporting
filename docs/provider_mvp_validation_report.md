# Provider MVP Validation Report

Validation date: **2026-08-26**

The initial raw snapshot was dated 2026-07-29. A non-destructive CMS catalog
freshness audit on 2026-08-26 found a newer CMS release dated 2026-08-13;
the active raw snapshot is now `data/raw/provider/2026-08-26/`. The audit and
release comparison are in `outputs/provider_freshness/2026-08-26/`; a
post-refresh check against the new snapshot is in
`outputs/provider_freshness/2026-08-26_post_snapshot/`.

## Overall assessment

**Share with caveats.**

Provider source verification, immutable snapshotting, source profiling,
relational modeling, SQL reporting views, automated QA, and the Power BI TMDL
semantic-model item are reproducible and have passed their implemented
checks. The Provider MVP must not yet be described as fully complete because
the model has not been processed and inspected in Power BI Desktop. Payer
remains gated.

The narrower Phase 1 source package is **ready to share** with the limitations
documented below.

## Question and scope reviewed

This validation asks whether the Provider MVP artifacts faithfully represent
the six selected public CMS aggregate datasets, preserve source semantics, and
support a controlled reporting model without making patient-level, formal
HEDIS, causal, or regulatory-reporting claims.

It does not evaluate a dashboard, patient outcomes, a payer module, or
synthetic gap closure.

## Evidence inventory

- Project charter:
  `Provider_Payer_Quality_Reporting_Project_Starter.md`
- Source manifest:
  `data/raw/provider/2026-08-26/provider_snapshot_manifest.json`
- Source profiling:
  `outputs/provider_phase1/2026-08-26/`
- Relational model:
  `data/processed/provider_quality.sqlite`
- Model QA:
  `outputs/provider_model/2026-08-26/`
- DDL and reporting views:
  `sql/ddl/001_provider_schema.sql` and
  `sql/views/001_provider_reporting_views.sql`
- Semantic-model contract:
  `powerbi/semantic_model.json`
- TMDL semantic-model item:
  `powerbi/ProviderQuality.SemanticModel/`
- Semantic-model validation:
  `outputs/powerbi/semantic_model_validation.json` and
  `outputs/powerbi/tmdl_validation.json`
- Regression tests:
  `tests/test_provider_phase1.py` and `tests/test_provider_model.py`

## Methodology review

- The six active sources are CMS Provider Data Catalog datasets and the
  current captured catalog release for all six is 2026-08-13.
- Measurement periods are taken from row-level dates or the published fiscal
  year, not inferred from the catalog release date.
- Facility IDs are ingested as strings. Numeric six-digit identifiers and
  six-character federal identifiers are not conflated.
- Raw values are retained alongside typed values. Recognized missing,
  suppressed, and not-applicable tokens parse to null semantics, never zero.
- Every source and fact grain is declared and checked for completeness and
  uniqueness.
- Official state and national comparison files remain separate from
  project-derived interpretations.
- Power BI relationships are one-to-many and single-direction, with no
  fact-to-fact joins or implicit summation of rates, ratios, or scores.

## Calculation and reconciliation spot-checks

| Check | Result | Evidence |
|---|---|---|
| Snapshot shape and integrity | Verified | 6 files, 94,062 rows, 23,273,953 CSV bytes; every file size, row count, column count, and SHA-256 rechecked by regression tests |
| Source grains | Verified | 6/6 candidate keys complete and unique; no exact duplicate rows |
| Source QA | Verified | 82/82 checks passed |
| Model QA | Verified | 33/33 checks passed |
| Provider benchmark joins | Verified | all 67,060 provider-measure rows match both the official state and national benchmark grain |
| Semantic contract | Verified headlessly | 106/106 schema, relationship, key, aggregation, and DAX-reference checks passed |
| TMDL serialization | Verified | 11 tables, 19 relationships, and 15 measures round-tripped through the Power BI Desktop Tabular Object Model assembly |
| Regression suite | Verified | 21/21 tests passed after a full profiling/model/semantic validation rerun |

Passing a check means the documented rule was satisfied; it does not mean CMS
source data are free of all real-world limitations.

## Issues and incomplete handoff items

1. **Medium — Power BI Desktop processing is not validated.** Power BI Desktop
   is installed, and driver-free typed CSV import extracts plus a TMDL model
   item have been generated. Until the model is processed and relationships,
   measures, data categories, and blank rendering are inspected in Desktop,
   the Power BI workstream and full Provider MVP remain incomplete.
2. **Medium — 21 program-file facilities do not match the current General
   Information release.** HRRP contributes 20 distinct unmatched Facility IDs
   and HVBP contributes 9, with 21 in the union. The model preserves those
   source-specific facility versions. The downloaded files do not establish
   the cause.
3. **Medium — release-to-release interval behavior changed.** The two
   published `Hybrid_HWR` rows violating the generic lower/score/upper rule
   were present in the 2026-05-13 release and carried CMS Footnote 29. The
   active 2026-08-13 release has no such exceptions; both release outputs are
   retained for comparison.
4. **Low — HCAHPS and HAI are deferred.** They are valid future Provider
   sources but are not part of the accepted six-file core snapshot.

## Visualization review

Not applicable. No dashboard pages or report visuals have been created.

## Required caveats for stakeholders

- These are public, aggregate CMS provider-quality results, not patient-level
  claims, EHR records, or real patient data.
- The project does not perform or claim formal HEDIS calculation or reporting.
- Published missing, not-available, not-applicable, and suppression states are
  not zero.
- Measurement periods differ across measures and programs; cross-measure
  comparisons require period and unit alignment.
- Facility ID is a source string; 164 General Information identifiers are
  alternate federal VA/DoD IDs and must not be labeled Medicare CCNs.
- The model republishes CMS results and does not independently reproduce CMS
  risk adjustment, confidence intervals, or payment calculations.
- CMS public-domain reuse does not imply CMS or U.S. government endorsement.

## Gate decision

- Phase 0 source verification: **pass**
- Phase 1 ingestion and profiling: **pass**
- Phase 2 relational model, SQL views, and automated QA: **pass**
- Phase 3 semantic contract, TMDL model item, and headless QA: **pass**
- Phase 3 Power BI Desktop processing/inspection: **pending**
- Dashboard pages: **not started by design**
- Payer module: **closed until the pending Provider gate is completed**
