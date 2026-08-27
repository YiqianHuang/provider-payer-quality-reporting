# Power BI workstream

The Provider Phase 1 and Phase 2 QA gates have passed. The semantic-model
contract is implemented and headlessly validated. No dashboard pages have
been created.

Artifacts:

- `model_spec.md`;
- `dax_measures.md`;
- `semantic_model.json`;
- `ProviderQuality.SemanticModel/definition.pbism`;
- `ProviderQuality.SemanticModel/definition/*.tmdl`;
- `../outputs/powerbi/semantic_model_validation.json`;
- `../outputs/powerbi/semantic_model_validation.md`;
- `../outputs/powerbi/tmdl_validation.json`.

The model tables are exported from the validated SQLite database to
`../data/processed/powerbi_import/`, and the TMDL partitions import those typed
CSV extracts. This avoids an additional SQLite ODBC dependency.

The generated TMDL was serialized and deserialized through the Tabular Object
Model assembly shipped with the installed Power BI Desktop version. A Desktop
processing pass and visual relationship/blank-behavior inspection still
remain; that environment-dependent step is not represented as complete by the
round-trip validator.

Rebuild the Power BI assets after rebuilding the relational model:

```powershell
python -m src.powerbi.export_powerbi_tables --project-root .

powershell.exe -NoProfile -ExecutionPolicy Bypass `
  -File src\powerbi\build_tmdl_semantic_model.ps1 `
  -ProjectRoot .
```
