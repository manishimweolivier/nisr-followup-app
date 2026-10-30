"""
Authentication Module for FollowUp
Manages local login credentials, session persistence, and authorization guards.
"""

import streamlit as st
import config
from services.auth_service import authenticate_user, log_audit_action
from assets.logo import render_brand_header_html

def init_session_state():
    """Ensure essential authentication and session state variables are initialized."""
    if config.SESSION_AUTH not in st.session_state:
        st.session_state[config.SESSION_AUTH] = False
    if config.SESSION_USER not in st.session_state:
        st.session_state[config.SESSION_USER] = None
    if config.SESSION_ROLE not in st.session_state:
        st.session_state[config.SESSION_ROLE] = None

def render_login_screen():
    """Display the clinical authentication interface."""
    st.markdown(render_brand_header_html(), unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1.8, 1])
    with col2:
        st.markdown(
            """
            <div style="background-color: #ffffff; border: 1px solid #cbd5e1; border-radius: 8px; padding: 24px; box-shadow: 0 1px 3px rgba(0,0,0,0.06);">
                <div style="font-size: 1.15rem; font-weight: 600; color: #0f172a; margin-bottom: 4px;">
                    Healthcare Provider Authentication
                </div>
                <div style="font-size: 0.82rem; color: #475569; margin-bottom: 18px;">
                    Enter your authorized credentials to access patient continuity records.
                </div>
            """,
            unsafe_allow_html=True
        )
        
        with st.form("login_form", clear_on_submit=False):
            username = st.text_input("Username or Staff ID", placeholder="e.g. admin or dr.mucyo")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            submit_btn = st.form_submit_button("Sign In to FollowUp", use_container_width=True, type="primary")
            
            if submit_btn:
                if not username or not password:
                    st.error("Please enter both username and password.")
                else:
                    user_data = authenticate_user(username, password)
                    if user_data:
                        st.session_state[config.SESSION_AUTH] = True
                        st.session_state[config.SESSION_USER] = user_data
                        st.session_state[config.SESSION_ROLE] = user_data["role"]
                        st.success(f"Welcome, {user_data['full_name']}.")
                        st.rerun()
                    else:
                        st.error("Invalid username or password. Please verify your credentials.")
                        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Initial Access / Credentials Guidance
        with st.expander("Default System Accounts & Access Roles Reference", expanded=False):
            st.markdown(
                """
                **Pre-configured Accounts:**
                - **Administrator**: `admin` / `AdminSecure2026!` (Full system administration & user access)
                - **Healthcare Provider**: `dr.mucyo` / `Provider2026!` (Registration, clinical reviews, discharges)
                - **Nurse / Provider**: `nurse.keza` / `Provider2026!` (Clinical appointments, support plans)
                - **Follow-Up Officer**: `officer.aline` / `Officer2026!` (Home visits, follow-up calls, tasks)
                - **Read-Only Management**: `mgmt.director` / `Review2026!` (Dashboards, analytics, NISR indicators)
                """
            )

def render_sidebar_user_profile():
    """Render logged-in user details and sign out button in the navigation sidebar."""
    user = st.session_state.get(config.SESSION_USER)
    if not user:
        return
        
    st.sidebar.markdown(
        f"""
        <div class="sidebar-user-card">
            <div class="sidebar-user-name">{user.get('full_name', 'Healthcare Staff')}</div>
            <div class="sidebar-user-role">{user.get('role', 'User')}</div>
            <div class="sidebar-user-facility">{user.get('facility', 'Healthcare Facility')}</div>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    if st.sidebar.button("Sign Out", use_container_width=True):
        log_audit_action(
            username=user.get("username", "unknown"),
            role=user.get("role", "unknown"),
            action="USER_LOGOUT",
            target_type="User",
            target_ref=user.get("username", ""),
            details="User logged out of active session."
        )
        st.session_state[config.SESSION_AUTH] = False
        st.session_state[config.SESSION_USER] = None
        st.session_state[config.SESSION_ROLE] = None
        st.rerun()
