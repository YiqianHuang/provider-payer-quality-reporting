PRAGMA foreign_keys = ON;

CREATE TABLE dim_source_release (
    source_release_key INTEGER PRIMARY KEY,
    dataset_id TEXT NOT NULL,
    dataset_title TEXT NOT NULL,
    source_issued_date TEXT,
    source_modified_date TEXT NOT NULL,
    source_release_date TEXT NOT NULL,
    snapshot_date TEXT NOT NULL,
    downloaded_at_utc TEXT NOT NULL,
    file_name TEXT NOT NULL,
    raw_path TEXT NOT NULL,
    download_url TEXT NOT NULL,
    sha256 TEXT NOT NULL,
    row_count INTEGER NOT NULL,
    column_count INTEGER NOT NULL,
    file_size_bytes INTEGER NOT NULL,
    UNIQUE (dataset_id, snapshot_date, sha256)
);

CREATE TABLE dim_geography (
    geography_key INTEGER PRIMARY KEY,
    geography_type TEXT NOT NULL,
    state_code TEXT NOT NULL,
    geography_name TEXT,
    UNIQUE (geography_type, state_code)
);

CREATE TABLE dim_reporting_period (
    reporting_period_key INTEGER PRIMARY KEY,
    period_role TEXT NOT NULL,
    measurement_start_date TEXT NOT NULL DEFAULT '',
    measurement_end_date TEXT NOT NULL DEFAULT '',
    fiscal_year INTEGER NOT NULL DEFAULT 0,
    source_release_date TEXT NOT NULL DEFAULT '',
    snapshot_date TEXT NOT NULL,
    period_label TEXT NOT NULL,
    UNIQUE (
        period_role,
        measurement_start_date,
        measurement_end_date,
        fiscal_year,
        source_release_date,
        snapshot_date
    )
);

CREATE TABLE dim_facility (
    facility_key INTEGER PRIMARY KEY,
    facility_id TEXT NOT NULL CHECK (length(facility_id) = 6),
    snapshot_date TEXT NOT NULL,
    source_release_key INTEGER NOT NULL,
    geography_key INTEGER NOT NULL,
    facility_record_source_dataset_id TEXT NOT NULL,
    is_current_general_info_match INTEGER NOT NULL CHECK (
        is_current_general_info_match IN (0, 1)
    ),
    facility_name TEXT NOT NULL,
    address_line_1 TEXT,
    city TEXT,
    state_code TEXT,
    zip_code TEXT,
    county_name TEXT,
    telephone_number TEXT,
    hospital_type TEXT,
    hospital_ownership TEXT,
    emergency_services_raw TEXT,
    birthing_friendly_raw TEXT,
    is_alternate_federal_id INTEGER NOT NULL CHECK (
        is_alternate_federal_id IN (0, 1)
    ),
    overall_rating_raw TEXT,
    overall_rating_numeric REAL,
    overall_rating_footnote_code TEXT,
    mort_group_measure_count_raw TEXT,
    mort_group_measure_count INTEGER,
    mort_facility_measure_count_raw TEXT,
    mort_facility_measure_count INTEGER,
    mort_better_count_raw TEXT,
    mort_better_count INTEGER,
    mort_no_different_count_raw TEXT,
    mort_no_different_count INTEGER,
    mort_worse_count_raw TEXT,
    mort_worse_count INTEGER,
    mort_group_footnote_code TEXT,
    safety_group_measure_count_raw TEXT,
    safety_group_measure_count INTEGER,
    safety_facility_measure_count_raw TEXT,
    safety_facility_measure_count INTEGER,
    safety_better_count_raw TEXT,
    safety_better_count INTEGER,
    safety_no_different_count_raw TEXT,
    safety_no_different_count INTEGER,
    safety_worse_count_raw TEXT,
    safety_worse_count INTEGER,
    safety_group_footnote_code TEXT,
    readm_group_measure_count_raw TEXT,
    readm_group_measure_count INTEGER,
    readm_facility_measure_count_raw TEXT,
    readm_facility_measure_count INTEGER,
    readm_better_count_raw TEXT,
    readm_better_count INTEGER,
    readm_no_different_count_raw TEXT,
    readm_no_different_count INTEGER,
    readm_worse_count_raw TEXT,
    readm_worse_count INTEGER,
    readm_group_footnote_code TEXT,
    patient_experience_group_measure_count_raw TEXT,
    patient_experience_group_measure_count INTEGER,
    patient_experience_facility_measure_count_raw TEXT,
    patient_experience_facility_measure_count INTEGER,
    patient_experience_group_footnote_code TEXT,
    timely_effective_group_measure_count_raw TEXT,
    timely_effective_group_measure_count INTEGER,
    timely_effective_facility_measure_count_raw TEXT,
    timely_effective_facility_measure_count INTEGER,
    timely_effective_group_footnote_code TEXT,
    UNIQUE (facility_id, snapshot_date),
    FOREIGN KEY (geography_key)
        REFERENCES dim_geography(geography_key),
    FOREIGN KEY (source_release_key)
        REFERENCES dim_source_release(source_release_key)
);

