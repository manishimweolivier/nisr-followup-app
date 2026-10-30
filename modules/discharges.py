"""
Hospital Discharge Management Module for FollowUp
Coordinates transition from inpatient admission to outpatient continuity of care,
care instructions, and initial follow-up appointment generation.
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta

import config
from database.connection import execute_query
from services.discharge_service import record_discharge, list_discharges, close_discharge
from services.patient_service import search_patients, get_patient_by_id
from services.auth_service import check_permission
from utils.formatting import get_status_badge_html, format_date

def render_discharges_page():
    """Render the hospital discharge management module."""
    user = st.session_state.get(config.SESSION_USER)
    can_edit = check_permission(user, [config.ROLE_ADMIN, config.ROLE_PROVIDER])
    
    st.markdown(
        """
        <div style="margin-bottom: 16px;">
            <h2 style="color: #1e3a8a; margin-bottom: 2px; font-weight: 700;">Inpatient Discharge & Care Continuity</h2>
            <div style="font-size: 0.85rem; color: #475569;">
                Record hospital discharge regimens and transitional care instructions for chronic continuity cases.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    tab_list, tab_record = st.tabs(["Discharged Patients Registry", "Record New Hospital Discharge"])
    
    # ---------------- TAB 1: DISCHARGES LIST ----------------
    with tab_list:
        # Filters
        facilities = execute_query("SELECT id, name FROM facilities WHERE is_active = 1 ORDER BY name")
        fac_opts = {"All Facilities": 0}
        for f in facilities:
            fac_opts[f["name"]] = f["id"]
            
        c1, c2, c3 = st.columns([1.5, 1.2, 1.2])
        with c1:
            sel_fac = st.selectbox("Facility Filter", list(fac_opts.keys()), key="dis_fac_filter")
        with c2:
            sel_stat = st.selectbox("Continuity Status", ["All Statuses", "Open", "Completed"], key="dis_stat_filter")
        with c3:
            sel_cond = st.selectbox("Condition Category", ["All Conditions"] + config.CONDITION_CATEGORIES, key="dis_cond_filter")
            
        discharges = list_discharges(
            facility_id=fac_opts[sel_fac],
            status=sel_stat,
            condition=sel_cond
        )
        
        st.markdown(f"<div style='font-size: 0.82rem; color: #475569; margin: 8px 0;'>Showing <strong>{len(discharges)}</strong> discharge record(s)</div>", unsafe_allow_html=True)
        
        if not discharges:
            st.info("No discharge records match the selected criteria.")
        else:
            for d in discharges:
                with st.expander(f"{d['discharge_ref']} - {d['patient_name']} ({d['patient_ref']}) | Discharged {format_date(d['discharge_date'])}", expanded=(d['status'] == 'Open')):
                    col_info1, col_info2 = st.columns([2, 1])
                    with col_info1:
                        st.markdown(
                            f"""
                            <div style="font-size: 0.86rem; color: #0f172a; line-height: 1.5;">
                                <strong>Admitted:</strong> {format_date(d['admission_date'])} &bull; 
                                <strong>Discharged:</strong> {format_date(d['discharge_date'])} &bull; 
                                <strong>Facility:</strong> {d['facility_name']}<br>
                                <strong>Clinical Diagnosis:</strong> {d['diagnosis_summary']}<br>
                                <strong>Discharge Instructions:</strong> {d['followup_instructions']}<br>
                                <strong>Recommended Next Appointment:</strong> {format_date(d['recommended_appointment_date'])} &bull; 
                                <strong>Clinician:</strong> {d['responsible_clinician']}
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
                        if d.get("discharge_support_needs"):
                            st.markdown(
                                f"<div style='margin-top: 6px; font-size: 0.82rem; color: #b45309; background: #fffbeb; padding: 6px 10px; border-radius: 4px;'><strong>Documented Support Requirements:</strong> {d['discharge_support_needs']}</div>",
                                unsafe_allow_html=True
                            )
                    with col_info2:
                        st.markdown(f"Status: {get_status_badge_html(d['status'])}", unsafe_allow_html=True)
                        if d['status'] == 'Open' and can_edit:
                            if st.button("Mark Care Cycle Completed", key=f"close_dis_{d['id']}", use_container_width=True):
                                close_discharge(
                                    discharge_id=d['id'],
                                    actor_username=user.get("username", "system"),
                                    actor_role=user.get("role", "Healthcare Provider")
                                )
                                st.success(f"Discharge {d['discharge_ref']} marked as completed.")
                                st.rerun()

    # ---------------- TAB 2: RECORD NEW DISCHARGE ----------------
    with tab_record:
        if not can_edit:
            st.warning("Only Healthcare Providers or Administrators can record hospital discharges.")
        else:
            all_patients = search_patients()
            if not all_patients:
                st.warning("No registered patients found. Please register the patient in Patient Management first.")
            else:
                pat_dict = {f"{p['patient_ref']} - {p['full_name']} ({p['condition_category']})": p["id"] for p in all_patients}
                
                with st.form("new_discharge_form"):
                    st.markdown("<div class='form-section-title'>1. Patient Identification</div>", unsafe_allow_html=True)
                    sel_patient_label = st.selectbox("Select Admitted Patient *", list(pat_dict.keys()))
                    patient_id = pat_dict[sel_patient_label]
                    
                    st.markdown("<div class='form-section-title'>2. Hospital Admission & Discharge Timeline</div>", unsafe_allow_html=True)
                    today_val = date.today()
                    c_d1, c_d2, c_d3 = st.columns(3)
                    with c_d1:
                        adm_date = st.date_input("Admission Date *", value=today_val - timedelta(days=5))
                    with c_d2:
                        dis_date = st.date_input("Discharge Date *", value=today_val)
                    with c_d3:
                        rec_apt_date = st.date_input("Recommended Follow-Up Date *", value=today_val + timedelta(days=14))
                        
                    st.markdown("<div class='form-section-title'>3. Clinical Instructions & Support Needs</div>", unsafe_allow_html=True)
                    diagnosis = st.text_input("Clinical Discharge Diagnosis Summary *", placeholder="e.g. Decompensated Heart Failure NYHA III stabilized, Grade 2 Essential Hypertension")
                    
                    c_fac, c_doc = st.columns(2)
                    with c_fac:
                        dis_fac_opts = {f["name"]: f["id"] for f in facilities}
                        dis_fac_name = st.selectbox("Discharging Facility *", list(dis_fac_opts.keys()))
                        facility_id = dis_fac_opts[dis_fac_name]
                    with c_doc:
                        clinician = st.text_input("Attending Clinician *", value=user.get("full_name", "Dr. David Mucyo, MD"))
                        
                    instructions = st.text_area("Post-Discharge Care & Medication Regimen Instructions *", placeholder="Detail medication dosages, self-monitoring requirements, warning signs to watch for, and diet/lifestyle directives.")
                    support_needs = st.text_input("Logistical / Social Support Requirements (Optional)", placeholder="e.g. Transport subsidy voucher needed, caregiver counseling, pillbox organizer")
                    
                    auto_schedule = st.checkbox("Automatically schedule initial follow-up appointment on recommended date", value=True)
                    
                    submit_btn = st.form_submit_button("Record Hospital Discharge", type="primary", use_container_width=True)
                    
                    if submit_btn:
                        selected_patient_data = get_patient_by_id(patient_id)
                        cond_cat = selected_patient_data["condition_category"] if selected_patient_data else "Other Chronic Condition"
                        
                        ok, msg, dref = record_discharge(
                            patient_id=patient_id,
                            facility_id=facility_id,
                            admission_date=adm_date.isoformat(),
                            discharge_date=dis_date.isoformat(),
                            diagnosis_summary=diagnosis,
                            condition_category=cond_cat,
                            followup_instructions=instructions,
                            recommended_appointment_date=rec_apt_date.isoformat(),
                            responsible_clinician=clinician,
                            discharge_support_needs=support_needs,
                            auto_schedule_appointment=auto_schedule,
                            actor_username=user.get("username", "system"),
                            actor_role=user.get("role", "Healthcare Provider")
                        )
                        if ok:
                            st.success(f"{msg} Discharge reference: {dref}")
                            st.rerun()
                        else:
                            st.error(msg)
