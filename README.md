# US Healthcare Quality Performance Reporting

This repository is a portfolio case study built from public, aggregate CMS
quality-reporting data. It is not a production hospital or health-plan system,
does not contain patient-level claims or EHR records, and does not represent
formal HEDIS calculation or reporting.

## Current scope

The active workstream is the **Provider MVP**:

1. verify CMS source metadata and definitions;
2. preserve immutable raw snapshots and hashes;
3. profile schema, grain, missingness, duplicates, suppression, footnotes, and
   measurement periods;
4. build validated provider reporting models and SQL views;
5. specify a Power BI semantic model only after the source QA gate passes.

Payer and synthetic gap-closure work are out of scope until the Provider MVP
passes its documented QA gates. No dashboard is being built during source
verification and ingestion.

## Project controls

- [Business requirements](docs/business_requirements.md)
- [Provider MVP implementation plan](docs/provider_mvp_implementation_plan.md)
- [Source inventory](docs/source_inventory.md)
- [Source-to-target mapping](docs/source_to_target_mapping.md)
- [Measure dictionary](docs/measure_dictionary.md)
- [Data quality plan](docs/data_quality_plan.md)
- [Limitations](docs/limitations.md)
- [Raw data handling](data/README.md)
- [Provider model QA report](outputs/provider_model/2026-08-26/model_qa_report.md)
- [Power BI semantic-model specification](powerbi/model_spec.md)
- [Power BI semantic-model validation](outputs/powerbi/semantic_model_validation.md)
- [Provider MVP validation report](docs/provider_mvp_validation_report.md)
- [CMS freshness check](outputs/provider_freshness/2026-08-26/freshness_check.md)
- [Post-refresh CMS freshness check](outputs/provider_freshness/2026-08-26_post_snapshot/freshness_check.md)

The project charter and highest-priority execution standard is
`Provider_Payer_Quality_Reporting_Project_Starter.md`.

## Reproducible outputs

- Initial raw snapshot: `data/raw/provider/2026-07-29/`
- Current accepted raw snapshot: `data/raw/provider/2026-08-26/`
- Source profiling: `outputs/provider_phase1/2026-08-26/`
- Provider relational model: `data/processed/provider_quality.sqlite`
- Model QA: `outputs/provider_model/2026-08-26/`
- Semantic-model contract, generated TMDL model item, and validation:
  `powerbi/` and `outputs/powerbi/`

Power BI Desktop is installed locally. SQLite is the reproducible evidence
store; typed CSV extracts provide a driver-free import layer for the generated
TMDL semantic model. The contract has passed headless schema, relationship,
aggregation, DAX-reference, and TMDL round-trip validation. A Desktop
processing/inspection pass is still pending; no dashboard pages have been
created.
