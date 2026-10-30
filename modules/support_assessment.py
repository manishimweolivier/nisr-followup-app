"""
Patient Support & Continuity Vulnerability Assessment Module for FollowUp
Evaluates social determinants of health, logistical barriers, and continuity risks
using transparent rule-based human decision support.
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date

import config
from services.support_service import (
    record_support_assessment,
    list_support_assessments,
    get_continuity_barrier_breakdown
)
from services.patient_service import search_patients, get_patient_by_id
from services.auth_service import check_permission
from utils.formatting import get_status_badge_html, format_date

def render_support_assessment_page():
    """Render the patient support and vulnerability assessment module."""
    user = st.session_state.get(config.SESSION_USER)
    can_edit = check_permission(user, [config.ROLE_ADMIN, config.ROLE_PROVIDER, config.ROLE_OFFICER])
    
    st.markdown(
        """
        <div style="margin-bottom: 16px;">
            <h2 style="color: #1e3a8a; margin-bottom: 2px; font-weight: 700;">Continuity Support & Vulnerability Assessment</h2>
            <div style="font-size: 0.85rem; color: #475569;">
                Systematically evaluate social determinants and logistical obstacles to facilitate proactive outreach.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Clinical Safety & Decision-Support Notice
    st.markdown(
        """
        <div class="health-notice-banner">
            <strong>Clinical Safety Disclaimer:</strong> Vulnerability tiers and barrier scores are administrative decision-support tools designed solely to identify logistical gaps and prioritize patient outreach. They are <strong>never</strong> medical diagnoses, prognostic predictions, or substitutes for qualified clinical judgment.
        </div>
        """,
        unsafe_allow_html=True
    )
    
    tab_list, tab_new = st.tabs(["Active Vulnerability Registry", "Conduct Structured Assessment"])
    
    # ---------------- TAB 1: ASSESSMENTS REGISTRY ----------------
    with tab_list:
        c1, c2 = st.columns([1.5, 2.5])
        with c1:
            sel_tier = st.selectbox("Filter Vulnerability Tier", ["All Tiers", config.VULNERABILITY_HIGH, config.VULNERABILITY_MODERATE, config.VULNERABILITY_LOW])
            
        assessments = list_support_assessments(tier=sel_tier)
        st.markdown(f"<div style='font-size: 0.82rem; color: #475569; margin: 8px 0;'>Showing <strong>{len(assessments)}</strong> recorded assessment(s)</div>", unsafe_allow_html=True)
        
        if not assessments:
            st.info("No recorded assessments match the filter.")
        else:
            for ass in assessments:
                barriers_list = []
                if ass["financial_difficulties"]: barriers_list.append("Financial constraints")
                if ass["transport_difficulties"]: barriers_list.append("Transport barrier")
                if ass["long_distance_facility"]: barriers_list.append("Distance > 1hr")
                if ass["lack_of_caregiver"]: barriers_list.append("No caregiver")
                if ass["medicine_access_difficulty"]: barriers_list.append("Medication refill barrier")
                if ass["repeated_missed_appointments"]: barriers_list.append("Prior missed visits")
                if ass["food_insecurity"]: barriers_list.append("Food insecurity")
                if ass["disability_mobility_barrier"]: barriers_list.append("Mobility limitation")
                
                with st.expander(f"{ass['assessment_ref']} - {ass['patient_name']} ({ass['patient_ref']}) | {ass['vulnerability_tier']} ({ass['vulnerability_score']}/8)", expanded=(ass['vulnerability_tier'] == config.VULNERABILITY_HIGH)):
                    col_a, col_b = st.columns([2, 1])
                    with col_a:
                        st.markdown(
                            f"""
                            <div style="font-size: 0.86rem; color: #0f172a; line-height: 1.5;">
                                <strong>Date Assessed:</strong> {format_date(ass['assessment_date'])} &bull; 
                                <strong>Assessor:</strong> {ass['assessor_name']} &bull; 
                                <strong>Condition:</strong> {ass['condition_category']}<br>
                                <strong>Catchment Facility:</strong> {ass['facility_name']} &bull; 
                                <strong>District:</strong> {ass['patient_district']}<br>
                                <strong>Documented Barriers:</strong> {', '.join(barriers_list) if barriers_list else 'None reported'}<br>
                                <strong>Recommended Support Actions:</strong> {ass['support_actions_recommended']}
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
                        if ass.get("review_notes"):
                            st.markdown(
                                f"<div style='margin-top: 6px; font-size: 0.82rem; color: #334155; background: #f8fafc; padding: 6px 10px; border-radius: 4px;'><strong>Multidisciplinary Notes:</strong> {ass['review_notes']}</div>",
                                unsafe_allow_html=True
                            )
                    with col_b:
                        st.markdown(f"Vulnerability Tier: {get_status_badge_html(ass['vulnerability_tier'])}", unsafe_allow_html=True)
                        st.markdown(f"<div style='font-size: 0.8rem; color: #475569; margin-top: 4px;'>Barrier Score: <strong>{ass['vulnerability_score']} of 8</strong></div>", unsafe_allow_html=True)
                        st.markdown(f"<div style='font-size: 0.8rem; color: #475569;'>Status: <strong>{ass['support_status']}</strong></div>", unsafe_allow_html=True)

    # ---------------- TAB 2: CONDUCT ASSESSMENT ----------------
    with tab_new:
        if not can_edit:
            st.warning("Only authorized clinical staff or follow-up officers can record vulnerability assessments.")
        else:
            all_patients = search_patients()
            if not all_patients:
                st.warning("No registered patients found.")
            else:
                pat_dict = {f"{p['patient_ref']} - {p['full_name']} ({p['condition_category']})": p for p in all_patients}
                
                with st.form("new_assessment_form"):
                    st.markdown("<div class='form-section-title'>1. Patient Identification</div>", unsafe_allow_html=True)
                    sel_p_label = st.selectbox("Select Patient to Assess *", list(pat_dict.keys()))
                    sel_p = pat_dict[sel_p_label]
                    
                    assessor = st.text_input("Assessor Staff Name *", value=user.get("full_name", ""))
                    
                    st.markdown("<div class='form-section-title'>2. Structured Continuity Barrier Screening (8 Key Indicators)</div>", unsafe_allow_html=True)
                    st.write("Screen for documented logistical and socioeconomic obstacles to care continuity:")
                    
                    c1, c2 = st.columns(2)
                    with c1:
                        f_fin = st.checkbox("1. Financial difficulties / Out-of-pocket costs", help="Patient or household lacks funds for consultation co-pays or required tests.")
                        f_trans = st.checkbox("2. Transportation difficulties", help="Lack of affordable transport or inaccessible roads.")
                        f_dist = st.checkbox("3. Long distance to facility (> 1 hour travel time)", help="Patient resides > 1 hour travel time from nearest health post/center.")
                        f_cg = st.checkbox("4. Lack of family or caregiver support", help="Patient lives alone, is elderly or lacks assistance for appointment attendance.")
                    with c2:
                        f_med = st.checkbox("5. Difficulty accessing prescribed medicines", help="Pharmacy stock-outs or inability to refill chronic prescriptions.")
                        f_miss = st.checkbox("6. History of repeated missed appointments", help="Patient has failed to attend one or more previous follow-up visits.")
                        f_food = st.checkbox("7. Food insecurity / nutritional constraints", help="Insufficient nutrition impacting metabolic control or medication timing.")
                        f_mob = st.checkbox("8. Physical disability or mobility limitation", help="Impaired ambulation preventing unassisted travel.")
                        
                    other_b = st.text_input("Other Documented Barriers (Optional)", placeholder="e.g. Seasonal agricultural migration, work conflict, language barrier")
                    
                    st.markdown("<div class='form-section-title'>3. Support Plan & Decision Directives</div>", unsafe_allow_html=True)
                    rec_actions = st.text_area("Recommended Support Plan & Human Review Directives", placeholder="Detail specific interventions: e.g. Assign CHW for home pill check; request transport voucher from social welfare fund; schedule case review.")
                    rev_notes = st.text_input("Review Notes / Team Coordination", placeholder="e.g. Discussed with social worker; community health worker assigned.")
                    
                    auto_task = st.checkbox("Automatically create high-priority follow-up task if High Continuity Risk is determined", value=True)
                    
                    sub_ass_btn = st.form_submit_button("Submit Vulnerability Assessment", type="primary", use_container_width=True)
                    
                    if sub_ass_btn:
                        ok, msg, aref = record_support_assessment(
                            patient_id=sel_p["id"],
                            assessor_name=assessor,
                            financial_difficulties=f_fin,
                            transport_difficulties=f_trans,
                            long_distance_facility=f_dist,
                            lack_of_caregiver=f_cg,
                            medicine_access_difficulty=f_med,
                            repeated_missed_appointments=f_miss,
                            food_insecurity=f_food,
                            disability_mobility_barrier=f_mob,
                            other_barriers=other_b,
                            support_actions_recommended=rec_actions,
                            review_notes=rev_notes,
                            auto_create_task=auto_task,
                            actor_username=user.get("username", "system"),
                            actor_role=user.get("role", "Healthcare Provider")
                        )
                        if ok:
                            st.success(f"{msg} Reference: {aref}")
                            st.rerun()
                        else:
                            st.error(msg)
