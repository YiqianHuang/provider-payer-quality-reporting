# Provider Measure Dictionary

Period note: the measure metadata is release-aware. The initial 2026-05-13
snapshot used the periods listed in the original tables; the active
2026-08-13 CMS release has updated Unplanned Hospital Visits periods. The
current row-level periods are recorded in
`outputs/provider_phase1/2026-08-26/measure_catalog.csv` and the model's
`dim_reporting_period`/`dim_measure` tables. Do not infer a period from the
catalog release date.

All entries below are **official published CMS results or fields**. The project
does not independently calculate the underlying risk adjustment or formal
program result.

## Suppression-rule codes used in this document

- **G** - General Information: `Not Available` and the applicable published
  overall/group footnote fields.
- **U** - Unplanned Visits: published text such as `Not Available`,
  `Not Applicable`, `Number of Cases Too Small`, plus Footnote Crosswalk codes
  including 1, 5, 7, 19, 28, and 29.
- **H** - HRRP: `N/A`, `Too Few to Report`, and the published footnote code.
- **V** - HVBP TPS: `Not Available`; this file does not publish a Footnote
  column.

For every rule, suppressed/unavailable values remain null/blank and never
become zero.

## Shared interpretation-limit codes

- **L1** - Facility-level public aggregate; no patient-level, causal, or
  clinical-appropriateness inference.
- **L2** - Do not average with measures having a different unit, direction, or
  measurement period.
- **L3** - Use the CMS-published risk-standardized result; do not substitute a
  simple rate calculated from aggregate counts.
- **L4** - Program score is specific to its fiscal year and program rules; it
  is not a readmission rate or a general clinical outcome.

## Facility summary

| Measure key | Name | Unit | Direction | Period | Suppression | Permitted interpretation | Limit |
|---|---|---|---|---|---|---|---|
| `OVERALL_HOSPITAL_RATING` | Overall Hospital Rating | 1-5 stars | Higher is better | Release 2026-05-13; underlying measure periods vary | G | Published CMS summary rating for facility comparison | L1, L2; do not infer one common service period |

## Unplanned Hospital Visits

| Measure ID | Official source name | Unit | Direction | Measurement period | Suppression | Permitted interpretation | Limit |
|---|---|---|---|---|---|---|---|
| `EDAC_30_AMI` | Hospital return days for heart attack patients | Days per 100 discharges; may be negative | Lower is better | 2021-07-01 to 2024-06-30 | U | Negative means fewer return days than expected for similar case mix; zero means as expected | L1-L3 |
| `EDAC_30_HF` | Hospital return days for heart failure patients | Days per 100 discharges; may be negative | Lower is better | 2021-07-01 to 2024-06-30 | U | Same EDAC interpretation as above | L1-L3 |
| `EDAC_30_PN` | Hospital return days for pneumonia patients | Days per 100 discharges; may be negative | Lower is better | 2021-07-01 to 2024-06-30 | U | Same EDAC interpretation as above | L1-L3 |
| `Hybrid_HWR` | Hybrid Hospital-Wide All-Cause Readmission Measure | Percent rate | Lower is better | 2023-07-01 to 2024-06-30 | U | Published hospital-wide readmission rate and comparison context | L1-L3; hybrid reporting methodology applies |
| `OP_32` | Rate of unplanned hospital visits after colonoscopy | Risk-standardized visits per 1,000 colonoscopies | Lower is better | 2022-01-01 to 2024-12-31 | U | Compare with the official national rate when reportable | L1-L3 |
| `OP_35_ADM` | Inpatient admissions for outpatient chemotherapy patients | Risk-standardized admissions per 100 chemotherapy patients | Lower is better | 2024-01-01 to 2024-12-31 | U | Compare with the official national rate when reportable | L1-L3 |
| `OP_35_ED` | ED visits for outpatient chemotherapy patients | Risk-standardized ED visits per 100 chemotherapy patients | Lower is better | 2024-01-01 to 2024-12-31 | U | Compare with the official national rate when reportable | L1-L3 |
| `OP_36` | Unplanned hospital visits after outpatient surgery | Risk-standardized ratio; 1 is expected | Lower is better | 2024-01-01 to 2024-12-31 | U | Below/near/above 1 supports better/no-different/worse-than-expected context | L1-L3 |
| `READM_30_AMI` | AMI 30-day readmission rate | Percent | Lower is better | 2021-07-01 to 2024-06-30 | U | Published risk-standardized 30-day readmission result | L1-L3 |
| `READM_30_CABG` | CABG readmission rate | Percent | Lower is better | 2021-07-01 to 2024-06-30 | U | Published risk-standardized 30-day readmission result | L1-L3 |
| `READM_30_COPD` | COPD 30-day readmission rate | Percent | Lower is better | 2021-07-01 to 2024-06-30 | U | Published risk-standardized 30-day readmission result | L1-L3 |
| `READM_30_HF` | Heart failure 30-day readmission rate | Percent | Lower is better | 2021-07-01 to 2024-06-30 | U | Published risk-standardized 30-day readmission result | L1-L3 |
| `READM_30_HIP_KNEE` | Hip/knee replacement readmission rate | Percent | Lower is better | 2021-07-01 to 2024-06-30 | U | Published risk-standardized 30-day readmission result | L1-L3 |
| `READM_30_PN` | Pneumonia 30-day readmission rate | Percent | Lower is better | 2021-07-01 to 2024-06-30 | U | Published risk-standardized 30-day readmission result | L1-L3 |

