"""
Overview Dashboard Module for FollowUp
Displays live operational continuity metrics, follow-up status distributions,
missed appointment indicators, and barrier frequencies strictly from database records.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

import config
from database.connection import execute_query
from services.reporting_service import (
    get_overview_metrics,
    get_conditions_distribution,
    get_appointment_status_breakdown,
    get_followup_trend_by_month
)
from services.support_service import get_continuity_barrier_breakdown
from utils.formatting import get_status_badge_html

def render_overview_page():
    """Render the operational clinical overview dashboard."""
    st.markdown(
        """
        <div style="margin-bottom: 16px;">
            <h2 style="color: #1e3a8a; margin-bottom: 2px; font-weight: 700;">Operational Continuity Overview</h2>
            <div style="font-size: 0.85rem; color: #475569;">
                Real-time operational indicators across active patient cohorts and partner facilities.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Facility Filter Header
    facilities = execute_query("SELECT id, name FROM facilities WHERE is_active = 1 ORDER BY name")
    facility_options = {"All Facilities": 0}
    for f in facilities:
        facility_options[f["name"]] = f["id"]
        
    col_filter, col_spacer = st.columns([2, 3])
    with col_filter:
        selected_fac_name = st.selectbox("Filter Catchment Facility", list(facility_options.keys()), index=0)
        selected_fac_id = facility_options[selected_fac_name]
        
    # Retrieve live metrics
    metrics = get_overview_metrics(facility_id=selected_fac_id if selected_fac_id > 0 else None)
    
    # Check Empty State
    if metrics["total_patients"] == 0:
        st.info("No registered patients found in the local database. Use Patient Management to register patients or initialize demonstration data.")
        return
        
    # 6 Core Metrics Cards (Compact, professional healthcare styling)
    st.markdown(
        f"""
        <div class="metric-container-grid">
            <div class="metric-card-pro">
                <div class="metric-card-label">Total Registered</div>
                <div class="metric-card-value">{metrics['total_patients']}</div>
                <div class="metric-card-caption">All registered chronic patients</div>
            </div>
            <div class="metric-card-pro">
                <div class="metric-card-label">Active Follow-Up</div>
                <div class="metric-card-value" style="color: #1e3a8a;">{metrics['active_patients']}</div>
                <div class="metric-card-caption">Patients under active monitoring</div>
            </div>
            <div class="metric-card-pro">
                <div class="metric-card-label">Appointments Due</div>
                <div class="metric-card-value" style="color: #b45309;">{metrics['due_appointments']}</div>
                <div class="metric-card-caption">Scheduled for review today</div>
            </div>
            <div class="metric-card-pro">
                <div class="metric-card-label">Missed Appointments</div>
                <div class="metric-card-value" style="color: #b91c1c;">{metrics['missed_appointments']}</div>
                <div class="metric-card-caption">Past scheduled date without visit</div>
            </div>
            <div class="metric-card-pro">
                <div class="metric-card-label">Support / Review Flags</div>
                <div class="metric-card-value" style="color: #c2410c;">{metrics['review_patients']}</div>
                <div class="metric-card-caption">High continuity risk or multiple misses</div>
            </div>
            <div class="metric-card-pro">
                <div class="metric-card-label">Completed Visits</div>
                <div class="metric-card-value" style="color: #047857;">{metrics['completed_appointments']}</div>
                <div class="metric-card-caption">{metrics['completion_rate']}% completion rate</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Attention Alerts for Missed or High Risk Patients
    if metrics['missed_appointments'] > 0 or metrics['review_patients'] > 0:
        st.markdown(
            f"""
            <div class="health-alert-banner">
                <strong>Continuity Alert:</strong> {metrics['missed_appointments']} appointment(s) have been missed and {metrics['review_patients']} patient(s) are flagged for multidisciplinary continuity review. Prioritize follow-up task assignment and patient contact outreach.
            </div>
            """,
            unsafe_allow_html=True
        )
        
    st.markdown("<hr style='border: none; border-top: 1px solid #cbd5e1; margin: 18px 0;'>", unsafe_allow_html=True)
    
    # Charts Row 1: Follow-Up Status Breakdown & Chronic Condition Distribution
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        st.markdown("<div style='font-weight: 600; font-size: 0.95rem; color: #1e3a8a; margin-bottom: 6px;'>Appointment Continuity Status</div>", unsafe_allow_html=True)
        df_status = get_appointment_status_breakdown(facility_id=selected_fac_id if selected_fac_id > 0 else None)
        if not df_status.empty:
            # Healthcare color palette
            color_map = {
                "Completed": "#047857",
                "Scheduled": "#1d4ed8",
                "Due": "#f59e0b",
                "Missed": "#dc2626",
                "Rescheduled": "#7c3aed",
                "Requires Review": "#ea580c"
            }
            fig_status = px.pie(
                df_status,
                names="status",
                values="count",
                color="status",
                color_discrete_map=color_map,
                hole=0.45
            )
            fig_status.update_layout(
                margin=dict(l=10, r=10, t=10, b=10),
                height=260,
                legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
            )
            st.plotly_chart(fig_status, use_container_width=True)
        else:
            st.caption("No appointments recorded for this selection.")
            
    with col_chart2:
        st.markdown("<div style='font-weight: 600; font-size: 0.95rem; color: #1e3a8a; margin-bottom: 6px;'>Patient Cohort by Condition Category</div>", unsafe_allow_html=True)
        df_cond = get_conditions_distribution(facility_id=selected_fac_id if selected_fac_id > 0 else None)
        if not df_cond.empty:
            fig_cond = px.bar(
                df_cond,
                x="patient_count",
                y="condition_category",
                orientation="h",
                color_discrete_sequence=["#1e3a8a"],
                labels={"patient_count": "Patients", "condition_category": "Condition"}
            )
            fig_cond.update_layout(
                margin=dict(l=10, r=10, t=10, b=10),
                height=260,
                yaxis=dict(autorange="reversed")
            )
            st.plotly_chart(fig_cond, use_container_width=True)
        else:
            st.caption("No condition records available.")
            
    # Charts Row 2: Reported Continuity Barriers & Monthly Activity Trends
    col_chart3, col_chart4 = st.columns(2)
    
    with col_chart3:
        st.markdown("<div style='font-weight: 600; font-size: 0.95rem; color: #1e3a8a; margin-bottom: 6px;'>Documented Barriers to Continued Care</div>", unsafe_allow_html=True)
        barriers_dict = get_continuity_barrier_breakdown()
        if barriers_dict and any(barriers_dict.values()):
            df_barriers = pd.DataFrame([
                {"Barrier": k, "Count": v} for k, v in barriers_dict.items() if v > 0
            ]).sort_values(by="Count", ascending=True)
            
            fig_barriers = px.bar(
                df_barriers,
                x="Count",
                y="Barrier",
                orientation="h",
                color_discrete_sequence=["#c2410c"],
                labels={"Count": "Reported Cases", "Barrier": "Barrier Category"}
            )
            fig_barriers.update_layout(
                margin=dict(l=10, r=10, t=10, b=10),
                height=250
            )
            st.plotly_chart(fig_barriers, use_container_width=True)
        else:
            st.caption("No continuity barriers recorded in active assessments.")
            
    with col_chart4:
        st.markdown("<div style='font-weight: 600; font-size: 0.95rem; color: #1e3a8a; margin-bottom: 6px;'>Monthly Follow-Up Trajectory</div>", unsafe_allow_html=True)
        df_trends = get_followup_trend_by_month(facility_id=selected_fac_id if selected_fac_id > 0 else None)
        if not df_trends.empty:
            fig_trend = go.Figure()
            fig_trend.add_trace(go.Bar(
                x=df_trends["month_period"],
                y=df_trends["completed"],
                name="Completed",
                marker_color="#047857"
            ))
            fig_trend.add_trace(go.Bar(
                x=df_trends["month_period"],
                y=df_trends["missed"],
                name="Missed",
                marker_color="#dc2626"
            ))
            fig_trend.update_layout(
                barmode="group",
                margin=dict(l=10, r=10, t=10, b=10),
                height=250,
                legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
            )
            st.plotly_chart(fig_trend, use_container_width=True)
        else:
            st.caption("No historical follow-up activity available yet.")
