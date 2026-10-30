"""
Appointment Scheduling and Tracking Module for FollowUp
Coordinates scheduling, rescheduling, real-time overdue detection, and completion logging.
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta

import config
from database.connection import execute_query
from services.followup_service import (
    list_appointments,
    schedule_appointment,
    reschedule_appointment,
    sync_overdue_appointments
)
from services.patient_service import search_patients, get_patient_by_id
from services.auth_service import check_permission
from utils.formatting import get_status_badge_html, format_date

def render_appointments_page():
    """Render the appointment tracking and scheduling module."""
    user = st.session_state.get(config.SESSION_USER)
    can_edit = check_permission(user, [config.ROLE_ADMIN, config.ROLE_PROVIDER, config.ROLE_OFFICER])
    
    # Sync overdues on access
    sync_overdue_appointments()
    
    st.markdown(
        """
        <div style="margin-bottom: 16px;">
            <h2 style="color: #1e3a8a; margin-bottom: 2px; font-weight: 700;">Follow-Up Appointment Tracking</h2>
            <div style="font-size: 0.85rem; color: #475569;">
                Manage clinical consultations, home visits, and phone follow-ups with automatic overdue detection.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    tab_active, tab_missed, tab_all, tab_schedule = st.tabs([
        "Upcoming & Due Today", "Missed Appointments", "All Records", "Schedule Appointment"
    ])
    
    # ---------------- TAB 1: UPCOMING & DUE TODAY ----------------
    with tab_active:
        st.markdown("<div style='font-size: 0.88rem; font-weight: 600; color: #1e3a8a; margin-bottom: 8px;'>Active Appointments Pending Attendance</div>", unsafe_allow_html=True)
        active_apts = list_appointments()
        active_filtered = [a for a in active_apts if a["status"] in [config.STATUS_SCHEDULED, config.STATUS_DUE]]
        
        if not active_filtered:
            st.info("No active appointments pending for current or upcoming dates.")
        else:
            for apt in active_filtered:
                with st.container():
                    st.markdown(
                        f"""
                        <div style="background: #ffffff; border: 1px solid #cbd5e1; border-radius: 6px; padding: 12px 16px; margin-bottom: 10px;">
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <div>
                                    <span style="font-weight: 700; color: #1e3a8a; font-size: 0.95rem;">{apt['appointment_ref']}</span> &bull; 
                                    <span style="font-weight: 600; color: #0f172a;">{apt['patient_name']}</span> ({apt['patient_ref']})
                                    <div style="font-size: 0.82rem; color: #475569; margin-top: 2px;">
                                        <strong>Date:</strong> {format_date(apt['scheduled_date'])} at {apt['scheduled_time'] or '09:00'} &bull; 
                                        <strong>Modality:</strong> {apt['followup_type']} &bull; 
                                        <strong>Officer:</strong> {apt['responsible_worker']} &bull; 
                                        <strong>Facility:</strong> {apt['facility_name']}
                                    </div>
                                    <div style="font-size: 0.8rem; color: #64748b; margin-top: 2px;">
                                        <em>Condition: {apt['condition_category']} &bull; District: {apt['patient_district']} &bull; Phone: {apt['patient_phone'] or 'Unlisted'}</em>
                                    </div>
                                </div>
                                <div style="text-align: right;">
                                    {get_status_badge_html(apt['status'])}
                                </div>
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                    
                    if can_edit:
                        c_act1, c_act2, c_spacer = st.columns([1.2, 1.2, 2.5])
                        with c_act1:
                            if st.button("Complete Visit / Call", key=f"rec_visit_btn_{apt['id']}"):
                                st.session_state["active_apt_for_record"] = apt
                                st.info("Navigate to the Follow-Up Visits module to record clinical interaction details.")
                        with c_act2:
                            with st.popover("Reschedule"):
                                render_reschedule_popover(apt, user)

    # ---------------- TAB 2: MISSED APPOINTMENTS ----------------
    with tab_missed:
        missed_apts = [a for a in list_appointments() if a["status"] == config.STATUS_MISSED]
        st.markdown(
            f"""
            <div class="health-alert-banner">
                <strong>Attention Required:</strong> {len(missed_apts)} missed appointment(s) identified based on past scheduled dates. Prompt outreach is recommended to prevent loss to follow-up.
            </div>
            """,
            unsafe_allow_html=True
        )
        
        if not missed_apts:
            st.success("No missed appointments in the continuity registry.")
        else:
            for apt in missed_apts:
                with st.expander(f"{apt['appointment_ref']} - {apt['patient_name']} ({apt['patient_ref']}) | Missed on {format_date(apt['scheduled_date'])}", expanded=True):
                    col_m1, col_m2 = st.columns([2, 1])
                    with col_m1:
                        st.markdown(
                            f"""
                            <div style="font-size: 0.85rem; color: #0f172a;">
                                <strong>Original Scheduled Date:</strong> {format_date(apt['scheduled_date'])}<br>
                                <strong>Modality:</strong> {apt['followup_type']}<br>
                                <strong>Assigned Clinician/Officer:</strong> {apt['responsible_worker']}<br>
                                <strong>Facility:</strong> {apt['facility_name']}<br>
                                <strong>Patient Phone:</strong> {apt['patient_phone'] or 'Unlisted'}<br>
                                <strong>Clinical Notes:</strong> {apt['outcome_notes'] or 'No initial notes recorded.'}
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
                    with col_m2:
                        st.markdown(f"Status: {get_status_badge_html(apt['status'])}", unsafe_allow_html=True)
                        if can_edit:
                            st.markdown("<div style='font-weight: 600; font-size: 0.8rem; margin-top: 6px;'>Take Continuity Action:</div>", unsafe_allow_html=True)
                            with st.popover("Reschedule Appointment"):
                                render_reschedule_popover(apt, user)

    # ---------------- TAB 3: ALL RECORDS ----------------
    with tab_all:
        all_apts = list_appointments()
        if not all_apts:
            st.info("No appointments found.")
        else:
            df_apts = pd.DataFrame([
                {
                    "Ref": a["appointment_ref"],
                    "Patient Ref": a["patient_ref"],
                    "Patient Name": a["patient_name"],
                    "Date": format_date(a["scheduled_date"]),
                    "Time": a["scheduled_time"] or "09:00",
                    "Type": a["followup_type"],
                    "Officer": a["responsible_worker"],
                    "Facility": a["facility_name"],
                    "Status": a["status"]
                } for a in all_apts
            ])
            st.dataframe(df_apts, use_container_width=True, hide_index=True)

    # ---------------- TAB 4: SCHEDULE APPOINTMENT ----------------
    with tab_schedule:
        if not can_edit:
            st.warning("Only authorized Healthcare Providers or Officers can schedule appointments.")
        else:
            all_patients = search_patients()
            if not all_patients:
                st.warning("No patients registered.")
            else:
                pat_dict = {f"{p['patient_ref']} - {p['full_name']} ({p['condition_category']})": p for p in all_patients}
                facilities = execute_query("SELECT id, name FROM facilities WHERE is_active = 1 ORDER BY name")
                fac_opts = {f["name"]: f["id"] for f in facilities}
                
                with st.form("schedule_appointment_form"):
                    st.markdown("<div class='form-section-title'>1. Patient & Modality</div>", unsafe_allow_html=True)
                    sel_patient_label = st.selectbox("Select Patient *", list(pat_dict.keys()))
                    sel_pat = pat_dict[sel_patient_label]
                    
                    c1, c2 = st.columns(2)
                    with c1:
                        followup_type = st.selectbox("Follow-Up Modality *", config.FOLLOWUP_TYPES)
                    with c2:
                        fac_name = st.selectbox("Healthcare Facility *", list(fac_opts.keys()))
                        facility_id = fac_opts[fac_name]
                        
                    st.markdown("<div class='form-section-title'>2. Schedule Timing & Responsibility</div>", unsafe_allow_html=True)
                    c3, c4, c5 = st.columns([1.5, 1, 2])
                    with c3:
                        sch_date = st.date_input("Scheduled Date *", value=date.today() + timedelta(days=7))
                    with c4:
                        sch_time = st.selectbox("Time Slot", ["08:30", "09:00", "10:00", "11:00", "14:00", "15:30"])
                    with c5:
                        responsible_worker = st.text_input("Responsible Healthcare Worker / Officer *", value=user.get("full_name", ""))
                        
                    notes = st.text_area("Appointment Clinical Objective / Notes", placeholder="e.g. 30-day glycemic control review, fasting blood glucose test, and blood pressure titration.")
                    
                    sub_btn = st.form_submit_button("Schedule Follow-Up Appointment", type="primary", use_container_width=True)
                    if sub_btn:
                        ok, msg, aref = schedule_appointment(
                            patient_id=sel_pat["id"],
                            facility_id=facility_id,
                            scheduled_date=sch_date.isoformat(),
                            followup_type=followup_type,
                            responsible_worker=responsible_worker,
                            scheduled_time=sch_time,
                            notes=notes,
                            actor_username=user.get("username", "system"),
                            actor_role=user.get("role", "Healthcare Provider")
                        )
                        if ok:
                            st.success(f"{msg} (Reference: {aref})")
                            st.rerun()
                        else:
                            st.error(msg)

def render_reschedule_popover(apt: dict, user: dict):
    """Render inline popover form to reschedule an appointment."""
    st.markdown(f"<strong>Reschedule {apt['appointment_ref']}</strong>", unsafe_allow_html=True)
    new_date = st.date_input("New Date", value=date.today() + timedelta(days=7), key=f"resched_dt_{apt['id']}")
    reason = st.text_area("Reason for Rescheduling", placeholder="e.g. Patient contacted by phone; delayed due to heavy rain in sector.", key=f"resched_rsn_{apt['id']}")
    
    if st.button("Confirm Rescheduling", key=f"confirm_resched_{apt['id']}", type="primary"):
        ok, msg = reschedule_appointment(
            appointment_id=apt["id"],
            new_scheduled_date=new_date.isoformat(),
            reason=reason,
            actor_username=user.get("username", "system"),
            actor_role=user.get("role", "Healthcare Provider")
        )
        if ok:
            st.success(msg)
            st.rerun()
        else:
            st.error(msg)