The state source supplies counts by CMS comparison category. The national
source supplies a National Rate when applicable. `Not Applicable` national
rates for EDAC and OP-36 are not zeros.

## Hospital Readmissions Reduction Program

Each row below represents the official published **Excess Readmission Ratio**.
The same source also publishes predicted rate, expected rate, discharge count,
and readmission count as separate fields.

| Measure ID | Condition/procedure | Unit | Direction | Measurement/program period | Suppression | Permitted interpretation | Limit |
|---|---|---|---|---|---|---|---|
| `READM-30-AMI-HRRP` | AMI | Ratio: predicted / expected | Lower is better | 2021-07-01 to 2024-06-30; FY 2026 | H | Ratio above 1 indicates predicted readmissions exceed the expected result for similar patients | L1-L3; payment implications require official HRRP rules |
| `READM-30-CABG-HRRP` | CABG | Ratio: predicted / expected | Lower is better | 2021-07-01 to 2024-06-30; FY 2026 | H | Same ratio interpretation | L1-L3 |
| `READM-30-COPD-HRRP` | COPD | Ratio: predicted / expected | Lower is better | 2021-07-01 to 2024-06-30; FY 2026 | H | Same ratio interpretation | L1-L3 |
| `READM-30-HF-HRRP` | Heart failure | Ratio: predicted / expected | Lower is better | 2021-07-01 to 2024-06-30; FY 2026 | H | Same ratio interpretation | L1-L3 |
| `READM-30-HIP-KNEE-HRRP` | Hip/knee replacement | Ratio: predicted / expected | Lower is better | 2021-07-01 to 2024-06-30; FY 2026 | H | Same ratio interpretation | L1-L3 |
| `READM-30-PN-HRRP` | Pneumonia | Ratio: predicted / expected | Lower is better | 2021-07-01 to 2024-06-30; FY 2026 | H | Same ratio interpretation | L1-L3 |

## Hospital Value-Based Purchasing - Total Performance Score file

| Measure key | Name | Unit | Direction | Period | Suppression | Permitted interpretation | Limit |
|---|---|---|---|---|---|---|---|
| `HVBP_CLINICAL_UNWEIGHTED` | Unweighted Normalized Clinical Outcomes Domain Score | Score | Higher is better | FY 2026 | V | Official unweighted normalized domain score | L1, L2, L4 |
| `HVBP_CLINICAL_WEIGHTED` | Weighted Normalized Clinical Outcomes Domain Score | Score | Higher is better | FY 2026 | V | Official weighted domain contribution | L1, L2, L4 |
| `HVBP_ENGAGEMENT_UNWEIGHTED` | Unweighted Person and Community Engagement Domain Score | Score | Higher is better | FY 2026 | V | Official unweighted normalized domain score | L1, L2, L4 |
| `HVBP_ENGAGEMENT_WEIGHTED` | Weighted Person and Community Engagement Domain Score | Score | Higher is better | FY 2026 | V | Official weighted domain contribution | L1, L2, L4 |
| `HVBP_SAFETY_UNWEIGHTED` | Unweighted Normalized Safety Domain Score | Score | Higher is better | FY 2026 | V | Official unweighted normalized domain score | L1, L2, L4 |
| `HVBP_SAFETY_WEIGHTED` | Weighted Safety Domain Score | Score | Higher is better | FY 2026 | V | Official weighted domain contribution | L1, L2, L4 |
| `HVBP_EFFICIENCY_UNWEIGHTED` | Unweighted Normalized Efficiency and Cost Reduction Domain Score | Score | Higher is better | FY 2026 | V | Official unweighted normalized domain score | L1, L2, L4 |
| `HVBP_EFFICIENCY_WEIGHTED` | Weighted Efficiency and Cost Reduction Domain Score | Score | Higher is better | FY 2026 | V | Official weighted domain contribution | L1, L2, L4 |
| `HVBP_TPS` | Total Performance Score | Score | Higher is better | FY 2026 | V | Official CMS hospital-level TPS | L1, L2, L4; do not reverse-engineer payment adjustment from this file alone |

## Source provenance

Definitions and units come from the April 2026 CMS Hospital Downloadable
Database Data Dictionary, including its measure descriptions, measure dates,
file schemas, Appendix A measure list, and Appendix E footnote crosswalk.
Observed measurement periods are reconciled to the downloaded CSVs in
`outputs/provider_phase1/2026-08-26/measurement_periods.csv`.
