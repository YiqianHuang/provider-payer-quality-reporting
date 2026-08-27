# Power BI Semantic Model Validation

- Model: `Provider Quality Performance`
- Version: `0.1.0`
- Status counts: `{"PASS": 106}`

| Check | Status | Severity | Details |
|---|---|---|---|
| unique_table_names | PASS | Critical | All semantic table names are unique. |
| source_columns_Dim Facility | PASS | Critical | Source object dim_facility; missing columns: [] |
| source_columns_Dim Geography | PASS | Critical | Source object dim_geography; missing columns: [] |
| source_columns_Dim Measure | PASS | Critical | Source object dim_measure; missing columns: [] |
| source_columns_Dim Reporting Period | PASS | Critical | Source object dim_reporting_period; missing columns: [] |
| source_columns_Dim Source Release | PASS | Critical | Source object dim_source_release; missing columns: [] |
| source_columns_Fact Provider Measure | PASS | Critical | Source object fact_provider_measure; missing columns: [] |
| source_columns_Fact State Benchmark | PASS | Critical | Source object fact_provider_state_benchmark; missing columns: [] |
| source_columns_Fact National Benchmark | PASS | Critical | Source object fact_provider_national_benchmark; missing columns: [] |
| source_columns_Fact HRRP | PASS | Critical | Source object fact_provider_hrrp_measure; missing columns: [] |
| source_columns_Fact HVBP | PASS | Critical | Source object fact_provider_program_score; missing columns: [] |
| source_columns_Fact Quality Check | PASS | Critical | Source object fact_quality_check; missing columns: [] |
| relationship_references_Geography to Facility | PASS | Critical | Relationship table and column references resolve. |
| no_fact_to_fact_Geography to Facility | PASS | Critical | Relationship is dimension-to-dimension or dimension-to-fact. |
| single_direction_Geography to Facility | PASS | High | Relationship uses single-direction filtering. |
| one_side_unique_Geography to Facility | PASS | Critical | One-side rows=56; distinct keys=56. |
| relationship_references_Facility to Provider Measure | PASS | Critical | Relationship table and column references resolve. |
| no_fact_to_fact_Facility to Provider Measure | PASS | Critical | Relationship is dimension-to-dimension or dimension-to-fact. |
| single_direction_Facility to Provider Measure | PASS | High | Relationship uses single-direction filtering. |
| one_side_unique_Facility to Provider Measure | PASS | Critical | One-side rows=5440; distinct keys=5440. |
| relationship_references_Facility to HRRP | PASS | Critical | Relationship table and column references resolve. |
| no_fact_to_fact_Facility to HRRP | PASS | Critical | Relationship is dimension-to-dimension or dimension-to-fact. |
| single_direction_Facility to HRRP | PASS | High | Relationship uses single-direction filtering. |
| one_side_unique_Facility to HRRP | PASS | Critical | One-side rows=5440; distinct keys=5440. |
| relationship_references_Facility to HVBP | PASS | Critical | Relationship table and column references resolve. |
| no_fact_to_fact_Facility to HVBP | PASS | Critical | Relationship is dimension-to-dimension or dimension-to-fact. |
| single_direction_Facility to HVBP | PASS | High | Relationship uses single-direction filtering. |
| one_side_unique_Facility to HVBP | PASS | Critical | One-side rows=5440; distinct keys=5440. |
| relationship_references_Geography to State Benchmark | PASS | Critical | Relationship table and column references resolve. |
| no_fact_to_fact_Geography to State Benchmark | PASS | Critical | Relationship is dimension-to-dimension or dimension-to-fact. |
| single_direction_Geography to State Benchmark | PASS | High | Relationship uses single-direction filtering. |
| one_side_unique_Geography to State Benchmark | PASS | Critical | One-side rows=56; distinct keys=56. |
| relationship_references_Measure to Provider Measure | PASS | Critical | Relationship table and column references resolve. |
| no_fact_to_fact_Measure to Provider Measure | PASS | Critical | Relationship is dimension-to-dimension or dimension-to-fact. |
| single_direction_Measure to Provider Measure | PASS | High | Relationship uses single-direction filtering. |
| one_side_unique_Measure to Provider Measure | PASS | Critical | One-side rows=29; distinct keys=29. |
| relationship_references_Measure to State Benchmark | PASS | Critical | Relationship table and column references resolve. |
| no_fact_to_fact_Measure to State Benchmark | PASS | Critical | Relationship is dimension-to-dimension or dimension-to-fact. |
| single_direction_Measure to State Benchmark | PASS | High | Relationship uses single-direction filtering. |
| one_side_unique_Measure to State Benchmark | PASS | Critical | One-side rows=29; distinct keys=29. |
| relationship_references_Measure to National Benchmark | PASS | Critical | Relationship table and column references resolve. |
| no_fact_to_fact_Measure to National Benchmark | PASS | Critical | Relationship is dimension-to-dimension or dimension-to-fact. |
| single_direction_Measure to National Benchmark | PASS | High | Relationship uses single-direction filtering. |
| one_side_unique_Measure to National Benchmark | PASS | Critical | One-side rows=29; distinct keys=29. |
| relationship_references_Measure to HRRP | PASS | Critical | Relationship table and column references resolve. |
| no_fact_to_fact_Measure to HRRP | PASS | Critical | Relationship is dimension-to-dimension or dimension-to-fact. |
| single_direction_Measure to HRRP | PASS | High | Relationship uses single-direction filtering. |
| one_side_unique_Measure to HRRP | PASS | Critical | One-side rows=29; distinct keys=29. |
| relationship_references_Period to Provider Measure | PASS | Critical | Relationship table and column references resolve. |
| no_fact_to_fact_Period to Provider Measure | PASS | Critical | Relationship is dimension-to-dimension or dimension-to-fact. |
| single_direction_Period to Provider Measure | PASS | High | Relationship uses single-direction filtering. |
| one_side_unique_Period to Provider Measure | PASS | Critical | One-side rows=8; distinct keys=8. |
| relationship_references_Period to State Benchmark | PASS | Critical | Relationship table and column references resolve. |
| no_fact_to_fact_Period to State Benchmark | PASS | Critical | Relationship is dimension-to-dimension or dimension-to-fact. |
| single_direction_Period to State Benchmark | PASS | High | Relationship uses single-direction filtering. |
| one_side_unique_Period to State Benchmark | PASS | Critical | One-side rows=8; distinct keys=8. |
| relationship_references_Period to National Benchmark | PASS | Critical | Relationship table and column references resolve. |
| no_fact_to_fact_Period to National Benchmark | PASS | Critical | Relationship is dimension-to-dimension or dimension-to-fact. |
| single_direction_Period to National Benchmark | PASS | High | Relationship uses single-direction filtering. |
| one_side_unique_Period to National Benchmark | PASS | Critical | One-side rows=8; distinct keys=8. |
| relationship_references_Period to HRRP | PASS | Critical | Relationship table and column references resolve. |
| no_fact_to_fact_Period to HRRP | PASS | Critical | Relationship is dimension-to-dimension or dimension-to-fact. |
| single_direction_Period to HRRP | PASS | High | Relationship uses single-direction filtering. |
| one_side_unique_Period to HRRP | PASS | Critical | One-side rows=8; distinct keys=8. |
| relationship_references_Period to HVBP | PASS | Critical | Relationship table and column references resolve. |
| no_fact_to_fact_Period to HVBP | PASS | Critical | Relationship is dimension-to-dimension or dimension-to-fact. |
| single_direction_Period to HVBP | PASS | High | Relationship uses single-direction filtering. |
| one_side_unique_Period to HVBP | PASS | Critical | One-side rows=8; distinct keys=8. |
| relationship_references_Release to Provider Measure | PASS | Critical | Relationship table and column references resolve. |
| no_fact_to_fact_Release to Provider Measure | PASS | Critical | Relationship is dimension-to-dimension or dimension-to-fact. |
| single_direction_Release to Provider Measure | PASS | High | Relationship uses single-direction filtering. |
| one_side_unique_Release to Provider Measure | PASS | Critical | One-side rows=6; distinct keys=6. |
| relationship_references_Release to State Benchmark | PASS | Critical | Relationship table and column references resolve. |
| no_fact_to_fact_Release to State Benchmark | PASS | Critical | Relationship is dimension-to-dimension or dimension-to-fact. |
| single_direction_Release to State Benchmark | PASS | High | Relationship uses single-direction filtering. |
| one_side_unique_Release to State Benchmark | PASS | Critical | One-side rows=6; distinct keys=6. |
| relationship_references_Release to National Benchmark | PASS | Critical | Relationship table and column references resolve. |
| no_fact_to_fact_Release to National Benchmark | PASS | Critical | Relationship is dimension-to-dimension or dimension-to-fact. |
| single_direction_Release to National Benchmark | PASS | High | Relationship uses single-direction filtering. |
| one_side_unique_Release to National Benchmark | PASS | Critical | One-side rows=6; distinct keys=6. |
| relationship_references_Release to HRRP | PASS | Critical | Relationship table and column references resolve. |
| no_fact_to_fact_Release to HRRP | PASS | Critical | Relationship is dimension-to-dimension or dimension-to-fact. |
| single_direction_Release to HRRP | PASS | High | Relationship uses single-direction filtering. |
| one_side_unique_Release to HRRP | PASS | Critical | One-side rows=6; distinct keys=6. |
| relationship_references_Release to HVBP | PASS | Critical | Relationship table and column references resolve. |
| no_fact_to_fact_Release to HVBP | PASS | Critical | Relationship is dimension-to-dimension or dimension-to-fact. |
| single_direction_Release to HVBP | PASS | High | Relationship uses single-direction filtering. |
| one_side_unique_Release to HVBP | PASS | Critical | One-side rows=6; distinct keys=6. |
| unique_measure_names | PASS | Critical | Measure count: 15. |
| dax_references_Facility Count | PASS | Critical | Home table=Dim Facility; unresolved=[]. |
| dax_references_Reportable Provider Results | PASS | Critical | Home table=Fact Provider Measure; unresolved=[]. |
| dax_references_Suppressed Provider Results | PASS | Critical | Home table=Fact Provider Measure; unresolved=[]. |
| dax_references_Reportable Result Percent | PASS | Critical | Home table=Fact Provider Measure; unresolved=[]. |
| dax_references_Selected Provider Score | PASS | Critical | Home table=Fact Provider Measure; unresolved=[]. |
| dax_references_Selected National Benchmark | PASS | Critical | Home table=Fact National Benchmark; unresolved=[]. |
| dax_references_Direction Adjusted Gap | PASS | Critical | Home table=Fact Provider Measure; unresolved=[]. |
| dax_references_Better Result Count | PASS | Critical | Home table=Fact Provider Measure; unresolved=[]. |
| dax_references_Same Result Count | PASS | Critical | Home table=Fact Provider Measure; unresolved=[]. |
| dax_references_Worse Result Count | PASS | Critical | Home table=Fact Provider Measure; unresolved=[]. |
| dax_references_Selected HRRP Excess Ratio | PASS | Critical | Home table=Fact HRRP; unresolved=[]. |
| dax_references_HRRP Above Expected Count | PASS | Critical | Home table=Fact HRRP; unresolved=[]. |
| dax_references_Selected HVBP TPS | PASS | Critical | Home table=Fact HVBP; unresolved=[]. |
| dax_references_Passed QA Checks | PASS | Critical | Home table=Fact Quality Check; unresolved=[]. |
| dax_references_Failed QA Checks | PASS | Critical | Home table=Fact Quality Check; unresolved=[]. |
| double_fact_fields_disable_implicit_sum | PASS | Critical | Unsafe fields: []. |
| no_active_release_to_facility_path | PASS | High | Facility and program facts may originate from different dataset releases; an active release-to-facility relationship would create misleading filtering. |
