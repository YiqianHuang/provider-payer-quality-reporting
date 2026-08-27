# Source Inventory

Inventory date: **2026-08-26**

The authoritative local manifest is
`data/raw/provider/2026-08-26/provider_snapshot_manifest.json`.
All row counts exclude the CSV header. All file sizes are bytes.

## Current accepted snapshot after freshness check

The 2026-08-26 freshness audit detected a new CMS catalog release. The active
snapshot is now `data/raw/provider/2026-08-26/`, released by CMS on
2026-08-13. The earlier 2026-07-29 snapshot remains immutable and is retained
for release comparison.

| Dataset ID | Modified | Released | Rows | Columns | Bytes | SHA-256 |
|---|---|---|---:|---:|---:|---|
| `xubh-q36u` | 2026-07-22 | 2026-08-13 | 5,419 | 38 | 1,450,767 | `f874f09fef895a1ccf5bb7392dcbb2be05c9860339261b093fe00f0c1b013480` |
| `632h-zaca` | 2026-07-22 | 2026-08-13 | 67,060 | 20 | 19,048,784 | `a3e64029ea6daea1f7de163e5b5054b918d0c8be986fccfc47c7a8d5b29a6d1d` |
| `4gkm-5ypv` | 2026-07-22 | 2026-08-13 | 784 | 14 | 135,088 | `b3ac4695472df9847c032bccce2fd56db6bc65dcdcc9ac77aaf0aa25b9384f22` |
| `cvcs-xecj` | 2026-07-22 | 2026-08-13 | 14 | 14 | 2,814 | `44e39aedc296f00fa8477a3485a66012cbfcdefb173435199a0b03343c9402c3` |
| `9n3s-kdb3` | 2026-01-26 | 2026-08-13 | 18,330 | 12 | 2,068,464 | `7e7915dd2751a1e59ac46dbc9194fb781e820962a04d47c31344ea2bb30c91f6` |
| `ypbt-wvdk` | 2026-01-26 | 2026-08-13 | 2,455 | 17 | 568,036 | `68263e795e5cd228b63e9632f50b1613e409f3ff20d85fd0c114aed4085ee103` |

Current snapshot total: **94,062 rows, 23,273,953 CSV bytes**.

The current Unplanned Hospital Visits periods are captured in
`outputs/provider_phase1/2026-08-26/measurement_periods.csv`; they shifted from
the prior release, so period alignment must be release-aware.

## Initial Provider MVP raw snapshot (2026-07-29)

