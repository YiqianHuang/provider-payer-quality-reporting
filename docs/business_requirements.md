# Business Requirements

## Purpose

Build a reproducible, reviewable portfolio case study that demonstrates how
public CMS provider-quality results can be governed, modeled, validated, and
prepared for stakeholder reporting.

The project supports performance review and follow-up investigation. It does
not establish clinical causality, calculate patient-level outcomes, reproduce
formal HEDIS specifications, or represent a production deployment.

## Stakeholders and decisions

| Stakeholder | Decision supported | Required evidence |
|---|---|---|
| Hospital Quality Director | Identify measures or domains that warrant review | Official CMS result, comparison category, measurement period, suppression state |
| Clinical/Data Quality Analyst | Decide whether a result is safe to report | Source release, schema, grain, type, missingness, duplicate, footnote, and reconciliation checks |
| Operations leader | Prioritize questions for root-cause follow-up | Facility/state/national context with explicit interpretation limits |
| BI developer/reviewer | Reproduce the result and validate refresh behavior | Immutable source, SHA-256, transformation logic, SQL/DAX, and QA output |

## Active scope: Provider MVP

The Provider MVP includes:

- Hospital General Information;
- Unplanned Hospital Visits at hospital, state, and national levels;
- Hospital Readmissions Reduction Program (HRRP);
- Hospital Value-Based Purchasing (HVBP) Total Performance Score;
- source metadata and dictionary capture;
- immutable ingestion, profiling, source-to-target mapping, measure
  definitions, automated QA, provider data model, SQL reporting views, and a
  Power BI semantic-model contract and generated TMDL model item.

HCAHPS and HAI are deferred Provider extensions. They are not part of the first
raw snapshot.

## Explicitly out of scope until Provider QA passes

- Payer/Medicare Advantage Star Ratings;
- payer enrollment;
- synthetic member-level gap closure;
- dashboard pages or visual design;
- patient-level claims, EHR, or clinical-record analysis;
- independent reproduction of CMS risk adjustment;
- formal HEDIS, NCQA, or regulatory submission calculations.

## Functional requirements

| ID | Requirement | Acceptance evidence |
|---|---|---|
| BR-01 | Use only verified official CMS sources for the Provider MVP | Dataset metadata snapshots and official URLs in `source_inventory.md` |
| BR-02 | Preserve every raw release without overwrite | Date/dataset-partitioned raw paths and overwrite refusal in the downloader |
| BR-03 | Record release, modified, download, and measurement-period concepts separately | Manifest, source inventory, period profile |
| BR-04 | Preserve Facility ID as a string | String-only raw ingestion and Facility ID format QA |
| BR-05 | Preserve blanks, suppression text, and footnotes | Raw strings, suppression counts, footnote profiles, no zero imputation |
| BR-06 | Declare and validate one grain for every modeled fact | Candidate-grain QA before modeling; model-level uniqueness tests later |
| BR-07 | Document every reporting measure | Unit, direction, period, suppression rule, interpretation, and limit in `measure_dictionary.md` |
| BR-08 | Distinguish official fields from project-derived fields | Source-to-target mapping and semantic-model metadata |
| BR-09 | Reconcile source counts to downstream outputs | Manifest-to-profile checks now; Bronze/Silver/Gold/report reconciliation later |
| BR-10 | Make important findings reproducible | Official source, SQL/DAX, or QA evidence path beside each future result |

## Nonfunctional requirements

- Python and SQL workflows must be rerunnable from the repository.
- Raw snapshots and accepted schema baselines are immutable inputs.
- New releases must trigger schema, row-count, measure-set, period, and
  regression checks.
- A failed critical or high-severity check blocks progression.
- A review result requires written disposition; it cannot be silently promoted
  to pass.
- No project statement may imply CMS endorsement, production use, patient-level
  access, or clinical validation.

## Provider MVP acceptance gates

### Source gate

- all six required dataset IDs resolve through the CMS metadata API;
- CSV download URLs and the official hospital dictionary are accessible;
- source release/modified dates and local download timestamp are recorded.

### Ingestion gate

- all files have SHA-256, byte size, row count, and column count;
- raw files are stored as source-shaped CSVs;
- Facility ID values remain strings and retain leading zeros;
- suppression and footnote values remain unchanged.

### Profiling gate

- candidate source grain is unique and complete;
- exact duplicates, missingness, field types, date order, suppression,
  footnotes, and schema are checked;
- all critical/high failures are resolved or the phase remains blocked.

### Model/semantic gate

- each fact declares a release-aware period grain;
- official state/national comparison joins reconcile;
- missing/suppressed values remain blank in SQL and DAX;
- visible headline values can be independently recomputed.
