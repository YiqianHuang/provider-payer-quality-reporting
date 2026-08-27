"""Curated semantic metadata for the April/May 2026 Provider MVP."""

from __future__ import annotations


OFFICIAL = "Official published CMS result"

UNPLANNED_SUPPRESSION = (
    "Published missing/suppression text and CMS footnote codes; "
    "nonreportable values remain null, never zero."
)
HRRP_SUPPRESSION = (
    "N/A, Too Few to Report, or a published HRRP footnote; "
    "nonreportable values remain null, never zero."
)
HVBP_SUPPRESSION = (
    "Not Available in the published TPS field; the source has no Footnote "
    "column. Nonreportable values remain null, never zero."
)

AGGREGATE_LIMIT = (
    "Public facility-level aggregate; does not support patient-level, causal, "
    "or clinical-appropriateness inference."
)


UNPLANNED_MEASURES = [
    {
        "measure_id": "EDAC_30_AMI",
        "measure_name": "Hospital return days for heart attack patients",
        "domain": "Unplanned visits - return days",
        "unit": "Days per 100 discharges",
        "direction": "Lower is better",
        "start": "2021-07-01",
        "end": "2024-06-30",
        "interpretation": (
            "Negative is fewer acute-care return days than expected; zero is "
            "as expected; positive is more than expected."
        ),
        "limit": AGGREGATE_LIMIT,
    },
    {
        "measure_id": "EDAC_30_HF",
        "measure_name": "Hospital return days for heart failure patients",
        "domain": "Unplanned visits - return days",
        "unit": "Days per 100 discharges",
        "direction": "Lower is better",
        "start": "2021-07-01",
        "end": "2024-06-30",
        "interpretation": (
            "Negative is fewer acute-care return days than expected; zero is "
            "as expected; positive is more than expected."
        ),
        "limit": AGGREGATE_LIMIT,
    },
    {
        "measure_id": "EDAC_30_PN",
        "measure_name": "Hospital return days for pneumonia patients",
        "domain": "Unplanned visits - return days",
        "unit": "Days per 100 discharges",
        "direction": "Lower is better",
        "start": "2021-07-01",
        "end": "2024-06-30",
        "interpretation": (
            "Negative is fewer acute-care return days than expected; zero is "
            "as expected; positive is more than expected."
        ),
        "limit": AGGREGATE_LIMIT,
    },
    {
        "measure_id": "Hybrid_HWR",
        "measure_name": (
            "Hybrid Hospital-Wide All-Cause Readmission Measure (HWR)"
        ),
        "domain": "Readmission",
        "unit": "Percent",
        "direction": "Lower is better",
        "start": "2023-07-01",
        "end": "2024-06-30",
        "interpretation": "Published hospital-wide readmission rate.",
        "limit": (
            f"{AGGREGATE_LIMIT} Hybrid measure reporting methodology applies."
        ),
    },
    {
        "measure_id": "OP_32",
        "measure_name": (
            "Rate of unplanned hospital visits after colonoscopy "
            "(per 1,000 colonoscopies)"
        ),
        "domain": "Unplanned visits - outpatient procedure",
        "unit": "Visits per 1,000 colonoscopies",
        "direction": "Lower is better",
        "start": "2022-01-01",
        "end": "2024-12-31",
        "interpretation": (
            "Published risk-standardized rate compared with the official "
            "national rate when reportable."
        ),
        "limit": AGGREGATE_LIMIT,
    },
    {
        "measure_id": "OP_35_ADM",
        "measure_name": (
            "Rate of inpatient admissions for patients receiving outpatient "
            "chemotherapy"
        ),
        "domain": "Unplanned visits - outpatient chemotherapy",
        "unit": "Admissions per 100 chemotherapy patients",
        "direction": "Lower is better",
        "start": "2024-01-01",
        "end": "2024-12-31",
        "interpretation": (
            "Published risk-standardized rate compared with the official "
            "national rate when reportable."
        ),
        "limit": AGGREGATE_LIMIT,
    },
    {
        "measure_id": "OP_35_ED",
        "measure_name": (
            "Rate of emergency department (ED) visits for patients receiving "
            "outpatient chemotherapy"
        ),
        "domain": "Unplanned visits - outpatient chemotherapy",
        "unit": "ED visits per 100 chemotherapy patients",
        "direction": "Lower is better",
        "start": "2024-01-01",
        "end": "2024-12-31",
        "interpretation": (
            "Published risk-standardized rate compared with the official "
            "national rate when reportable."
        ),
        "limit": AGGREGATE_LIMIT,
    },
    {
        "measure_id": "OP_36",
        "measure_name": (
            "Ratio of unplanned hospital visits after hospital outpatient "
            "surgery"
        ),
        "domain": "Unplanned visits - outpatient surgery",
        "unit": "Risk-standardized ratio",
        "direction": "Lower is better",
        "start": "2024-01-01",
        "end": "2024-12-31",
        "interpretation": (
            "A ratio is interpreted relative to one using the published "
            "better/no-different/worse-than-expected category."
        ),
        "limit": AGGREGATE_LIMIT,
    },
]

