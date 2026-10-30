"""
NISR Statistical Data Service for FollowUp
Manages Rwanda National Institute of Statistics (NISR) aggregate survey datasets,
specifically EICV7 living conditions, poverty, and health access indicators.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple
from pathlib import Path
import pandas as pd
import json

import config
from database.connection import execute_query, execute_single, execute_statement, query_to_dataframe
from services.auth_service import log_audit_action

def get_nisr_district_indicators(province: Optional[str] = None) -> pd.DataFrame:
    """Retrieve official NISR EICV7 district indicators as a DataFrame."""
    sql = """
        SELECT district, province, poverty_rate_pct, extreme_poverty_rate_pct,
               health_insurance_coverage_pct, travel_time_over_1hr_pct,
               chronic_illness_reported_pct, unimproved_sanitation_pct,
               reference_survey, source_citation
        FROM nisr_district_indicators
        WHERE 1=1
    """
    params = []
    if province and province != "All Provinces":
        sql += " AND province = ?"
        params.append(province)
        
    sql += " ORDER BY province, district"
    return query_to_dataframe(sql, tuple(params))

def get_nisr_national_summary() -> Dict[str, Any]:
    """Calculate aggregate national weighted averages across all 30 districts."""
    df = get_nisr_district_indicators()
    if df.empty:
        return {}
        
    return {
        "total_districts": len(df),
        "avg_poverty_rate": round(df["poverty_rate_pct"].mean(), 1),
        "avg_extreme_poverty_rate": round(df["extreme_poverty_rate_pct"].mean(), 1),
        "avg_insurance_coverage": round(df["health_insurance_coverage_pct"].mean(), 1),
        "avg_travel_time_over_1hr": round(df["travel_time_over_1hr_pct"].mean(), 1),
        "avg_chronic_illness_reported": round(df["chronic_illness_reported_pct"].mean(), 1),
        "max_travel_time_district": df.loc[df["travel_time_over_1hr_pct"].idxmax()]["district"],
        "max_travel_time_pct": df["travel_time_over_1hr_pct"].max(),
        "highest_poverty_district": df.loc[df["poverty_rate_pct"].idxmax()]["district"],
        "highest_poverty_pct": df["poverty_rate_pct"].max(),
        "highest_insurance_district": df.loc[df["health_insurance_coverage_pct"].idxmax()]["district"],
        "highest_insurance_pct": df["health_insurance_coverage_pct"].max()
    }

def get_registered_patients_by_district() -> pd.DataFrame:
    """Aggregate actual registered continuity patients by district to overlay with NISR statistics."""
    sql = """
        SELECT district, COUNT(*) as registered_patients_count,
               SUM(CASE WHEN followup_status = 'Active Follow-Up' THEN 1 ELSE 0 END) as active_followup_count,
               SUM(CASE WHEN followup_status = 'Requires Review' THEN 1 ELSE 0 END) as review_needed_count
        FROM patients
        GROUP BY district
    """
    return query_to_dataframe(sql)

def import_custom_nisr_dataset(csv_file_obj,
                               dataset_name: str,
                               source_url: str,
                               reference_period: str,
                               geographic_coverage: str,
                               indicator_description: str,
                               actor_username: str,
                               actor_role: str) -> Tuple[bool, str]:
    """
    Import an external NISR or Ministry of Health aggregate statistical CSV file.
    Validates structure, updates local indicators, and stores official dataset metadata.
    """
    try:
        df = pd.read_csv(csv_file_obj)
        required_cols = ["district", "province", "poverty_rate_pct", "health_insurance_coverage_pct", "travel_time_over_1hr_pct"]
        missing = [c for c in required_cols if c not in df.columns]
        if missing:
            return False, f"CSV file is missing mandatory indicator columns: {', '.join(missing)}."
            
        now_str = datetime.now().isoformat()
        dataset_key = f"custom_nisr_{int(datetime.now().timestamp())}"
        
        # Insert or update district indicators
        for _, row in df.iterrows():
            execute_statement(
                """
                INSERT OR REPLACE INTO nisr_district_indicators
                (district, province, poverty_rate_pct, extreme_poverty_rate_pct,
                 health_insurance_coverage_pct, travel_time_over_1hr_pct,
                 chronic_illness_reported_pct, unimproved_sanitation_pct,
                 reference_survey, source_citation)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(row["district"]), str(row["province"]),
                    float(row.get("poverty_rate_pct", 0.0)),
                    float(row.get("extreme_poverty_rate_pct", 0.0)),
                    float(row.get("health_insurance_coverage_pct", 0.0)),
                    float(row.get("travel_time_over_1hr_pct", 0.0)),
                    float(row.get("chronic_illness_reported_pct", 0.0)),
                    float(row.get("unimproved_sanitation_pct", 0.0)),
                    reference_period,
                    dataset_name
                )
            )
            
        # Store metadata
        execute_statement(
            """
            INSERT INTO statistical_datasets
            (dataset_key, dataset_name, publishing_institution, source_url,
             reference_period, geographic_coverage, indicator_description, imported_at, row_count)
            VALUES (?, ?, 'National Institute of Statistics of Rwanda (NISR)', ?, ?, ?, ?, ?, ?)
            """,
            (
                dataset_key, dataset_name.strip(), source_url.strip(),
                reference_period.strip(), geographic_coverage.strip(),
                indicator_description.strip(), now_str, len(df)
            )
        )
        
        log_audit_action(
            username=actor_username,
            role=actor_role,
            action="DATASET_IMPORT",
            target_type="StatisticalDataset",
            target_ref=dataset_key,
            details=f"Imported {len(df)} district records for dataset '{dataset_name}'."
        )
        return True, f"Successfully imported {len(df)} district indicator records."
    except Exception as e:
        return False, f"Failed to import statistical CSV: {str(e)}"

def list_imported_datasets() -> List[Dict[str, Any]]:
    """Retrieve metadata of all official and imported statistical datasets."""
    rows = execute_query("SELECT * FROM statistical_datasets ORDER BY imported_at DESC")
    return [dict(r) for r in rows]
