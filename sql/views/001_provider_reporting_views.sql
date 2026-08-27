DROP VIEW IF EXISTS vw_provider_measure_reporting;
CREATE VIEW vw_provider_measure_reporting AS
SELECT
    fpm.provider_measure_key,
    f.facility_id,
    f.facility_name,
    f.hospital_type,
    f.hospital_ownership,
    f.state_code,
    f.is_alternate_federal_id,
    m.measure_id,
    m.measure_name,
    m.domain,
    m.unit,
    m.direction,
    m.measurement_start_date,
    m.measurement_end_date,
    fpm.comparison_category,
    fpm.score_numeric,
    fpm.score_raw,
    fpm.lower_estimate_numeric,
    fpm.upper_estimate_numeric,
    fpm.denominator_numeric,
    fpm.patient_count,
    fpm.patients_returned,
    fpm.footnote_code_raw,
    fpm.is_reportable,
    fpm.is_suppressed,
    fpm.suppression_reason,
    nb.national_rate_numeric,
    nb.national_rate_raw,
    sb.hospitals_worse AS state_hospitals_worse,
    sb.hospitals_same AS state_hospitals_same,
    sb.hospitals_better AS state_hospitals_better,
    sb.hospitals_too_few AS state_hospitals_too_few,
    fpm.snapshot_date,
    sr.source_release_date,
    sr.dataset_id AS source_dataset_id
FROM fact_provider_measure AS fpm
JOIN dim_facility AS f
  ON f.facility_key = fpm.facility_key
JOIN dim_measure AS m
  ON m.measure_key = fpm.measure_key
JOIN dim_source_release AS sr
  ON sr.source_release_key = fpm.source_release_key
LEFT JOIN fact_provider_national_benchmark AS nb
  ON nb.measure_key = fpm.measure_key
 AND nb.snapshot_date = fpm.snapshot_date
LEFT JOIN fact_provider_state_benchmark AS sb
  ON sb.geography_key = f.geography_key
 AND sb.measure_key = fpm.measure_key
 AND sb.snapshot_date = fpm.snapshot_date;

DROP VIEW IF EXISTS vw_provider_hrrp_reporting;
CREATE VIEW vw_provider_hrrp_reporting AS
SELECT
    h.provider_hrrp_key,
    f.facility_id,
    f.facility_name,
    f.state_code,
    f.hospital_type,
    f.hospital_ownership,
    m.measure_id,
    m.measure_name,
    m.unit,
    m.direction,
    m.measurement_start_date,
    m.measurement_end_date,
    m.fiscal_year,
    h.excess_readmission_ratio,
    h.predicted_readmission_rate,
    h.expected_readmission_rate,
    h.discharge_count,
    h.readmission_count,
    h.footnote_code_raw,
    h.is_reportable,
    h.is_suppressed,
    h.suppression_reason,
    h.snapshot_date,
    sr.source_release_date
FROM fact_provider_hrrp_measure AS h
JOIN dim_facility AS f
  ON f.facility_key = h.facility_key
JOIN dim_measure AS m
  ON m.measure_key = h.measure_key
JOIN dim_source_release AS sr
  ON sr.source_release_key = h.source_release_key;

DROP VIEW IF EXISTS vw_provider_hvbp_reporting;
CREATE VIEW vw_provider_hvbp_reporting AS
SELECT
    p.provider_program_score_key,
    f.facility_id,
    f.facility_name,
    f.state_code,
    f.hospital_type,
    f.hospital_ownership,
    p.fiscal_year,
    p.program_name,
    p.clinical_outcomes_unweighted,
    p.clinical_outcomes_weighted,
    p.engagement_unweighted,
    p.engagement_weighted,
    p.safety_unweighted,
    p.safety_weighted,
    p.efficiency_unweighted,
    p.efficiency_weighted,
    p.total_performance_score,
    p.is_tps_reportable,
    p.suppression_reason,
    p.snapshot_date,
    sr.source_release_date
FROM fact_provider_program_score AS p
JOIN dim_facility AS f
  ON f.facility_key = p.facility_key
JOIN dim_source_release AS sr
  ON sr.source_release_key = p.source_release_key;

DROP VIEW IF EXISTS vw_provider_suppression_summary;
CREATE VIEW vw_provider_suppression_summary AS
SELECT
    m.measure_id,
    m.measure_name,
    m.unit,
    m.direction,
    COUNT(*) AS source_rows,
    SUM(CASE WHEN fpm.is_reportable = 1 THEN 1 ELSE 0 END)
        AS reportable_rows,
    SUM(CASE WHEN fpm.is_suppressed = 1 THEN 1 ELSE 0 END)
        AS suppressed_rows,
    SUM(CASE
        WHEN fpm.is_reportable = 0 AND fpm.is_suppressed = 0 THEN 1
        ELSE 0
    END) AS other_nonreportable_rows
FROM fact_provider_measure AS fpm
JOIN dim_measure AS m
  ON m.measure_key = fpm.measure_key
GROUP BY
    m.measure_id,
    m.measure_name,
    m.unit,
    m.direction;

DROP VIEW IF EXISTS vw_provider_benchmark_join_coverage;
CREATE VIEW vw_provider_benchmark_join_coverage AS
SELECT
    COUNT(*) AS provider_measure_rows,
    SUM(CASE WHEN national_benchmark_key IS NOT NULL THEN 1 ELSE 0 END)
        AS national_benchmark_matched_rows,
    SUM(CASE WHEN state_benchmark_key IS NOT NULL THEN 1 ELSE 0 END)
        AS state_benchmark_matched_rows
FROM (
    SELECT
        fpm.provider_measure_key,
        nb.national_benchmark_key,
        sb.state_benchmark_key
    FROM fact_provider_measure AS fpm
    JOIN dim_facility AS f
      ON f.facility_key = fpm.facility_key
    LEFT JOIN fact_provider_national_benchmark AS nb
      ON nb.measure_key = fpm.measure_key
     AND nb.snapshot_date = fpm.snapshot_date
    LEFT JOIN fact_provider_state_benchmark AS sb
      ON sb.geography_key = f.geography_key
     AND sb.measure_key = fpm.measure_key
     AND sb.snapshot_date = fpm.snapshot_date
);

DROP VIEW IF EXISTS vw_provider_data_quality_summary;
CREATE VIEW vw_provider_data_quality_summary AS
SELECT
    phase,
    status,
    severity,
    COUNT(*) AS check_count
FROM fact_quality_check
GROUP BY phase, status, severity;
