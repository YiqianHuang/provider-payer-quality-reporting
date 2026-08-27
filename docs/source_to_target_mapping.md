# Source-to-Target Mapping

## Mapping rules

1. Bronze tables preserve every source column as text and add only lineage
   fields: `source_dataset_id`, `source_release_id`, `source_file_name`,
   `source_row_number`, and `ingested_at`.
2. Facility ID is a six-character string. Numeric CCNs and alternate federal
   VA/DoD identifiers are not conflated.
3. Silver tables retain both raw and typed representations for scores and
   dates. A failed numeric parse never becomes zero.
4. Suppression text, footnote codes, comparison categories, and period fields
   remain separate attributes.
5. Gold facts include `source_release_id` in their unique grain.

## Hospital General Information (`xubh-q36u`)

Target grain: one `dim_facility_version` row per Facility ID and source release.

| Source field(s) | Silver/Gold target | Type / rule |
|---|---|---|
| Facility ID | `facility_id` | `varchar(6)`; trim only; preserve leading zero and `F` suffix |
| Facility Name | `facility_name` | text |
| Address | `address_line_1` | text |
| City/Town | `city` | text |
| State | `state_code` | `char(2)` |
| ZIP Code | `zip_code_raw`, `zip_code` | source text retained; normalized display value is string |
| County/Parish | `county_name` | text |
| Telephone Number | `telephone_number` | string; not numeric |
| Hospital Type | `hospital_type` | controlled source text |
| Hospital Ownership | `hospital_ownership` | controlled source text |
| Emergency Services | `has_emergency_services_raw`, `has_emergency_services` | raw text plus nullable boolean |
| Meets criteria for birthing friendly designation | `birthing_friendly_raw`, `birthing_friendly_flag` | blank remains unknown/not published |
| Hospital overall rating | `overall_rating_raw`, `overall_rating_numeric` | 1-5 when reportable; `Not Available` -> null |
| Hospital overall rating footnote | `overall_rating_footnote_code` | preserve source code |
| MORT Group Measure Count; Count of Facility MORT Measures; Count of MORT Measures Better/No Different/Worse | `mort_*_raw`, typed count fields | numeric only when reportable |
| MORT Group Footnote | `mort_group_footnote_code` | preserve source code |
| Safety Group Measure Count; Count of Facility Safety Measures; Count of Safety Measures Better/No Different/Worse | `safety_*_raw`, typed count fields | numeric only when reportable |
| Safety Group Footnote | `safety_group_footnote_code` | preserve source code |
| READM Group Measure Count; Count of Facility READM Measures; Count of READM Measures Better/No Different/Worse | `readm_*_raw`, typed count fields | numeric only when reportable |
| READM Group Footnote | `readm_group_footnote_code` | preserve source code |
| Pt Exp Group Measure Count; Count of Facility Pt Exp Measures | `patient_experience_*_raw`, typed count fields | numeric only when reportable |
| Pt Exp Group Footnote | `patient_experience_footnote_code` | preserve source code |
| TE Group Measure Count; Count of Facility TE Measures | `timely_effective_*_raw`, typed count fields | numeric only when reportable |
| TE Group Footnote | `timely_effective_footnote_code` | preserve source code |

The overall rating is kept on the release-versioned facility record for this
MVP, but it is not treated as an invariant facility attribute.

HRRP/HVBP Facility IDs absent from the current General Information release are
added as source-specific facility versions using only the name, state, and
address attributes actually available in the program source. They are marked
`is_current_general_info_match = 0` and retain the program dataset's
`source_release_key`.

## Unplanned Hospital Visits - Hospital (`632h-zaca`)

Target:
`fact_provider_measure`; grain is Facility ID × Measure ID × Start Date × End
Date × source release.

| Source field | Target | Type / rule |
|---|---|---|
| Facility ID | `facility_id` | string foreign key to the matching facility release |
| Facility Name | Bronze audit field | do not use as a join key |
| Address, City/Town, State, ZIP Code, County/Parish, Telephone Number | Bronze audit fields | facility attributes come from `dim_facility_version`; compare for drift |
| Measure ID | `measure_id` | string foreign key to `dim_measure_version` |
| Measure Name | `measure_name_source` | retain for label reconciliation |
| Compared to National | `comparison_category_raw`, `comparison_category` | controlled source text; preserve capitalization variants before standardization |
| Denominator | `denominator_raw`, `denominator_numeric` | null when unavailable/suppressed |
| Score | `score_raw`, `score_numeric` | measure-specific unit; no cross-measure summation |
| Lower Estimate | `lower_estimate_raw`, `lower_estimate_numeric` | nullable numeric |
| Higher Estimate | `upper_estimate_raw`, `upper_estimate_numeric` | source label normalized from “Higher” to semantic “upper” |
| Number of Patients | `patient_count_raw`, `patient_count` | aggregate count; does not create patient-level data |
| Number of Patients Returned | `patients_returned_raw`, `patients_returned` | aggregate count |
| Footnote | `footnote_code_raw` | preserve comma-separated codes |
| Start Date | `measurement_start_date` | strict `%m/%d/%Y` parse |
| End Date | `measurement_end_date` | strict `%m/%d/%Y` parse |
| Derived from raw fields | `is_reportable`, `is_suppressed`, `suppression_reason` | explicit mapping; never infer zero |

