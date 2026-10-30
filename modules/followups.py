"""
Follow-Up Visits & Outcomes Module for FollowUp
Records in-person clinical consultations, home tracer visits, and telephone check-ins,
documenting medication adherence, continuity barriers, and next steps.
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta

import config
from services.followup_service import (
    record_followup_interaction,
    list_appointments,
    get_followup_records_for_patient
)
from services.patient_service import search_patients, get_patient_by_id
from services.auth_service import check_permission
from utils.formatting import format_date, get_status_badge_html

def render_followups_page():
    """Render the follow-up visits and outcomes module."""
    user = st.session_state.get(config.SESSION_USER)
    can_edit = check_permission(user, [config.ROLE_ADMIN, config.ROLE_PROVIDER, config.ROLE_OFFICER])
    
    st.markdown(
        """
        <div style="margin-bottom: 16px;">
            <h2 style="color: #1e3a8a; margin-bottom: 2px; font-weight: 700;">Follow-Up Visits & Patient Outcomes</h2>
            <div style="font-size: 0.85rem; color: #475569;">
                Document clinic encounters, CHW community home visits, and phone monitoring calls.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    tab_record, tab_history = st.tabs(["Record Follow-Up Encounter", "Chronological Encounter Log"])
    
    # Check if an active appointment was passed from the Appointments screen
    preset_apt = st.session_state.get("active_apt_for_record", None)
    
    # ---------------- TAB 1: RECORD VISIT ----------------
    with tab_record:
        if not can_edit:
            st.warning("Only Healthcare Providers or Follow-Up Officers can record follow-up outcomes.")
        else:
            all_patients = search_patients()
            if not all_patients:
                st.warning("No registered patients found.")
            else:
                pat_dict = {f"{p['patient_ref']} - {p['full_name']} ({p['condition_category']})": p for p in all_patients}
                
                # Determine default patient index if preset from another screen
                default_idx = 0
                if preset_apt:
                    preset_ref = preset_apt.get("patient_ref")
                    for idx, label in enumerate(pat_dict.keys()):
                        if preset_ref in label:
                            default_idx = idx
                            break
                            
                with st.form("record_followup_form"):
                    st.markdown("<div class='form-section-title'>1. Encounter Details & Modality</div>", unsafe_allow_html=True)
                    sel_patient_label = st.selectbox("Select Patient *", list(pat_dict.keys()), index=default_idx)
                    sel_pat = pat_dict[sel_patient_label]
                    
                    c1, c2, c3 = st.columns([1.5, 1.5, 1.2])
                    with c1:
                        interaction_date = st.date_input("Encounter Date *", value=date.today())
                    with c2:
                        followup_type = st.selectbox("Encounter Modality *", config.FOLLOWUP_TYPES, 
                                                    index=config.FOLLOWUP_TYPES.index(preset_apt["followup_type"]) if preset_apt and preset_apt.get("followup_type") in config.FOLLOWUP_TYPES else 0)
                    with c3:
                        worker = st.text_input("Healthcare Staff *", value=user.get("full_name", ""))
                        
                    # Check linked appointment
                    apt_id = None
                    if preset_apt and preset_apt.get("patient_id") == sel_pat["id"]:
                        st.info(f"Linking encounter to appointment: {preset_apt['appointment_ref']} ({format_date(preset_apt['scheduled_date'])})")
                        apt_id = preset_apt["id"]
                    else:
                        # Find open appointments for this patient
                        open_apts = [a for a in list_appointments(patient_id=sel_pat["id"]) if a["status"] in ["Scheduled", "Due", "Missed"]]
                        if open_apts:
                            apt_options = {"None (Unscheduled / Ad-hoc check-in)": None}
                            for a in open_apts:
                                apt_options[f"{a['appointment_ref']} - {format_date(a['scheduled_date'])} ({a['status']})"] = a["id"]
                            sel_apt_label = st.selectbox("Link to Existing Appointment", list(apt_options.keys()))
                            apt_id = apt_options[sel_apt_label]
                            
                    st.markdown("<div class='form-section-title'>2. Clinical Status & Adherence Evaluation</div>", unsafe_allow_html=True)
                    c4, c5 = st.columns(2)
                    with c4:
                        adherence = st.selectbox("Medication Adherence Status", ["Full", "Partial", "Interrupted", "Not Applicable"])
                    with c5:
                        patient_status_summary = st.text_input("Current Patient Clinical Status *", placeholder="e.g. Asymptomatic, blood pressure 130/85, no peripheral edema")
                        
                    st.markdown("<div class='form-section-title'>3. Documented Continuity Barriers</div>", unsafe_allow_html=True)
                    st.write("Select any social, logistical, or financial barriers reported during this interaction:")
                    
                    b_cols = st.columns(3)
                    with b_cols[0]:
                        b_fin = st.checkbox("Financial constraints / medication cost")
                        b_trans = st.checkbox("Transportation difficulties")
                        b_dist = st.checkbox("Long distance to facility (> 1hr)")
                    with b_cols[1]:
                        b_cg = st.checkbox("Lack of family/caregiver support")
                        b_refill = st.checkbox("Difficulty refilling prescriptions")
                        b_mob = st.checkbox("Disability or mobility limitations")
                    with b_cols[2]:
                        b_food = st.checkbox("Food insecurity")
                        b_stigma = st.checkbox("Stigma / psychological distress")
                        b_work = st.checkbox("Livelihood / work conflict")
                        
                    st.markdown("<div class='form-section-title'>4. Action Taken & Next Steps</div>", unsafe_allow_html=True)
                    action_taken = st.text_area("Action Taken During Encounter *", placeholder="e.g. Conducted clinical exam, dispensed 60-day medication refill, verified inhaler technique, coordinated transport voucher.")
                    
                    c6, c7 = st.columns(2)
                    with c6:
                        next_steps = st.text_input("Next Support Directives / Recommendations", placeholder="e.g. Continue home blood pressure diary; schedule dietitian consult")
                    with c7:
                        schedule_next = st.checkbox("Schedule Next Continuity Follow-Up Appointment", value=True)
                        next_date = st.date_input("Next Follow-Up Date", value=date.today() + timedelta(days=30))
                        
                    submit_btn = st.form_submit_button("Save Follow-Up Encounter Record", type="primary", use_container_width=True)
                    
                    if submit_btn:
                        barriers_selected = []
                        if b_fin: barriers_selected.append("Financial constraints")
                        if b_trans: barriers_selected.append("Transportation difficulties")
                        if b_dist: barriers_selected.append("Long distance to facility")
                        if b_cg: barriers_selected.append("Lack of caregiver support")
                        if b_refill: barriers_selected.append("Difficulty refilling prescriptions")
                        if b_mob: barriers_selected.append("Disability/mobility limitations")
                        if b_food: barriers_selected.append("Food insecurity")
                        if b_stigma: barriers_selected.append("Stigma/psychological distress")
                        if b_work: barriers_selected.append("Work/livelihood conflict")
                        
                        ok, msg, fref = record_followup_interaction(
                            patient_id=sel_pat["id"],
                            interaction_date=interaction_date.isoformat(),
                            followup_type=followup_type,
                            responsible_worker=worker,
                            patient_status_summary=patient_status_summary,
                            action_taken=action_taken,
                            appointment_id=apt_id,
                            medication_adherence=adherence,
                            reported_barriers=barriers_selected,
                            next_steps=next_steps,
                            next_followup_date=next_date.isoformat() if schedule_next else None,
                            actor_username=user.get("username", "system"),
                            actor_role=user.get("role", "Healthcare Provider")
                        )
                        if ok:
                            st.success(f"{msg} Encounter Reference: {fref}")
                            if "active_apt_for_record" in st.session_state:
                                del st.session_state["active_apt_for_record"]
                            st.rerun()
                        else:
                            st.error(msg)

    # ---------------- TAB 2: HISTORY ----------------
    with tab_history:
        all_patients = search_patients()
        if not all_patients:
            st.info("No registered patients found.")
        else:
            pat_map = {f"{p['patient_ref']} - {p['full_name']}": p["id"] for p in all_patients}
            sel_pat_h = st.selectbox("Select Patient to View Encounter History", list(pat_map.keys()), key="hist_pat_sel")
            patient_id_h = pat_map[sel_pat_h]
            
            records = get_followup_records_for_patient(patient_id_h)
            if not records:
                st.info("No follow-up interaction records logged for this patient.")
            else:
                st.markdown(f"<div style='font-size: 0.82rem; color: #475569; margin-bottom: 12px;'>Showing <strong>{len(records)}</strong> interaction record(s)</div>", unsafe_allow_html=True)
                for r in records:
                    with st.expander(f"{r['record_ref']} - {format_date(r['interaction_date'])} ({r['followup_type']})", expanded=True):
                        st.markdown(
                            f"""
                            <div style="font-size: 0.85rem; color: #0f172a; line-height: 1.5;">
                                <strong>Date:</strong> {format_date(r['interaction_date'])} &bull; 
                                <strong>Modality:</strong> {r['followup_type']} &bull; 
                                <strong>Healthcare Worker:</strong> {r['responsible_worker']}<br>
                                <strong>Medication Adherence:</strong> {r['medication_adherence'] or 'Not Recorded'}<br>
                                <strong>Patient Clinical Status:</strong> {r['patient_status_summary']}<br>
                                <strong>Action Taken:</strong> {r['action_taken']}<br>
                                <strong>Next Steps:</strong> {r['next_steps'] or 'None recorded'}<br>
                                <strong>Next Recommended Date:</strong> {format_date(r['next_followup_date']) if r.get('next_followup_date') else 'Not specified'}
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
