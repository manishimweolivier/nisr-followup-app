"""
Patient Management Module for FollowUp
Patient registration, comprehensive clinical profiles, search and filtering,
and longitudinal care timeline viewer.
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date

import config
from database.connection import execute_query
from services.patient_service import (
    register_patient,
    update_patient,
    search_patients,
    get_patient_by_id,
    get_patient_timeline
)
from services.followup_service import (
    list_appointments,
    get_followup_records_for_patient,
    schedule_appointment
)
from services.discharge_service import list_discharges
from services.support_service import list_support_assessments
from services.task_service import list_tasks
from services.auth_service import check_permission
from utils.formatting import get_status_badge_html, format_date
from utils.pdf_export import generate_patient_summary_pdf

def render_patients_page():
    """Render the main patient management module."""
    user = st.session_state.get(config.SESSION_USER)
    can_edit = check_permission(user, [config.ROLE_ADMIN, config.ROLE_PROVIDER])
    
    st.markdown(
        """
        <div style="margin-bottom: 16px;">
            <h2 style="color: #1e3a8a; margin-bottom: 2px; font-weight: 700;">Patient Care Registry & Profiles</h2>
            <div style="font-size: 0.85rem; color: #475569;">
                Comprehensive patient directory, longitudinal continuity profiles, and intake registration.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    tab_list, tab_register = st.tabs(["Patient Directory", "Register New Patient"])
    
    # ---------------- TAB 1: PATIENT DIRECTORY & PROFILES ----------------
    with tab_list:
        # Search and Filters Bar
        col_search, col_cond, col_fac, col_stat = st.columns([2, 1.5, 1.5, 1.2])
        
        facilities = execute_query("SELECT id, name FROM facilities WHERE is_active = 1 ORDER BY name")
        fac_dict = {"All Facilities": 0}
        for f in facilities:
            fac_dict[f["name"]] = f["id"]
            
        with col_search:
            search_query = st.text_input("Search Patient", placeholder="Search by name, reference code (e.g. FOL-2026-0001), or phone", label_visibility="collapsed")
        with col_cond:
            selected_cond = st.selectbox("Condition", ["All Conditions"] + config.CONDITION_CATEGORIES, label_visibility="collapsed")
        with col_fac:
            selected_fac = st.selectbox("Facility", list(fac_dict.keys()), label_visibility="collapsed")
        with col_stat:
            selected_stat = st.selectbox("Follow-Up Status", ["All Statuses", "Active Follow-Up", "Requires Review", "Completed", "Lost to Follow-Up"], label_visibility="collapsed")
            
        patients = search_patients(
            query=search_query,
            condition=selected_cond,
            facility_id=fac_dict[selected_fac],
            status=selected_stat
        )
        
        st.markdown(f"<div style='font-size: 0.82rem; color: #475569; margin: 8px 0;'>Showing <strong>{len(patients)}</strong> registered patient record(s)</div>", unsafe_allow_html=True)
        
        if not patients:
            st.info("No matching patient records found.")
        else:
            # Display patient directory table
            table_data = []
            for p in patients:
                table_data.append({
                    "ID": p["id"],
                    "Reference": p["patient_ref"],
                    "Full Name": p["full_name"],
                    "Age / Sex": f"{p['age']}y / {p['sex']}",
                    "Condition Category": p["condition_category"],
                    "Catchment Facility": p["facility_name"],
                    "District": p["district"],
                    "Status": p["followup_status"],
                    "Registered": format_date(p["registration_date"])
                })
                
            df_display = pd.DataFrame(table_data)
            st.dataframe(
                df_display.drop(columns=["ID"]),
                use_container_width=True,
                hide_index=True
            )
            
            # Patient Selection for Profile View
            st.markdown("<div class='form-section-title'>Inspect Detailed Continuity Profile</div>", unsafe_allow_html=True)
            col_sel, col_btn = st.columns([3, 1])
            with col_sel:
                patient_map = {f"{p['patient_ref']} - {p['full_name']} ({p['condition_category']})": p["id"] for p in patients}
                selected_label = st.selectbox("Select Patient to View Profile", list(patient_map.keys()), key="select_patient_view")
                selected_id = patient_map[selected_label]
                
            render_patient_profile_view(selected_id, can_edit, user)

    # ---------------- TAB 2: REGISTER NEW PATIENT ----------------
    with tab_register:
        if not can_edit:
            st.warning("Your current user role has Read-Only permissions. Registering patients requires Healthcare Provider or Administrator access.")
        else:
            render_patient_registration_form(facilities, user)