For the accepted release, two `Hybrid_HWR` records with Footnote 29 are
preserved as explicit interval-order exceptions. Raw Score, Lower Estimate,
Higher Estimate, comparison category, and footnote remain unchanged.

## Unplanned Hospital Visits - State (`4gkm-5ypv`)

Target:
`fact_provider_state_benchmark`; grain is State × Measure ID × Start Date × End
Date × source release.

| Source field(s) | Target | Type / rule |
|---|---|---|
| State | `state_code` | `char(2)` |
| Measure ID, Measure Name | `measure_id`, `measure_name_source` | join by ID and version |
| Number of Hospitals Worse/Same/Better/Too Few | `hospital_count_worse/same/better/too_few_raw` plus typed counts | comparison-category count family |
| Number of Hospitals Fewer/Average/More/Too Small | `hospital_count_fewer/average/more/too_small_raw` plus typed counts | EDAC/category count family |
| Footnote | `footnote_code_raw` | preserve |
| Start Date, End Date | measurement dates | strict date parse |

This source does not publish a state rate in the current schema. It provides
official state context through counts by CMS comparison category.

## Unplanned Hospital Visits - National (`cvcs-xecj`)

Target:
`fact_provider_national_benchmark`; grain is Measure ID × Start Date × End Date
× source release.

| Source field(s) | Target | Type / rule |
|---|---|---|
| Measure ID, Measure Name | `measure_id`, `measure_name_source` | official measure version |
| National Rate | `national_rate_raw`, `national_rate_numeric` | null when `Not Applicable`; unit comes from measure dictionary |
| Number of Hospitals Worse/Same/Better/Too Few | official national category counts | typed only when reportable |
| Number of Hospitals Fewer/Average/More/Too Small | official EDAC/category counts | typed only when reportable |
| Footnote | `footnote_code_raw` | column retained even when blank |
| Start Date, End Date | measurement dates | strict date parse |

## Hospital Readmissions Reduction Program (`9n3s-kdb3`)

Target:
`fact_provider_hrrp_measure`; grain is Facility ID × Measure Name × Start Date ×
End Date × FY 2026 × source release.

| Source field | Target | Type / rule |
|---|---|---|
| Facility Name | Bronze audit field | label only |
| Facility ID | `facility_id` | six-character string |
| State | `state_code_source` | reconciliation attribute |
| Measure Name | `measure_id` | source value is the HRRP measure identifier |
| Number of Discharges | `discharge_count_raw`, `discharge_count` | aggregate count |
| Footnote | `footnote_code_raw` | preserve |
| Excess Readmission Ratio | `excess_readmission_ratio_raw`, typed numeric | official published result; do not recompute |
| Predicted Readmission Rate | `predicted_readmission_rate_raw`, typed numeric | published percent scale |
| Expected Readmission Rate | `expected_readmission_rate_raw`, typed numeric | published percent scale |
| Number of Readmissions | `readmission_count_raw`, typed count | aggregate count |
| Start Date, End Date | measurement dates | strict date parse |
| Official file name | `fiscal_year` | derive 2026 with lineage; validate against source inventory |

## HVBP Total Performance Score (`ypbt-wvdk`)

Target:
`fact_provider_program_score`; grain is Facility ID × Fiscal Year × program ×
source release.

| Source field | Target | Type / rule |
|---|---|---|
| Fiscal Year | `fiscal_year` | integer; part of grain |
| Facility ID | `facility_id` | string; part of grain |
| Facility Name, Address, City/Town, State, ZIP Code, County/Parish | Bronze audit fields | reconcile with facility version; do not duplicate into fact presentation layer |
| Unweighted Normalized Clinical Outcomes Domain Score | `clinical_outcomes_unweighted_raw`, typed score | `Not Available` -> null |
| Weighted Normalized Clinical Outcomes Domain Score | `clinical_outcomes_weighted_raw`, typed score | `Not Available` -> null |
| Unweighted Person And Community Engagement Domain Score | `engagement_unweighted_raw`, typed score | `Not Available` -> null |
| Weighted Person And Community Engagement Domain Score | `engagement_weighted_raw`, typed score | `Not Available` -> null |
| Unweighted Normalized Safety Domain Score | `safety_unweighted_raw`, typed score | `Not Available` -> null |
| Weighted Safety Domain Score | `safety_weighted_raw`, typed score | `Not Available` -> null |
| Unweighted Normalized Efficiency And Cost Reduction Domain Score | `efficiency_unweighted_raw`, typed score | `Not Available` -> null |
| Weighted Efficiency And Cost Reduction Domain Score | `efficiency_weighted_raw`, typed score | `Not Available` -> null |
| Total Performance Score | `total_performance_score_raw`, typed score | official TPS |

The official TPS file has no Footnote, measurement-start, or measurement-end
column. That absence is recorded; no field is fabricated.
