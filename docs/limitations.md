# Limitations and Interpretation Boundaries

## Data level and permitted claims

The project uses public CMS facility-, state-, national-, and program-level
aggregate results. It does not contain patient-level claims, EHR records, or
production clinical data. It cannot support member-level gap closure,
patient-level attribution, clinical appropriateness decisions, or causal
claims about why performance differs.

The project uses CMS-published results. It does not independently reproduce the
risk adjustment, confidence-interval methodology, sampling, or formal payment
calculations behind those results.

## HEDIS and regulatory boundary

No result in the Provider MVP is presented as a formal HEDIS calculation,
certified HEDIS reporting, an NCQA submission, or a CMS regulatory submission.
Restricted or paid technical specifications are not assumed. Any future
project-defined or synthetic measure must be labeled accordingly.

## Time and release comparability

- The initial six-file snapshot was released on 2026-05-13. A freshness audit
  on 2026-08-26 found a newer six-file catalog release dated 2026-08-13;
  the active snapshot is `data/raw/provider/2026-08-26/`.
- Current source modified dates range from 2026-01-26 to 2026-07-22.
- The official dictionary is the April 2026 release.
- Unplanned Hospital Visits contains five distinct measurement periods across
  its 14 measures in the current release, including changed 2022-2025 and
  2023-2025 windows.
- HRRP is an FY 2026 program file covering 2021-07-01 through 2024-06-30.
- HVBP TPS is keyed to Fiscal Year 2026 and does not include measurement
  start/end dates in the TPS file.
- Hospital General Information is release-versioned and does not publish one
  row-level measurement period. Its overall rating summarizes underlying
  measures with different periods.

Measures must not be combined, trended, or compared without first aligning the
relevant measurement-period and program-year semantics.

## Facility identifier boundary

Facility ID is a six-character source identifier and is always stored as a
string. In the General Information file, 5,268 unique identifiers are numeric
six-digit values and 164 are alternate federal VA/DoD identifiers ending in
`F`. Those alternate identifiers are valid source values but must not be
described as Medicare CCNs.

The Unplanned Hospital Visits file contains the same 164 alternate federal
identifiers across multiple measure rows. HRRP and HVBP coverage differs by
program; a nonmatch is not automatically an orphan-data defect.

The current program files contain facilities that are not present in the
current Hospital General Information release:

- HRRP: 20 distinct Facility IDs / 120 measure rows;
- HVBP TPS: 9 distinct Facility IDs / 9 program rows;
- combined union: 21 distinct facilities because eight IDs overlap.

The model preserves these as source-specific facility records with
`is_current_general_info_match = 0`; it does not drop the program facts or
invent missing facility attributes. The reason for each mismatch may involve
facility status or release timing, but that cause is not established by the
downloaded files and requires historical provider-reference research.

## Suppression and availability

Published files contain `Not Available`, `Not Applicable`,
`Too Few to Report`, `Number of Cases Too Small`, `N/A`, blanks, and numeric
footnote codes. These states are analytically different and are never converted
to zero.

The CMS footnote crosswalk includes, among others:

- 1: too few cases/patients to report;
- 5: results not available for the reporting period;
- 7: no cases met the measure criteria;
- 19: facility does not participate in the relevant IQR/OQR program;
- 28: results may be affected by an approved extraordinary-circumstances
  exception;
- 29: partial performance-period data due to an approved exception.

## Measure comparability

- Readmission rates and EDAC days have different units and cannot be averaged.
- EDAC can be negative, zero, or positive; lower is better.
- OP-36 is a ratio interpreted relative to one.
- HRRP Excess Readmission Ratio is an official program result and should not be
  replaced with a simple calculation from published counts.
- HVBP domain scores and TPS are program scores, not readmission rates.
- State and national files have different shapes: the state file publishes
  counts by comparison category, while the national file also publishes a
  national rate when applicable.
- Peer benchmarks created later are project-derived and must remain separate
  from official CMS comparisons.

Two `Hybrid_HWR` rows in the 2026-05-13 release had a published Score below
their published Lower Estimate. Both carry Footnote 29, which CMS defines as
partial performance-period data due to an approved exception. The model
preserves the raw values, excludes those two rows from the generic
lower-score-upper ordering assertion, and publishes them in
`outputs/provider_model/2026-07-29/interval_order_exceptions.csv`. The active
2026-08-13 release has no such interval exceptions. This is a comparability
warning, not permission to replace or recalculate the values.

## Licensing and endorsement

The CMS Hospital Downloadable Database Data Dictionary states that the public
reporting data are works of the U.S. government and are in the public domain;
permission is not required for reuse, and attribution is appreciated. Project
materials must not imply CMS or U.S. government endorsement.