CREATE INDEX idx_dim_facility_state
    ON dim_facility(state_code, snapshot_date);

CREATE TABLE dim_measure (
    measure_key INTEGER PRIMARY KEY,
    measure_id TEXT NOT NULL,
    measure_name TEXT NOT NULL,
    source_family TEXT NOT NULL,
    domain TEXT NOT NULL,
    unit TEXT NOT NULL,
    direction TEXT NOT NULL CHECK (
        direction IN ('Lower is better', 'Higher is better', 'Context only')
    ),
    official_or_project_defined TEXT NOT NULL,
    measurement_start_date TEXT NOT NULL DEFAULT '',
    measurement_end_date TEXT NOT NULL DEFAULT '',
    fiscal_year INTEGER NOT NULL DEFAULT 0,
    suppression_rule TEXT NOT NULL,
    business_interpretation TEXT NOT NULL,
    interpretation_limit TEXT NOT NULL,
    UNIQUE (
        measure_id,
        source_family,
        measurement_start_date,
        measurement_end_date,
        fiscal_year
    )
);

CREATE TABLE fact_provider_measure (
    provider_measure_key INTEGER PRIMARY KEY,
    facility_key INTEGER NOT NULL,
    measure_key INTEGER NOT NULL,
    reporting_period_key INTEGER NOT NULL,
    source_release_key INTEGER NOT NULL,
    snapshot_date TEXT NOT NULL,
    comparison_category_raw TEXT,
    comparison_category TEXT,
    denominator_raw TEXT,
    denominator_numeric REAL,
    score_raw TEXT,
    score_numeric REAL,
    lower_estimate_raw TEXT,
    lower_estimate_numeric REAL,
    upper_estimate_raw TEXT,
    upper_estimate_numeric REAL,
    patient_count_raw TEXT,
    patient_count INTEGER,
    patients_returned_raw TEXT,
    patients_returned INTEGER,
    footnote_code_raw TEXT,
    is_reportable INTEGER NOT NULL CHECK (is_reportable IN (0, 1)),
    is_suppressed INTEGER NOT NULL CHECK (is_suppressed IN (0, 1)),
    suppression_reason TEXT,
    UNIQUE (facility_key, measure_key, source_release_key),
    FOREIGN KEY (facility_key) REFERENCES dim_facility(facility_key),
    FOREIGN KEY (measure_key) REFERENCES dim_measure(measure_key),
    FOREIGN KEY (reporting_period_key)
        REFERENCES dim_reporting_period(reporting_period_key),
    FOREIGN KEY (source_release_key)
        REFERENCES dim_source_release(source_release_key)
);

CREATE INDEX idx_fact_provider_measure_lookup
    ON fact_provider_measure(measure_key, snapshot_date);

CREATE TABLE fact_provider_state_benchmark (
    state_benchmark_key INTEGER PRIMARY KEY,
    geography_key INTEGER NOT NULL,
    measure_key INTEGER NOT NULL,
    reporting_period_key INTEGER NOT NULL,
    source_release_key INTEGER NOT NULL,
    snapshot_date TEXT NOT NULL,
    hospitals_worse_raw TEXT,
    hospitals_worse INTEGER,
    hospitals_same_raw TEXT,
    hospitals_same INTEGER,
    hospitals_better_raw TEXT,
    hospitals_better INTEGER,
    hospitals_too_few_raw TEXT,
    hospitals_too_few INTEGER,
    hospitals_fewer_raw TEXT,
    hospitals_fewer INTEGER,
    hospitals_average_raw TEXT,
    hospitals_average INTEGER,
    hospitals_more_raw TEXT,
    hospitals_more INTEGER,
    hospitals_too_small_raw TEXT,
    hospitals_too_small INTEGER,
    footnote_code_raw TEXT,
    UNIQUE (
        geography_key,
        measure_key,
        source_release_key
    ),
    FOREIGN KEY (geography_key) REFERENCES dim_geography(geography_key),
    FOREIGN KEY (measure_key) REFERENCES dim_measure(measure_key),
    FOREIGN KEY (reporting_period_key)
        REFERENCES dim_reporting_period(reporting_period_key),
    FOREIGN KEY (source_release_key)
        REFERENCES dim_source_release(source_release_key)
);

