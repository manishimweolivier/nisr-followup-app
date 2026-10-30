"""
User Management & Administration Module for FollowUp
Manages user accounts, role allocations, system audit logs, and demo data reset.
"""

import streamlit as st
import pandas as pd
from datetime import datetime

import config
from database.connection import execute_query
from services.auth_service import (
    list_all_users,
    create_user,
    update_user_status,
    check_permission
)
from data.demo_data import seed_demo_data, reset_demo_data
from utils.formatting import get_status_badge_html, format_date

def render_user_management_page():
    """Render the user administration and security module."""
    user = st.session_state.get(config.SESSION_USER)
    if not check_permission(user, [config.ROLE_ADMIN]):
        st.error("Access Restricted: User management and system administration require Administrator privileges.")
        return
        
    st.markdown(
        """
        <div style="margin-bottom: 16px;">
            <h2 style="color: #1e3a8a; margin-bottom: 2px; font-weight: 700;">System Administration & User Access</h2>
            <div style="font-size: 0.85rem; color: #475569;">
                Manage authorized healthcare personnel credentials, access roles, audit records, and demo data.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    tab_users, tab_new_user, tab_audit, tab_demo = st.tabs([
        "Authorized Users", "Create User Account", "Security Audit Logs", "Demonstration Data Controls"
    ])
    
    # ---------------- TAB 1: USERS DIRECTORY ----------------
    with tab_users:
        users = list_all_users()
        st.markdown(f"<div style='font-size: 0.82rem; color: #475569; margin-bottom: 12px;'>Showing <strong>{len(users)}</strong> authorized user account(s)</div>", unsafe_allow_html=True)
        
        for u in users:
            with st.container():
                st.markdown(
                    f"""
                    <div style="background: #ffffff; border: 1px solid #cbd5e1; border-radius: 6px; padding: 12px 16px; margin-bottom: 10px;">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <div>
                                <span style="font-weight: 700; color: #1e3a8a; font-size: 0.95rem;">{u['full_name']}</span> &bull; 
                                <span style="color: #475569; font-size: 0.85rem;">@{u['username']}</span>
                                <div style="font-size: 0.82rem; color: #334155; margin-top: 2px;">
                                    <strong>Role:</strong> {u['role']} &bull; 
                                    <strong>Facility:</strong> {u['facility']} &bull; 
                                    <strong>Email:</strong> {u['email'] or 'Not provided'}
                                </div>
                                <div style="font-size: 0.78rem; color: #64748b; margin-top: 2px;">
                                    Created: {format_date(u['created_at'])} &bull; Last Login: {format_date(u['last_login']) if u.get('last_login') else 'Never'}
                                </div>
                            </div>
                            <div style="text-align: right;">
                                <span style="padding: 3px 8px; border-radius: 4px; font-size: 0.76rem; font-weight: 600; background: {'#ecfdf5' if u['is_active'] else '#fef2f2'}; color: {'#047857' if u['is_active'] else '#b91c1c'}; border: 1px solid {'#a7f3d0' if u['is_active'] else '#fecaca'};">
                                    {'Active' if u['is_active'] else 'Deactivated'}
                                </span>
                            </div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                
                # Deactivate / Activate action (cannot deactivate self)
                if u["username"] != user.get("username"):
                    c_tog, c_sp = st.columns([1.5, 4])
                    with c_tog:
                        if u["is_active"]:
                            if st.button("Deactivate Account", key=f"deact_{u['id']}", type="secondary"):
                                update_user_status(u["id"], 0, user.get("username", "admin"))
                                st.warning(f"Account @{u['username']} deactivated.")
                                st.rerun()
                        else:
                            if st.button("Reactivate Account", key=f"react_{u['id']}", type="primary"):
                                update_user_status(u["id"], 1, user.get("username", "admin"))
                                st.success(f"Account @{u['username']} reactivated.")
                                st.rerun()

    # ---------------- TAB 2: CREATE USER ----------------
    with tab_new_user:
        facilities = execute_query("SELECT name FROM facilities WHERE is_active = 1 ORDER BY name")
        fac_names = [f["name"] for f in facilities]
        
        with st.form("create_user_form"):
            st.markdown("<div class='form-section-title'>User Identity & Role Access</div>", unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            with c1:
                uname = st.text_input("Username *", placeholder="e.g. dr.kayitare")
                fname = st.text_input("Staff Full Name *", placeholder="e.g. Dr. Jean Kayitare, MD")
            with c2:
                email = st.text_input("Email Address *", placeholder="e.g. j.kayitare@followup.health.rw")
                role = st.selectbox("Authorization Role *", config.ALL_ROLES)
                
            c3, c4 = st.columns(2)
            with c3:
                facility = st.selectbox("Assigned Facility *", fac_names)
            with c4:
                pwd = st.text_input("Initial Password *", type="password", placeholder="Minimum 6 characters")
                
            submit_user = st.form_submit_button("Create User Account", type="primary")
            if submit_user:
                ok, msg = create_user(
                    username=uname,
                    full_name=fname,
                    email=email,
                    plain_password=pwd,
                    role=role,
                    facility=facility,
                    actor_username=user.get("username", "admin")
                )
                if ok:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)

    # ---------------- TAB 3: AUDIT LOGS ----------------
    with tab_audit:
        st.markdown("<div style='font-weight: 600; font-size: 0.92rem; color: #1e3a8a; margin-bottom: 8px;'>Immutable Healthcare System Audit Trail</div>", unsafe_allow_html=True)
        logs = execute_query("SELECT timestamp, username, role, action, target_type, target_ref, details FROM audit_logs ORDER BY id DESC LIMIT 100")
        if not logs:
            st.info("No audit logs recorded yet.")
        else:
            df_logs = pd.DataFrame([dict(l) for l in logs])
            st.dataframe(df_logs, use_container_width=True, hide_index=True)

    # ---------------- TAB 4: DEMO CONTROLS ----------------
    with tab_demo:
        st.markdown("<div style='font-weight: 600; font-size: 0.92rem; color: #1e3a8a; margin-bottom: 6px;'>Fictional Demonstration Dataset Controls</div>", unsafe_allow_html=True)
        st.write("Initialize or reset the pre-packaged fictional demonstration patients, discharges, appointments, and support assessments.")
        
        st.markdown(
            """
            <div class="health-notice-banner">
                <strong>Data Protection Safeguard:</strong> Demonstration records are strictly tagged with <code>is_demo = 1</code>. Resetting demonstration data safely removes only fictional test cases and preserves all genuine user-registered patient records (<code>is_demo = 0</code>).
            </div>
            """,
            unsafe_allow_html=True
        )
        
        col_d1, col_d2 = st.columns(2)
        with col_d1:
            if st.button("Re-seed Demonstration Data", type="primary", use_container_width=True):
                count = seed_demo_data(force_reset=True)
                st.success(f"Demonstration dataset re-initialized with {count} fictional clinical scenarios.")
                st.rerun()
        with col_d2:
            if st.button("Clear Demonstration Data", type="secondary", use_container_width=True):
                reset_demo_data()
                st.warning("All fictional demonstration records removed. Genuine user records preserved.")
                st.rerun()