| CMS dataset | Dataset ID | Issued | Modified | Released | Downloaded | Measurement period / program period | Rows | Columns | Bytes | SHA-256 |
|---|---|---|---|---|---|---|---:|---:|---:|---|
| [Hospital General Information](https://data.cms.gov/provider-data/dataset/xubh-q36u) | `xubh-q36u` | 2025-01-08 | 2026-04-28 | 2026-05-13 | 2026-07-29 | Release-versioned facility dimension; no row-level measurement dates | 5,432 | 38 | 1,453,884 | `83c98b2e8687580e0482b13e1e9acd5813534be243e5ccd9f55556a869595d40` |
| [Unplanned Hospital Visits - Hospital](https://data.cms.gov/provider-data/dataset/632h-zaca) | `632h-zaca` | 2023-07-05 | 2026-04-28 | 2026-05-13 | 2026-07-29 | Four measure-specific periods; see below | 67,088 | 20 | 19,035,194 | `6f8f59fed5a56e78868d8a4d73f1a78341168cc07f3536b72be952f35c76751d` |
| [Unplanned Hospital Visits - State](https://data.cms.gov/provider-data/dataset/4gkm-5ypv) | `4gkm-5ypv` | 2020-12-10 | 2026-04-21 | 2026-05-13 | 2026-07-29 | Same four measure-specific periods | 784 | 14 | 132,702 | `09ac5d707205c1f61bedb7b017c7de693222cda79a2f3b2fe81b0b8d623a9523` |
| [Unplanned Hospital Visits - National](https://data.cms.gov/provider-data/dataset/cvcs-xecj) | `cvcs-xecj` | 2020-12-10 | 2026-04-21 | 2026-05-13 | 2026-07-29 | Same four measure-specific periods | 14 | 14 | 2,770 | `0167c70db38f9449f798fedbecbd2918446063df5c7a58d715713b3fa6be14f6` |
| [Hospital Readmissions Reduction Program](https://data.cms.gov/provider-data/dataset/9n3s-kdb3) | `9n3s-kdb3` | 2020-12-10 | 2026-01-26 | 2026-05-13 | 2026-07-29 | 2021-07-01 through 2024-06-30; FY 2026 program file | 18,330 | 12 | 2,068,464 | `7e7915dd2751a1e59ac46dbc9194fb781e820962a04d47c31344ea2bb30c91f6` |
| [HVBP - Total Performance Score](https://data.cms.gov/provider-data/dataset/ypbt-wvdk) | `ypbt-wvdk` | 2023-07-05 | 2026-01-26 | 2026-05-13 | 2026-07-29 | Fiscal Year 2026; no start/end dates in this file | 2,455 | 17 | 568,036 | `68263e795e5cd228b63e9632f50b1613e409f3ff20d85fd0c114aed4085ee103` |

Snapshot total: **6 files, 94,103 source rows, 23,261,050 CSV
bytes**.

## Observed Unplanned Hospital Visits periods

| Measures | Start | End | Reporting-cycle context |
|---|---|---|---|
| `EDAC_30_AMI`, `EDAC_30_HF`, `EDAC_30_PN`, six `READM_30_*` measures | 2021-07-01 | 2024-06-30 | 36-month condition/procedure measures |
| `Hybrid_HWR` | 2023-07-01 | 2024-06-30 | One-year hybrid hospital-wide readmission period in this release |
| `OP_32` | 2022-01-01 | 2024-12-31 | 36-month outpatient colonoscopy measure |
| `OP_35_ADM`, `OP_35_ED`, `OP_36` | 2024-01-01 | 2024-12-31 | 12-month chemotherapy/surgery measures |

These dates are read from the CSVs and agree with the April 2026 data
dictionary. They must not be replaced by the 2026 catalog release year.

## Raw file locations and candidate source grains

| Dataset ID | Local raw file | Candidate grain |
|---|---|---|
| `xubh-q36u` | `data/raw/provider/2026-07-29/xubh-q36u/Hospital_General_Information.csv` | Facility ID |
| `632h-zaca` | `data/raw/provider/2026-07-29/632h-zaca/Unplanned_Hospital_Visits-Hospital.csv` | Facility ID × Measure ID × Start Date × End Date |
| `4gkm-5ypv` | `data/raw/provider/2026-07-29/4gkm-5ypv/Unplanned_Hospital_Visits-State.csv` | State × Measure ID × Start Date × End Date |
| `cvcs-xecj` | `data/raw/provider/2026-07-29/cvcs-xecj/Unplanned_Hospital_Visits-National.csv` | Measure ID × Start Date × End Date |
| `9n3s-kdb3` | `data/raw/provider/2026-07-29/9n3s-kdb3/FY_2026_Hospital_Readmissions_Reduction_Program_Hospital.csv` | Facility ID × Measure Name × Start Date × End Date |
| `ypbt-wvdk` | `data/raw/provider/2026-07-29/ypbt-wvdk/hvbp_tps.csv` | Facility ID × Fiscal Year |

All six candidate grains were complete and unique in the downloaded snapshot.
Final fact grains also include `source_release_id`.

## Official dictionary

- Title: Hospital Downloadable Database Data Dictionary
- Document release: April 2026
- Official URL:
  [HOSPITAL_Data_Dictionary.pdf](https://data.cms.gov/provider-data/sites/default/files/data_dictionaries/hospital/HOSPITAL_Data_Dictionary.pdf)
- Local file:
  `data/reference/HOSPITAL_Data_Dictionary_April_2026.pdf`
- Downloaded: 2026-07-29
- Size: 1,291,356 bytes
- SHA-256:
  `cd5016abee26e914b273a8fea8ab698710ff60f1c53a1b66e43bbd7168f6cb81`

The dictionary is 105 pages and identifies itself as the April 2026 release.
It documents the file schemas, reporting cycles, measure dates, measure list,
and public-reporting footnote crosswalk.

## CMS API and direct distributions

Catalog metadata was retrieved from:

`https://data.cms.gov/provider-data/api/1/metastore/schemas/dataset/items/<dataset-id>`

The exact direct CSV URL returned for each dataset is stored in its
`catalog_metadata.json` and in the provider snapshot manifest. The catalog
landing pages require JavaScript, but the metadata and CSV endpoints are
publicly accessible without authentication.

## Deferred Provider sources

The following valid Provider sources remain deferred and were not downloaded
in this snapshot:

- [Patient Survey (HCAHPS) - Hospital](https://data.cms.gov/provider-data/dataset/dgck-syfz),
  dataset `dgck-syfz`;
- [Healthcare Associated Infections - Hospital](https://data.cms.gov/provider-data/dataset/77hc-ibv8),
  dataset `77hc-ibv8`.

They may be added only after the current Provider core model passes its QA
gate. Payer sources are intentionally not inventoried as active inputs in this
Provider-only phase.

## Licensing

The official dictionary states that CMS Hospital Quality Initiative public
reporting data are public domain U.S. government works. Permission is not
required for reuse; attribution is appreciated. Reuse must not imply government
endorsement.
