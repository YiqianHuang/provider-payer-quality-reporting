# Power BI Semantic Model Specification

## Scope

This is the validated semantic-model contract for the Provider MVP. It does
not include report pages or dashboard visuals. The machine-readable source is
`powerbi/semantic_model.json`.

## Storage and refresh

- Mode: Import.
- Development source:
  `data/processed/provider_quality.sqlite`.
- Driver-free Power BI import extracts:
  `data/processed/powerbi_import/*.csv`.
- Power BI TMDL model item:
  `powerbi/ProviderQuality.SemanticModel/`.
- Production-style migration path: deploy the same DDL/views to SQL Server,
  Fabric Warehouse, or another supported relational source without changing
  the semantic grains or DAX contract.
- Refresh parameter: snapshot date/source release.
- Raw CSVs are not loaded directly into Power BI.

SQLite remains the local reproducible evidence store. The generated TMDL
partitions import validated, typed model extracts rather than the raw CMS CSVs,
so local Power BI refresh does not require an SQLite ODBC driver.

## Tables and grains

| Semantic table | Source object | Grain |
|---|---|---|
| Dim Facility | `dim_facility` | Facility ID × snapshot/facility version |
| Dim Geography | `dim_geography` | Geography type × state code |
| Dim Measure | `dim_measure` | Measure ID × source family × measurement period/fiscal year |
| Dim Reporting Period | `dim_reporting_period` | Period role × dates/fiscal year/release |
| Dim Source Release | `dim_source_release` | Dataset ID × snapshot × hash |
| Fact Provider Measure | `fact_provider_measure` | Facility × measure/version × dataset source release |
| Fact State Benchmark | `fact_provider_state_benchmark` | State × measure/version × dataset source release |
| Fact National Benchmark | `fact_provider_national_benchmark` | Measure/version × dataset source release |
| Fact HRRP | `fact_provider_hrrp_measure` | Facility × HRRP measure/version × dataset source release |
| Fact HVBP | `fact_provider_program_score` | Facility × fiscal year × program × dataset source release |
| Fact Quality Check | `fact_quality_check` | Run × phase × check |

## Relationship design

- All relationships are one-to-many and single-direction.
- No fact-to-fact relationship is permitted.
- Geography filters Facility and State Benchmark.
- Facility filters Provider Measure, HRRP, and HVBP.
- Measure filters Provider Measure, State Benchmark, National Benchmark, and
  HRRP.
- Reporting Period filters all measure/program facts.
- Source Release filters each fact through that fact's dataset-specific
  `source_release_key`.
- Source Release does not actively filter Dim Facility because the facility
  record may come from a different dataset release than a program fact.

The model intentionally avoids bidirectional relationships and ambiguous paths.

## Aggregation controls

The following fields must use `Summarize by: None`:

- facility overall rating;
- provider score, lower estimate, upper estimate, and denominator;
- national rate;
- HRRP ratio, predicted/expected rates, and source counts;
- every HVBP domain score and TPS;
- fiscal years and source row counts.

Only explicit measures may present these values. Official state category counts
may be summed when the current filter grain is understood.

## Missing and suppression behavior

- `Is Reportable = FALSE` yields `BLANK()` for provider and HRRP selected-value
  measures.
- `TPS Reportable = FALSE` yields `BLANK()` for HVBP TPS.
- `Not Available`, `Too Few to Report`, and Footnote-based exceptions never
  display as zero.
- A zero EDAC score remains a valid numeric zero because it means performance
  exactly as expected; it is not the same as missing.

## Measure direction

`Direction Adjusted Gap` returns a positive value when the selected facility is
better than the official national benchmark:

- lower-is-better: national minus facility;
- higher-is-better: facility minus national;
- context-only or missing benchmark: blank.

No cross-measure composite is created.

## Visibility

Hide surrogate keys, raw score fields, and lineage-only technical columns from
report users. Keep source release date, measurement start/end date, fiscal
year, unit, direction, suppression rule, footnote, and interpretation limit
visible through curated fields or tooltips.

## Known semantic warnings

- Eleven facilities are source-specific program records not present in the
  current General Information release. Show the `Current General Info Match`
  flag when reviewing program coverage.
- Two Hybrid HWR records have Footnote 29 and interval-order exceptions.
- The state benchmark file publishes category counts, not a state rate.
- National Rate is `Not Applicable` for EDAC and OP-36; DAX must leave the
  benchmark blank.

## Desktop validation still required

The repository validates table/column references, one-side key uniqueness,
relationship cardinality, no fact-to-fact paths, DAX-name uniqueness, and
unsafe summarization settings. Power BI Desktop must still validate refresh,
relationship activation, DAX syntax, formatting, and `BLANK()` rendering before
a PBIX can be called complete.
