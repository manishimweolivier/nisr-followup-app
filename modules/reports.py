"""
Reporting & Clinical Analytics Module for FollowUp
Generates management reports, facility performance benchmarks,
continuity barrier frequencies, and exports to CSV and PDF.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date, timedelta

import config
from database.connection import execute_query
from services.reporting_service import (
    get_overview_metrics,
    get_facility_performance_report,
    get_conditions_distribution,
    get_appointment_status_breakdown,
    get_followup_trend_by_month
)
from services.support_service import get_continuity_barrier_breakdown, list_support_assessments
from services.followup_service import list_appointments
from utils.helpers import dataframe_to_csv_bytes
from utils.formatting import format_date

def render_reports_page():
    """Render the reporting and clinical analytics module."""
    st.markdown(
        """
        <div style="margin-bottom: 16px;">
            <h2 style="color: #1e3a8a; margin-bottom: 2px; font-weight: 700;">Continuity Reports & Quality Analytics</h2>
            <div style="font-size: 0.85rem; color: #475569;">
                Evidence-based performance reports, facility benchmarks, and operational data exports.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Global Filters
    facilities = execute_query("SELECT id, name FROM facilities WHERE is_active = 1 ORDER BY name")
    fac_opts = {"All Facilities": 0}
    for f in facilities:
        fac_opts[f["name"]] = f["id"]
        
    c_f1, c_f2 = st.columns([2, 2])
    with c_f1:
        sel_facility = st.selectbox("Facility Filter", list(fac_opts.keys()), key="rep_fac_filter")
        fac_id = fac_opts[sel_facility]
        
    tab_summary, tab_facilities, tab_barriers, tab_export = st.tabs([
        "Operational Summary", "Facility Benchmarks", "Barrier Analysis", "Data Export (CSV)"
    ])
    
    # ---------------- TAB 1: OPERATIONAL SUMMARY ----------------
    with tab_summary:
        metrics = get_overview_metrics(facility_id=fac_id if fac_id > 0 else None)
        
        c_kpi1, c_kpi2, c_kpi3, c_kpi4 = st.columns(4)
        with c_kpi1:
            st.metric("Total Patients", metrics["total_patients"])
        with c_kpi2:
            st.metric("Completion Rate", f"{metrics['completion_rate']}%")
        with c_kpi3:
            st.metric("Missed Appointments", metrics["missed_appointments"])
        with c_kpi4:
            st.metric("Support / Review Flags", metrics["review_patients"])
            
        st.markdown("<hr style='border: none; border-top: 1px solid #cbd5e1; margin: 18px 0;'>", unsafe_allow_html=True)
        
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            st.markdown("<div style='font-weight: 600; font-size: 0.92rem; color: #1e3a8a; margin-bottom: 6px;'>Follow-Up Trajectory Over Time</div>", unsafe_allow_html=True)
            df_trend = get_followup_trend_by_month(facility_id=fac_id if fac_id > 0 else None)
            if not df_trend.empty:
                fig_t = px.bar(
                    df_trend,
                    x="month_period",
                    y=["completed", "missed"],
                    barmode="group",
                    color_discrete_map={"completed": "#047857", "missed": "#dc2626"},
                    labels={"value": "Visits", "month_period": "Month", "variable": "Status"}
                )
                fig_t.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=260)
                st.plotly_chart(fig_t, use_container_width=True)
            else:
                st.info("No appointment activity recorded for the selected filter.")
                
        with col_c2:
            st.markdown("<div style='font-weight: 600; font-size: 0.92rem; color: #1e3a8a; margin-bottom: 6px;'>Condition Distribution</div>", unsafe_allow_html=True)
            df_cond = get_conditions_distribution(facility_id=fac_id if fac_id > 0 else None)
            if not df_cond.empty:
                fig_c = px.pie(
                    df_cond,
                    names="condition_category",
                    values="patient_count",
                    hole=0.4,
                    color_discrete_sequence=px.colors.sequential.Blues_r
                )
                fig_c.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=260)
                st.plotly_chart(fig_c, use_container_width=True)
            else:
                st.info("No condition data available.")

    # ---------------- TAB 2: FACILITY BENCHMARKS ----------------
    with tab_facilities:
        st.markdown("<div style='font-weight: 600; font-size: 0.92rem; color: #1e3a8a; margin-bottom: 8px;'>Catchment Facility Comparative Performance Table</div>", unsafe_allow_html=True)
        df_fac = get_facility_performance_report()
        if df_fac.empty:
            st.info("No facility performance data available.")
        else:
            df_fac_disp = df_fac.rename(columns={
                "facility_name": "Healthcare Facility",
                "district": "District",
                "facility_type": "Classification",
                "registered_patients": "Registered Cohort",
                "active_followup": "Active Follow-Up",
                "requires_review": "Review Flags",
                "completed_appointments": "Completed Visits",
                "missed_appointments": "Missed Visits",
                "completion_rate_pct": "Completion Rate (%)"
            })
            st.dataframe(df_fac_disp, use_container_width=True, hide_index=True)
            
            # Comparative Completion Bar Chart
            fig_f = px.bar(
                df_fac,
                x="completion_rate_pct",
                y="facility_name",
                orientation="h",
                color="completion_rate_pct",
                color_continuous_scale="Teal",
                labels={"completion_rate_pct": "Completion Rate (%)", "facility_name": "Facility"}
            )
            fig_f.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=320, yaxis=dict(autorange="reversed"))
            st.plotly_chart(fig_f, use_container_width=True)

    # ---------------- TAB 3: BARRIER ANALYSIS ----------------
    with tab_barriers:
        st.markdown("<div style='font-weight: 600; font-size: 0.92rem; color: #1e3a8a; margin-bottom: 8px;'>Prevalence of Social & Logistical Continuity Barriers</div>", unsafe_allow_html=True)
        b_dict = get_continuity_barrier_breakdown()
        if b_dict and any(b_dict.values()):
            df_b = pd.DataFrame([
                {"Barrier Type": k, "Frequency": v} for k, v in b_dict.items()
            ]).sort_values(by="Frequency", ascending=False)
            
            col_b1, col_b2 = st.columns([1.5, 1])
            with col_b1:
                fig_bar = px.bar(
                    df_b,
                    x="Frequency",
                    y="Barrier Type",
                    orientation="h",
                    color="Frequency",
                    color_continuous_scale="Reds",
                    labels={"Frequency": "Total Recorded Cases", "Barrier Type": "Barrier"}
                )
                fig_bar.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=300, yaxis=dict(autorange="reversed"))
                st.plotly_chart(fig_bar, use_container_width=True)
            with col_b2:
                st.dataframe(df_b, use_container_width=True, hide_index=True)
        else:
            st.info("No continuity barrier assessments recorded yet.")

    # ---------------- TAB 4: DATA EXPORT ----------------
    with tab_export:
        st.markdown("<div style='font-weight: 600; font-size: 0.92rem; color: #1e3a8a; margin-bottom: 8px;'>Export Official Database Records to CSV</div>", unsafe_allow_html=True)
        st.write("Generate clean UTF-8 comma-separated value exports of all operational tables for offline reporting and institutional audits.")
        
        c_exp1, c_exp2, c_exp3 = st.columns(3)
        with c_exp1:
            st.markdown("<strong>Patient Registry</strong>", unsafe_allow_html=True)
            pts_df = pd.DataFrame(execute_query("SELECT patient_ref, full_name, age, sex, phone_number, district, sector, condition_category, followup_status, registration_date FROM patients"))
            if not pts_df.empty:
                st.download_button(
                    label="Download Patients CSV",
                    data=dataframe_to_csv_bytes(pts_df),
                    file_name="FollowUp_Patient_Registry.csv",
                    mime="text/csv",
                    use_container_width=True
                )
        with c_exp2:
            st.markdown("<strong>Appointments Log</strong>", unsafe_allow_html=True)
            apts_df = pd.DataFrame(execute_query("SELECT a.appointment_ref, p.patient_ref, p.full_name, a.scheduled_date, a.scheduled_time, a.followup_type, a.responsible_worker, a.status, a.outcome_notes FROM appointments a JOIN patients p ON a.patient_id = p.id"))
            if not apts_df.empty:
                st.download_button(
                    label="Download Appointments CSV",
                    data=dataframe_to_csv_bytes(apts_df),
                    file_name="FollowUp_Appointments_Log.csv",
                    mime="text/csv",
                    use_container_width=True
                )
        with c_exp3:
            st.markdown("<strong>Facility Benchmarks</strong>", unsafe_allow_html=True)
            fac_df = get_facility_performance_report()
            if not fac_df.empty:
                st.download_button(
                    label="Download Facility Report CSV",
                    data=dataframe_to_csv_bytes(fac_df),
                    file_name="FollowUp_Facility_Performance.csv",
                    mime="text/csv",
                    use_container_width=True
                )