for measure_id, name in [
    ("READM_30_AMI", "Acute Myocardial Infarction (AMI) 30-Day Readmission Rate"),
    ("READM_30_CABG", "Rate of readmission for CABG"),
    (
        "READM_30_COPD",
        "Rate of readmission for chronic obstructive pulmonary disease "
        "(COPD) patients",
    ),
    ("READM_30_HF", "Heart failure (HF) 30-Day Readmission Rate"),
    (
        "READM_30_HIP_KNEE",
        "Rate of readmission after hip/knee replacement",
    ),
    ("READM_30_PN", "Pneumonia (PN) 30-Day Readmission Rate"),
]:
    UNPLANNED_MEASURES.append(
        {
            "measure_id": measure_id,
            "measure_name": name,
            "domain": "Readmission",
            "unit": "Percent",
            "direction": "Lower is better",
            "start": "2021-07-01",
            "end": "2024-06-30",
            "interpretation": (
                "Published risk-standardized 30-day readmission rate and "
                "comparison category."
            ),
            "limit": AGGREGATE_LIMIT,
        }
    )


HRRP_MEASURES = [
    ("READM-30-AMI-HRRP", "AMI Excess Readmission Ratio"),
    ("READM-30-CABG-HRRP", "CABG Excess Readmission Ratio"),
    ("READM-30-COPD-HRRP", "COPD Excess Readmission Ratio"),
    ("READM-30-HF-HRRP", "Heart Failure Excess Readmission Ratio"),
    (
        "READM-30-HIP-KNEE-HRRP",
        "Hip/Knee Replacement Excess Readmission Ratio",
    ),
    ("READM-30-PN-HRRP", "Pneumonia Excess Readmission Ratio"),
]


HVBP_MEASURES = [
    (
        "HVBP_CLINICAL_UNWEIGHTED",
        "Unweighted Normalized Clinical Outcomes Domain Score",
    ),
    (
        "HVBP_CLINICAL_WEIGHTED",
        "Weighted Normalized Clinical Outcomes Domain Score",
    ),
    (
        "HVBP_ENGAGEMENT_UNWEIGHTED",
        "Unweighted Person And Community Engagement Domain Score",
    ),
    (
        "HVBP_ENGAGEMENT_WEIGHTED",
        "Weighted Person And Community Engagement Domain Score",
    ),
    (
        "HVBP_SAFETY_UNWEIGHTED",
        "Unweighted Normalized Safety Domain Score",
    ),
    ("HVBP_SAFETY_WEIGHTED", "Weighted Safety Domain Score"),
    (
        "HVBP_EFFICIENCY_UNWEIGHTED",
        "Unweighted Normalized Efficiency And Cost Reduction Domain Score",
    ),
    (
        "HVBP_EFFICIENCY_WEIGHTED",
        "Weighted Efficiency And Cost Reduction Domain Score",
    ),
    ("HVBP_TPS", "Total Performance Score"),
]


def measure_dimension_rows() -> list[dict[str, object]]:
    """Return complete measure-dimension rows for the Provider MVP."""
    rows: list[dict[str, object]] = []
    for item in UNPLANNED_MEASURES:
        rows.append(
            {
                "measure_id": item["measure_id"],
                "measure_name": item["measure_name"],
                "source_family": "unplanned_visits",
                "domain": item["domain"],
                "unit": item["unit"],
                "direction": item["direction"],
                "official_or_project_defined": OFFICIAL,
                "measurement_start_date": item["start"],
                "measurement_end_date": item["end"],
                "fiscal_year": 0,
                "suppression_rule": UNPLANNED_SUPPRESSION,
                "business_interpretation": item["interpretation"],
                "interpretation_limit": item["limit"],
            }
        )
    for measure_id, name in HRRP_MEASURES:
        rows.append(
            {
                "measure_id": measure_id,
                "measure_name": name,
                "source_family": "hrrp",
                "domain": "Readmission payment program",
                "unit": "Excess readmission ratio",
                "direction": "Lower is better",
                "official_or_project_defined": OFFICIAL,
                "measurement_start_date": "2021-07-01",
                "measurement_end_date": "2024-06-30",
                "fiscal_year": 2026,
                "suppression_rule": HRRP_SUPPRESSION,
                "business_interpretation": (
                    "Published predicted-to-expected readmission ratio; a "
                    "ratio above one indicates predicted exceeds expected."
                ),
                "interpretation_limit": (
                    f"{AGGREGATE_LIMIT} Payment implications require the "
                    "official HRRP methodology."
                ),
            }
        )
    for measure_id, name in HVBP_MEASURES:
        rows.append(
            {
                "measure_id": measure_id,
                "measure_name": name,
                "source_family": "hvbp_tps",
                "domain": "Value-based purchasing",
                "unit": "Score",
                "direction": "Higher is better",
                "official_or_project_defined": OFFICIAL,
                "measurement_start_date": "",
                "measurement_end_date": "",
                "fiscal_year": 2026,
                "suppression_rule": HVBP_SUPPRESSION,
                "business_interpretation": (
                    "Official FY 2026 HVBP domain or total performance score."
                ),
                "interpretation_limit": (
                    f"{AGGREGATE_LIMIT} Do not reverse-engineer a payment "
                    "adjustment from the TPS file alone."
                ),
            }
        )
    return rows

