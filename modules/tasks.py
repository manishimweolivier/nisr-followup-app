"""
Follow-Up Task Management Module for FollowUp
Coordinates task assignments, priority triage, deadline tracking, and action updates.
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta

import config
from services.task_service import (
    create_task,
    update_task_status,
    list_tasks
)
from services.patient_service import search_patients
from services.auth_service import check_permission, list_all_users
from utils.formatting import get_status_badge_html, format_date

def render_tasks_page():
    """Render the follow-up task coordination module."""
    user = st.session_state.get(config.SESSION_USER)
    can_edit = check_permission(user, [config.ROLE_ADMIN, config.ROLE_PROVIDER, config.ROLE_OFFICER])
    
    st.markdown(
        """
        <div style="margin-bottom: 16px;">
            <h2 style="color: #1e3a8a; margin-bottom: 2px; font-weight: 700;">Follow-Up Task Management</h2>
            <div style="font-size: 0.85rem; color: #475569;">
                Assign, monitor, and resolve outreach duties, home tracer visits, and multidisciplinary reviews.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    tab_tasks, tab_create = st.tabs(["Active Task Board", "Create Follow-Up Task"])
    
    # ---------------- TAB 1: TASK BOARD ----------------
    with tab_tasks:
        col_f1, col_f2, col_f3, col_f4 = st.columns([1.5, 1.2, 1.2, 1.2])
        
        users_list = list_all_users()
        user_names = ["All Assignees"] + sorted(list(set([u["full_name"] for u in users_list])))
        
        with col_f1:
            sel_assignee = st.selectbox("Assignee", user_names, label_visibility="collapsed")
        with col_f2:
            sel_status = st.selectbox("Status", ["All Statuses"] + config.ALL_TASK_STATUSES, label_visibility="collapsed")
        with col_f3:
            sel_pri = st.selectbox("Priority", ["All Priorities"] + config.ALL_TASK_PRIORITIES, label_visibility="collapsed")
        with col_f4:
            only_overdue = st.checkbox("Only Overdue", value=False)
            
        tasks = list_tasks(
            assigned_to=sel_assignee,
            status=sel_status,
            priority=sel_pri,
            only_overdue=only_overdue
        )
        
        st.markdown(f"<div style='font-size: 0.82rem; color: #475569; margin: 8px 0;'>Showing <strong>{len(tasks)}</strong> task(s)</div>", unsafe_allow_html=True)
        
        if not tasks:
            st.info("No tasks found matching the criteria.")
        else:
            for t in tasks:
                with st.expander(f"{t['task_ref']} - {t['title']} | Priority: {t['priority']} | Due: {format_date(t['due_date'])}", expanded=(t['status'] in ['Pending', 'In Progress'])):
                    col_t1, col_t2 = st.columns([2.5, 1.5])
                    with col_t1:
                        st.markdown(
                            f"""
                            <div style="font-size: 0.86rem; color: #0f172a; line-height: 1.5;">
                                <strong>Patient:</strong> {t['patient_name']} ({t['patient_ref']}) &bull; 
                                <strong>Facility:</strong> {t['facility_name']}<br>
                                <strong>Assigned To:</strong> {t['assigned_to']} &bull; 
                                <strong>Assigned By:</strong> {t['assigned_by']}<br>
                                <strong>Deadline:</strong> {format_date(t['due_date'])} {f"<span style='color: #dc2626; font-weight: 700;'>(OVERDUE)</span>" if t.get('is_overdue') else ""}<br>
                                <strong>Description:</strong> {t['description']}
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
                        if t.get("action_taken"):
                            comp_txt = f"(Completed on {format_date(t['completion_date'])})" if t.get('completion_date') else ""
                            st.markdown(
                                f"<div style='margin-top: 6px; font-size: 0.82rem; color: #047857; background: #ecfdf5; padding: 6px 10px; border-radius: 4px;'><strong>Action Taken:</strong> {t['action_taken']} {comp_txt}</div>",
                                unsafe_allow_html=True
                            )
                    with col_t2:
                        st.markdown(f"Status: {get_status_badge_html(t['status'])}", unsafe_allow_html=True)
                        st.markdown(f"Priority: {get_status_badge_html(t['priority'])}", unsafe_allow_html=True)
                        
                        if can_edit and t['status'] != config.TASK_STATUS_COMPLETED:
                            st.markdown("<hr style='margin: 8px 0; border: none; border-top: 1px solid #e2e8f0;'>", unsafe_allow_html=True)
                            with st.popover(f"Update Task {t['task_ref']}"):
                                render_update_task_popover(t, user)

    # ---------------- TAB 2: CREATE TASK ----------------
    with tab_create:
        if not can_edit:
            st.warning("Only authorized clinical staff or officers can assign tasks.")
        else:
            all_patients = search_patients()
            if not all_patients:
                st.warning("No registered patients found.")
            else:
                pat_dict = {f"{p['patient_ref']} - {p['full_name']} ({p['condition_category']})": p for p in all_patients}
                staff_names = [u["full_name"] for u in list_all_users() if u.get("is_active")]
                
                with st.form("create_task_form"):
                    st.markdown("<div class='form-section-title'>1. Target Patient & Assignment</div>", unsafe_allow_html=True)
                    sel_p_label = st.selectbox("Select Target Patient *", list(pat_dict.keys()))
                    sel_p = pat_dict[sel_p_label]
                    
                    c1, c2 = st.columns(2)
                    with c1:
                        assigned_to = st.selectbox("Assign To Staff *", staff_names)
                    with c2:
                        priority = st.selectbox("Priority Level *", config.ALL_TASK_PRIORITIES, index=1)
                        
                    st.markdown("<div class='form-section-title'>2. Task Directives & Deadline</div>", unsafe_allow_html=True)
                    title = st.text_input("Task Title *", placeholder="e.g. Conduct Home Tracer Visit for Missed Oncology Cycle")
                    description = st.text_area("Detailed Action Directives *", placeholder="Specify actions required: verify patient residence in sector, assess transport barrier, deliver medicine refill, coordinate clinician phone consult.")
                    
                    c3, c4 = st.columns(2)
                    with c3:
                        due_date = st.date_input("Deadline Date *", value=date.today() + timedelta(days=2))
                    with c4:
                        assigned_by = st.text_input("Assigned By", value=user.get("full_name", "Clinical Lead"))
                        
                    submit_btn = st.form_submit_button("Create & Assign Task", type="primary", use_container_width=True)
                    if submit_btn:
                        ok, msg, tref = create_task(
                            patient_id=sel_p["id"],
                            title=title,
                            description=description,
                            assigned_to=assigned_to,
                            assigned_by=assigned_by,
                            priority=priority,
                            due_date_str=due_date.isoformat(),
                            actor_username=user.get("username", "system"),
                            actor_role=user.get("role", "Healthcare Provider")
                        )
                        if ok:
                            st.success(f"{msg} Task Reference: {tref}")
                            st.rerun()
                        else:
                            st.error(msg)

def render_update_task_popover(task: dict, current_user: dict):
    """Render inline popover to update task progress."""
    st.markdown(f"<strong>Update {task['task_ref']}</strong>", unsafe_allow_html=True)
    new_stat = st.selectbox(
        "Status",
        config.ALL_TASK_STATUSES,
        index=config.ALL_TASK_STATUSES.index(task["status"]) if task["status"] in config.ALL_TASK_STATUSES else 0,
        key=f"task_stat_sel_{task['id']}"
    )
    action_text = st.text_area(
        "Action Taken / Resolution Summary",
        value=task.get("action_taken") or "",
        placeholder="e.g. Visited patient at home; delivered 30-day insulin refill and confirmed next visit.",
        key=f"task_act_txt_{task['id']}"
    )
    if st.button("Save Task Status", key=f"save_task_{task['id']}", type="primary"):
        ok, msg = update_task_status(
            task_id=task["id"],
            new_status=new_stat,
            action_taken=action_text,
            actor_username=current_user.get("username", "system"),
            actor_role=current_user.get("role", "Healthcare Provider")
        )
        if ok:
            st.success(msg)
            st.rerun()
        else:
            st.error(msg)
