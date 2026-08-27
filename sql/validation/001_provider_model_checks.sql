-- Duplicate Provider measure grain: expected zero rows.
SELECT
    facility_key,
    measure_key,
    source_release_key,
    COUNT(*) AS row_count
FROM fact_provider_measure
GROUP BY facility_key, measure_key, source_release_key
HAVING COUNT(*) > 1;

-- Suppressed or nonreportable scores must not be numeric zero by coercion.
SELECT COUNT(*) AS invalid_zero_rows
FROM fact_provider_measure
WHERE is_reportable = 0
  AND score_numeric = 0;

-- Applicable interval ordering: expected zero rows.
SELECT COUNT(*) AS invalid_interval_rows
FROM fact_provider_measure
WHERE lower_estimate_numeric IS NOT NULL
  AND score_numeric IS NOT NULL
  AND upper_estimate_numeric IS NOT NULL
  AND NOT (
      lower_estimate_numeric <= score_numeric
      AND score_numeric <= upper_estimate_numeric
  );

-- Every measure has required semantic metadata.
SELECT COUNT(*) AS incomplete_measure_rows
FROM dim_measure
WHERE unit = ''
   OR direction = ''
   OR suppression_rule = ''
   OR business_interpretation = ''
   OR interpretation_limit = '';

-- Official benchmark row-join coverage.
SELECT * FROM vw_provider_benchmark_join_coverage;

-- Fact-to-dimension orphan check: expected zero.
SELECT COUNT(*) AS orphan_rows
FROM fact_provider_measure AS fpm
LEFT JOIN dim_facility AS f
  ON f.facility_key = fpm.facility_key
LEFT JOIN dim_measure AS m
  ON m.measure_key = fpm.measure_key
WHERE f.facility_key IS NULL
   OR m.measure_key IS NULL;

