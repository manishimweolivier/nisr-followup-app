"""
Reporting and Clinical Analytics Service for FollowUp
Aggregates operational continuity indicators, completion metrics,
barrier frequencies, and facility performance from actual database records.
"""

from datetime import datetime, date
from typing import Optional, Dict, Any, List
import pandas as pd

import config
from database.connection import execute_query, execute_single, query_to_dataframe

def get_overview_metrics(facility_id: Optional[int] = None) -> Dict[str, Any]:
    """Calculate operational KPIs strictly from live database records."""
    # Ensure statuses are synchronized with actual dates
    from services.followup_service import sync_overdue_appointments
    sync_overdue_appointments()
    
    fac_filter_p = "WHERE 1=1"
    fac_filter_a = "WHERE 1=1"
    params_p = []
    params_a = []
    
    if facility_id and facility_id > 0:
        fac_filter_p += " AND facility_id = ?"
        fac_filter_a += " AND facility_id = ?"
        params_p.append(facility_id)
        params_a.append(facility_id)
        
    # 1. Total registered patients
    p_row = execute_single(f"SELECT COUNT(*) as cnt FROM patients {fac_filter_p}", tuple(params_p))
    total_patients = p_row["cnt"] if p_row else 0
    
    # 2. Patients under active follow-up
    active_row = execute_single(f"SELECT COUNT(*) as cnt FROM patients {fac_filter_p} AND followup_status = 'Active Follow-Up'", tuple(params_p))
    active_patients = active_row["cnt"] if active_row else 0
    
    # 3. Patients requiring review / high vulnerability
    review_row = execute_single(f"SELECT COUNT(*) as cnt FROM patients {fac_filter_p} AND followup_status = 'Requires Review'", tuple(params_p))
    review_patients = review_row["cnt"] if review_row else 0
    
    # 4. Follow-up appointments Due
    due_row = execute_single(f"SELECT COUNT(*) as cnt FROM appointments {fac_filter_a} AND status = 'Due'", tuple(params_a))
    due_appointments = due_row["cnt"] if due_row else 0
    
    # 5. Missed appointments
    missed_row = execute_single(f"SELECT COUNT(*) as cnt FROM appointments {fac_filter_a} AND status = 'Missed'", tuple(params_a))
    missed_appointments = missed_row["cnt"] if missed_row else 0
    
    # 6. Completed follow-up activities
    comp_row = execute_single(f"SELECT COUNT(*) as cnt FROM appointments {fac_filter_a} AND status = 'Completed'", tuple(params_a))
    completed_appointments = comp_row["cnt"] if comp_row else 0
    
    # Completion rate
    total_due_or_done = completed_appointments + missed_appointments
    completion_rate = round((completed_appointments / total_due_or_done * 100), 1) if total_due_or_done > 0 else 100.0
    
    return {
        "total_patients": total_patients,
        "active_patients": active_patients,
        "review_patients": review_patients,
        "due_appointments": due_appointments,
        "missed_appointments": missed_appointments,
        "completed_appointments": completed_appointments,
        "completion_rate": completion_rate
    }

def get_conditions_distribution(facility_id: Optional[int] = None) -> pd.DataFrame:
    """Return patient counts grouped by clinical condition category."""
    sql = """
        SELECT condition_category, COUNT(*) as patient_count
        FROM patients
        WHERE 1=1
    """
    params = []
    if facility_id and facility_id > 0:
        sql += " AND facility_id = ?"
        params.append(facility_id)
    sql += " GROUP BY condition_category ORDER BY patient_count DESC"
    return query_to_dataframe(sql, tuple(params))

def get_appointment_status_breakdown(facility_id: Optional[int] = None) -> pd.DataFrame:
    """Return appointment counts grouped by status."""
    from services.followup_service import sync_overdue_appointments
    sync_overdue_appointments()
    
    sql = "SELECT status, COUNT(*) as count FROM appointments WHERE 1=1"
    params = []
    if facility_id and facility_id > 0:
        sql += " AND facility_id = ?"
        params.append(facility_id)
    sql += " GROUP BY status ORDER BY count DESC"
    return query_to_dataframe(sql, tuple(params))

def get_facility_performance_report() -> pd.DataFrame:
    """Generate comparative continuity statistics across partner healthcare facilities."""
    from services.followup_service import sync_overdue_appointments
    sync_overdue_appointments()
    
    sql = """
        SELECT f.name as facility_name, f.district, f.facility_type,
               COUNT(DISTINCT p.id) as registered_patients,
               SUM(CASE WHEN p.followup_status = 'Active Follow-Up' THEN 1 ELSE 0 END) as active_followup,
               SUM(CASE WHEN p.followup_status = 'Requires Review' THEN 1 ELSE 0 END) as requires_review,
               SUM(CASE WHEN a.status = 'Completed' THEN 1 ELSE 0 END) as completed_appointments,
               SUM(CASE WHEN a.status = 'Missed' THEN 1 ELSE 0 END) as missed_appointments,
               SUM(CASE WHEN a.status = 'Due' THEN 1 ELSE 0 END) as due_appointments
        FROM facilities f
        LEFT JOIN patients p ON f.id = p.facility_id
        LEFT JOIN appointments a ON f.id = a.facility_id
        GROUP BY f.id, f.name, f.district, f.facility_type
        ORDER BY registered_patients DESC, f.name ASC
    """
    df = query_to_dataframe(sql)
    if not df.empty:
        # Calculate completion rate
        total_eval = df["completed_appointments"] + df["missed_appointments"]
        df["completion_rate_pct"] = (df["completed_appointments"] / total_eval * 100).fillna(100.0).round(1)
    return df

def get_followup_trend_by_month(facility_id: Optional[int] = None) -> pd.DataFrame:
    """Retrieve monthly trend of completed vs missed appointments."""
    sql = """
        SELECT SUBSTR(scheduled_date, 1, 7) as month_period,
               SUM(CASE WHEN status = 'Completed' THEN 1 ELSE 0 END) as completed,
               SUM(CASE WHEN status = 'Missed' THEN 1 ELSE 0 END) as missed,
               COUNT(*) as total_scheduled
        FROM appointments
        WHERE 1=1
    """
    params = []
    if facility_id and facility_id > 0:
        sql += " AND facility_id = ?"
        params.append(facility_id)
    sql += " GROUP BY SUBSTR(scheduled_date, 1, 7) ORDER BY month_period ASC"
    return query_to_dataframe(sql, tuple(params))