def render_patient_profile_view(patient_id: int, can_edit: bool, current_user: dict):
    """Render comprehensive multi-tab profile for the selected patient."""
    patient = get_patient_by_id(patient_id)
    if not patient:
        st.error("Patient profile could not be loaded.")
        return
        
    st.markdown(
        f"""
        <div style="background: #ffffff; border: 1px solid #cbd5e1; border-radius: 6px; padding: 18px; margin-top: 12px; margin-bottom: 20px;">
            <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 10px;">
                <div>
                    <span style="font-size: 0.8rem; font-weight: 700; color: #1e3a8a; background: #eff6ff; padding: 3px 8px; border-radius: 4px; border: 1px solid #bfdbfe;">
                        {patient['patient_ref']}
                    </span>
                    <h3 style="color: #0f172a; margin: 6px 0 2px 0; font-size: 1.35rem;">{patient['full_name']}</h3>
                    <div style="font-size: 0.82rem; color: #475569;">
                        {patient['age']} years &bull; {patient['sex']} &bull; {patient['condition_category']} &bull; Resident of {patient['district']} ({patient['sector'] or 'N/A'})
                    </div>
                </div>
                <div style="text-align: right;">
                    <div style="margin-bottom: 4px;">{get_status_badge_html(patient['followup_status'])}</div>
                    <div style="font-size: 0.78rem; color: #64748b;">Catchment: <strong>{patient['facility_name']}</strong></div>
                </div>
            </div>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 12px; margin-top: 14px; padding-top: 12px; border-top: 1px solid #e2e8f0; font-size: 0.82rem;">
                <div><strong>Primary Phone:</strong> {patient['phone_number'] or 'Not Provided'}</div>
                <div><strong>Alternate Phone:</strong> {patient['alternate_phone'] or 'None'}</div>
                <div><strong>Caregiver:</strong> {patient['caregiver_name'] or 'None'} ({patient['caregiver_phone'] or 'N/A'})</div>
                <div><strong>Registration Date:</strong> {format_date(patient['registration_date'])}</div>
            </div>
            {f"<div style='margin-top: 10px; font-size: 0.82rem; color: #334155; background: #f8fafc; padding: 8px 12px; border-radius: 4px;'><strong>Clinical Summary:</strong> {patient['clinical_summary']}</div>" if patient['clinical_summary'] else ""}
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Sub-tabs for clinical continuity record
    tab_timeline, tab_apts, tab_discharges, tab_flws, tab_support, tab_edit, tab_pdf = st.tabs([
        "Care Timeline", "Appointments", "Discharge Records", "Follow-Up Logs", "Support & Barriers", "Edit Details", "Export PDF"
    ])
    
    # 1. Timeline
    with tab_timeline:
        timeline = get_patient_timeline(patient_id)
        if not timeline:
            st.info("No recorded timeline events for this patient.")
        else:
            for ev in timeline:
                st.markdown(
                    f"""
                    <div style="border-left: 3px solid #1e3a8a; padding-left: 14px; margin-bottom: 14px;">
                        <div style="font-size: 0.76rem; color: #64748b; font-weight: 600;">{format_date(ev['date'])} &bull; {ev['event_type']}</div>
                        <div style="font-size: 0.92rem; font-weight: 600; color: #0f172a;">{ev['title']}</div>
                        <div style="font-size: 0.82rem; color: #334155; margin-top: 2px;">{ev['summary']}</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                
    # 2. Appointments
    with tab_apts:
        apts = list_appointments(patient_id=patient_id)
        if not apts:
            st.info("No scheduled appointments found.")
        else:
            for a in apts:
                st.markdown(
                    f"""
                    <div style="background: #ffffff; border: 1px solid #cbd5e1; border-radius: 4px; padding: 10px 14px; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <strong>{a['appointment_ref']}</strong> - {format_date(a['scheduled_date'])} ({a['scheduled_time'] or '09:00'}) &bull; <em>{a['followup_type']}</em>
                            <div style="font-size: 0.8rem; color: #475569;">Assigned: {a['responsible_worker']} | Notes: {a['outcome_notes'] or 'No notes'}</div>
                        </div>
                        <div>{get_status_badge_html(a['status'])}</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                
    # 3. Discharges
    with tab_discharges:
        discharges = list_discharges(condition=patient['condition_category'])
        patient_discharges = [d for d in discharges if d['patient_id'] == patient_id]
        if not patient_discharges:
            st.info("No hospital discharge records on file for this patient.")
        else:
            for d in patient_discharges:
                st.markdown(
                    f"""
                    <div style="background: #ffffff; border: 1px solid #cbd5e1; border-radius: 4px; padding: 12px; margin-bottom: 10px;">
                        <div style="display: flex; justify-content: space-between;">
                            <strong>{d['discharge_ref']} - Discharged {format_date(d['discharge_date'])}</strong>
                            <span>{get_status_badge_html(d['status'])}</span>
                        </div>
                        <div style="font-size: 0.82rem; color: #334155; margin-top: 4px;">
                            <strong>Admitted:</strong> {format_date(d['admission_date'])} &bull; <strong>Clinician:</strong> {d['responsible_clinician']}<br>
                            <strong>Diagnosis:</strong> {d['diagnosis_summary']}<br>
                            <strong>Discharge Instructions:</strong> {d['followup_instructions']}<br>
                            <strong>Recommended Next Visit:</strong> {format_date(d['recommended_appointment_date'])}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                
    # 4. Follow-Up Logs
    with tab_flws:
        flws = get_followup_records_for_patient(patient_id)
        if not flws:
            st.info("No interaction records logged yet.")
        else:
            for f in flws:
                st.markdown(
                    f"""
                    <div style="background: #ffffff; border: 1px solid #cbd5e1; border-radius: 4px; padding: 12px; margin-bottom: 10px;">
                        <div style="font-size: 0.88rem; font-weight: 600; color: #1e3a8a;">
                            {f['record_ref']} &bull; {format_date(f['interaction_date'])} &bull; {f['followup_type']}
                        </div>
                        <div style="font-size: 0.82rem; color: #334155; margin-top: 4px;">
                            <strong>Staff:</strong> {f['responsible_worker']} &bull; <strong>Adherence:</strong> {f['medication_adherence'] or 'N/A'}<br>
                            <strong>Status Summary:</strong> {f['patient_status_summary']}<br>
                            <strong>Action Taken:</strong> {f['action_taken']}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                
    # 5. Support & Barriers
    with tab_support:
        assessments = list_support_assessments(patient_id=patient_id)
        if not assessments:
            st.info("No structured vulnerability assessments recorded.")
        else:
            for ass in assessments:
                barriers = []
                if ass['financial_difficulties']: barriers.append("Financial Constraints")
                if ass['transport_difficulties']: barriers.append("Transport Difficulties")
                if ass['long_distance_facility']: barriers.append("Distance > 1hr")
                if ass['lack_of_caregiver']: barriers.append("No Caregiver")
                if ass['medicine_access_difficulty']: barriers.append("Med Refill Challenges")
                if ass['repeated_missed_appointments']: barriers.append("Repeated Missed Visits")
                if ass['food_insecurity']: barriers.append("Food Insecurity")
                if ass['disability_mobility_barrier']: barriers.append("Mobility Barrier")
                
                st.markdown(
                    f"""
                    <div style="background: #ffffff; border: 1px solid #cbd5e1; border-radius: 4px; padding: 12px; margin-bottom: 10px;">
                        <div style="display: flex; justify-content: space-between;">
                            <strong>{ass['assessment_ref']} - {format_date(ass['assessment_date'])}</strong>
                            <span>{get_status_badge_html(ass['vulnerability_tier'])}</span>
                        </div>
                        <div style="font-size: 0.82rem; color: #334155; margin-top: 4px;">
                            <strong>Assessor:</strong> {ass['assessor_name']} &bull; <strong>Score:</strong> {ass['vulnerability_score']}/8<br>
                            <strong>Identified Barriers:</strong> {', '.join(barriers) if barriers else 'None flagged'}<br>
                            <strong>Recommended Support Actions:</strong> {ass['support_actions_recommended']}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                
    # 6. Edit Details
    with tab_edit:
        if not can_edit:
            st.info("Read-only access. Modification requires Healthcare Provider role.")
        else:
            render_patient_edit_form(patient, current_user)
            
    # 7. Export PDF
    with tab_pdf:
        st.markdown("<div style='font-weight: 600; font-size: 0.95rem; color: #1e3a8a;'>Download Official Patient Continuity Summary (PDF)</div>", unsafe_allow_html=True)
        st.write("Generates a structured clinical continuity document containing demographics, appointments, and support history.")
        try:
            pdf_bytes = generate_patient_summary_pdf(
                patient=patient,
                appointments=list_appointments(patient_id=patient_id),
                followups=get_followup_records_for_patient(patient_id),
                assessments=list_support_assessments(patient_id=patient_id)
            )
            st.download_button(
                label=f"Download {patient['patient_ref']} Continuity PDF",
                data=pdf_bytes,
                file_name=f"Continuity_Summary_{patient['patient_ref']}.pdf",
                mime="application/pdf",
                type="primary"
            )
        except Exception as e:
            st.error(f"PDF generation error: {str(e)}")

def render_patient_registration_form(facilities: list, current_user: dict):
    """Render the patient registration form."""
    with st.form("patient_registration_form"):
        st.markdown("<div class='form-section-title'>1. Personal & Contact Information</div>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns([2, 1, 1])
        with c1:
            full_name = st.text_input("Full Name *", placeholder="e.g. Marie Louise Mukamwezi")
        with c2:
            age = st.number_input("Age (Years) *", min_value=0, max_value=120, value=45, step=1)
        with c3:
            sex = st.selectbox("Sex *", ["Female", "Male", "Other"])
            
        c4, c5 = st.columns(2)
        with c4:
            phone_number = st.text_input("Primary Telephone", placeholder="+250 788 000 000")
        with c5:
            alternate_phone = st.text_input("Alternate / Caregiver Phone", placeholder="+250 783 000 000")
            
        st.markdown("<div class='form-section-title'>2. Residence & Catchment Facility</div>", unsafe_allow_html=True)
        c6, c7, c8 = st.columns(3)
        with c6:
            district = st.text_input("District *", value="Nyarugenge", placeholder="e.g. Nyarugenge, Gasabo, Huye")
        with c7:
            sector = st.text_input("Sector", placeholder="e.g. Nyamirambo")
        with c8:
            cell = st.text_input("Cell / Village", placeholder="e.g. Mumena / Rugarama")
            
        fac_opts = {f["name"]: f["id"] for f in facilities}
        facility_name = st.selectbox("Assign Catchment Facility *", list(fac_opts.keys()))
        facility_id = fac_opts[facility_name]
        
        st.markdown("<div class='form-section-title'>3. Clinical Categorization & Follow-Up</div>", unsafe_allow_html=True)
        condition_category = st.selectbox("Chronic Condition Category *", config.CONDITION_CATEGORIES)
        clinical_summary = st.text_area("Clinical & Care Summary", placeholder="Enter diagnostic summary, primary prescribed medications, and specific follow-up goals.")
        
        c9, c10 = st.columns(2)
        with c9:
            caregiver_name = st.text_input("Designated Family Caregiver", placeholder="e.g. Emmanuel Niyonkuru (Brother)")
        with c10:
            initial_status = st.selectbox("Initial Follow-Up Status", ["Active Follow-Up", "Requires Review"])
            
        submit_btn = st.form_submit_button("Register Patient in Continuity System", type="primary", use_container_width=True)
        
        if submit_btn:
            success, msg, pref = register_patient(
                full_name=full_name,
                age=int(age),
                sex=sex,
                facility_id=facility_id,
                condition_category=condition_category,
                district=district,
                sector=sector,
                cell=cell,
                phone_number=phone_number,
                alternate_phone=alternate_phone,
                clinical_summary=clinical_summary,
                caregiver_name=caregiver_name,
                initial_status=initial_status,
                actor_username=current_user.get("username", "system"),
                actor_role=current_user.get("role", "Healthcare Provider")
            )
            if success:
                st.success(f"{msg} New patient reference: {pref}")
                st.rerun()
            else:
                st.error(msg)

def render_patient_edit_form(patient: dict, current_user: dict):
    """Render update form for existing patient."""
    facilities = execute_query("SELECT id, name FROM facilities WHERE is_active = 1 ORDER BY name")
    fac_opts = {f["name"]: f["id"] for f in facilities}
    
    with st.form("edit_patient_form"):
        e1, e2, e3 = st.columns([2, 1, 1])
        with e1:
            full_name = st.text_input("Full Name", value=patient["full_name"])
        with e2:
            age = st.number_input("Age", min_value=0, max_value=120, value=int(patient["age"]))
        with e3:
            sex = st.selectbox("Sex", ["Female", "Male", "Other"], index=["Female", "Male", "Other"].index(patient["sex"]) if patient["sex"] in ["Female", "Male", "Other"] else 0)
            
        e4, e5, e6 = st.columns(3)
        with e4:
            cond_idx = config.CONDITION_CATEGORIES.index(patient["condition_category"]) if patient["condition_category"] in config.CONDITION_CATEGORIES else 0
            cond = st.selectbox("Condition Category", config.CONDITION_CATEGORIES, index=cond_idx)
        with e5:
            stat_options = ["Active Follow-Up", "Requires Review", "Completed", "Lost to Follow-Up"]
            stat_idx = stat_options.index(patient["followup_status"]) if patient["followup_status"] in stat_options else 0
            stat = st.selectbox("Follow-Up Status", stat_options, index=stat_idx)
        with e6:
            fac_idx = list(fac_opts.values()).index(patient["facility_id"]) if patient["facility_id"] in fac_opts.values() else 0
            fac_name = st.selectbox("Facility", list(fac_opts.keys()), index=fac_idx)
            
        e7, e8, e9 = st.columns(3)
        with e7:
            district = st.text_input("District", value=patient["district"])
        with e8:
            sector = st.text_input("Sector", value=patient["sector"] or "")
        with e9:
            phone = st.text_input("Phone", value=patient["phone_number"] or "")
            
        clin = st.text_area("Clinical Summary", value=patient["clinical_summary"] or "")
        
        save_btn = st.form_submit_button("Save Patient Record Updates", type="primary")
        if save_btn:
            ok, msg = update_patient(
                patient_id=patient["id"],
                full_name=full_name,
                age=int(age),
                sex=sex,
                facility_id=fac_opts[fac_name],
                condition_category=cond,
                district=district,
                followup_status=stat,
                sector=sector,
                phone_number=phone,
                clinical_summary=clin,
                caregiver_name=patient["caregiver_name"],
                caregiver_phone=patient["caregiver_phone"],
                actor_username=current_user.get("username", "system"),
                actor_role=current_user.get("role", "Healthcare Provider")
            )
            if ok:
                st.success(msg)
                st.rerun()
            else:
                st.error(msg)