CREATE TABLE fact_provider_national_benchmark (
    national_benchmark_key INTEGER PRIMARY KEY,
    measure_key INTEGER NOT NULL,
    reporting_period_key INTEGER NOT NULL,
    source_release_key INTEGER NOT NULL,
    snapshot_date TEXT NOT NULL,
    national_rate_raw TEXT,
    national_rate_numeric REAL,
    hospitals_worse_raw TEXT,
    hospitals_worse INTEGER,
    hospitals_same_raw TEXT,
    hospitals_same INTEGER,
    hospitals_better_raw TEXT,
    hospitals_better INTEGER,
    hospitals_too_few_raw TEXT,
    hospitals_too_few INTEGER,
    hospitals_fewer_raw TEXT,
    hospitals_fewer INTEGER,
    hospitals_average_raw TEXT,
    hospitals_average INTEGER,
    hospitals_more_raw TEXT,
    hospitals_more INTEGER,
    hospitals_too_small_raw TEXT,
    hospitals_too_small INTEGER,
    footnote_code_raw TEXT,
    UNIQUE (measure_key, source_release_key),
    FOREIGN KEY (measure_key) REFERENCES dim_measure(measure_key),
    FOREIGN KEY (reporting_period_key)
        REFERENCES dim_reporting_period(reporting_period_key),
    FOREIGN KEY (source_release_key)
        REFERENCES dim_source_release(source_release_key)
);

CREATE TABLE fact_provider_hrrp_measure (
    provider_hrrp_key INTEGER PRIMARY KEY,
    facility_key INTEGER NOT NULL,
    measure_key INTEGER NOT NULL,
    reporting_period_key INTEGER NOT NULL,
    source_release_key INTEGER NOT NULL,
    snapshot_date TEXT NOT NULL,
    discharge_count_raw TEXT,
    discharge_count INTEGER,
    footnote_code_raw TEXT,
    excess_readmission_ratio_raw TEXT,
    excess_readmission_ratio REAL,
    predicted_readmission_rate_raw TEXT,
    predicted_readmission_rate REAL,
    expected_readmission_rate_raw TEXT,
    expected_readmission_rate REAL,
    readmission_count_raw TEXT,
    readmission_count INTEGER,
    is_reportable INTEGER NOT NULL CHECK (is_reportable IN (0, 1)),
    is_suppressed INTEGER NOT NULL CHECK (is_suppressed IN (0, 1)),
    suppression_reason TEXT,
    UNIQUE (facility_key, measure_key, source_release_key),
    FOREIGN KEY (facility_key) REFERENCES dim_facility(facility_key),
    FOREIGN KEY (measure_key) REFERENCES dim_measure(measure_key),
    FOREIGN KEY (reporting_period_key)
        REFERENCES dim_reporting_period(reporting_period_key),
    FOREIGN KEY (source_release_key)
        REFERENCES dim_source_release(source_release_key)
);

CREATE TABLE fact_provider_program_score (
    provider_program_score_key INTEGER PRIMARY KEY,
    facility_key INTEGER NOT NULL,
    reporting_period_key INTEGER NOT NULL,
    source_release_key INTEGER NOT NULL,
    snapshot_date TEXT NOT NULL,
    fiscal_year INTEGER NOT NULL,
    program_name TEXT NOT NULL,
    clinical_outcomes_unweighted_raw TEXT,
    clinical_outcomes_unweighted REAL,
    clinical_outcomes_weighted_raw TEXT,
    clinical_outcomes_weighted REAL,
    engagement_unweighted_raw TEXT,
    engagement_unweighted REAL,
    engagement_weighted_raw TEXT,
    engagement_weighted REAL,
    safety_unweighted_raw TEXT,
    safety_unweighted REAL,
    safety_weighted_raw TEXT,
    safety_weighted REAL,
    efficiency_unweighted_raw TEXT,
    efficiency_unweighted REAL,
    efficiency_weighted_raw TEXT,
    efficiency_weighted REAL,
    total_performance_score_raw TEXT,
    total_performance_score REAL,
    is_tps_reportable INTEGER NOT NULL CHECK (
        is_tps_reportable IN (0, 1)
    ),
    suppression_reason TEXT,
    UNIQUE (
        facility_key,
        fiscal_year,
        program_name,
        source_release_key
    ),
    FOREIGN KEY (facility_key) REFERENCES dim_facility(facility_key),
    FOREIGN KEY (reporting_period_key)
        REFERENCES dim_reporting_period(reporting_period_key),
    FOREIGN KEY (source_release_key)
        REFERENCES dim_source_release(source_release_key)
);

CREATE TABLE fact_quality_check (
    quality_check_key INTEGER PRIMARY KEY,
    check_id TEXT NOT NULL,
    run_id TEXT NOT NULL,
    phase TEXT NOT NULL,
    table_name TEXT NOT NULL,
    check_name TEXT NOT NULL,
    expected_value TEXT,
    actual_value TEXT,
    status TEXT NOT NULL,
    severity TEXT NOT NULL,
    details TEXT,
    checked_at TEXT NOT NULL,
    UNIQUE (check_id, run_id, phase)
);
