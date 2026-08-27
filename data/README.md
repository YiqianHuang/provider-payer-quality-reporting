# Data handling

## Raw snapshots

`data/raw/provider/YYYY-MM-DD/<dataset-id>/` contains source-shaped CMS files,
the catalog metadata captured at download time, and no transformed values.
Existing raw files must not be overwritten. A new CMS refresh receives a new
snapshot date and source-release record.

Raw CSV values are first read as strings. This preserves Facility ID/CCN
leading zeros and keeps suppression text such as `Not Available` and
`Too Few to Report` distinct from numeric zero.

## Reference files

`data/reference/` stores official dictionaries or other public technical
references used to interpret the downloaded datasets. Each downloaded
reference is hashed and identified in the source manifest.

## Payer data

`data/raw/payer/` is reserved. It must remain empty until the Provider MVP QA
gate has passed and the Payer phase is explicitly opened by the project plan.

