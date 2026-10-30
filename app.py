"""
FollowUp: Patient Continuity-of-Care and Follow-Up Management System
Main Streamlit Application Entrypoint.
A self-contained, fully local healthcare information management application.
"""

import streamlit as st
from pathlib import Path

# Configure page settings before any other Streamlit calls
st.set_page_config(
    page_title="FollowUp | Patient Continuity-of-Care System",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

import config
from database.initialization import initialize_database
from data.demo_data import seed_demo_data
from assets.logo import render_sidebar_brand_html, render_brand_header_html
from modules.authentication import init_session_state, render_login_screen, render_sidebar_user_profile
from modules.overview import render_overview_page
from modules.patients import render_patients_page
from modules.discharges import render_discharges_page
from modules.appointments import render_appointments_page
from modules.followups import render_followups_page
from modules.support_assessment import render_support_assessment_page
from modules.tasks import render_tasks_page
from modules.reports import render_reports_page
from modules.statistical_data import render_statistical_data_page
from modules.user_management import render_user_management_page
from services.auth_service import check_permission

def load_custom_css():
    """Inject clean clinical styles from assets/styles.css."""
    css_file = config.BASE_DIR / "assets" / "styles.css"
    if css_file.exists():
        with open(css_file, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

def main():
    """Main application lifecycle and routing."""
    # Ensure persistent database and baseline tables exist
    initialize_database()
    
    # Automatically seed fictional demonstration scenarios on first local launch
    seed_demo_data()
    
    # Inject styling
    load_custom_css()
    
    # Initialize authentication session state
    init_session_state()
    
    # If not logged in, render the login authentication interface
    if not st.session_state.get(config.SESSION_AUTH, False):
        render_login_screen()
        return
        
    current_user = st.session_state.get(config.SESSION_USER, {})
    user_role = current_user.get("role", config.ROLE_READONLY)
    
    # Sidebar Navigation Branding & Profile
    st.sidebar.markdown(render_sidebar_brand_html(), unsafe_allow_html=True)
    render_sidebar_user_profile()
    
    # Navigation Menu
    nav_options = [
        "Overview Dashboard",
        "Patient Management",
        "Discharge Management",
        "Appointments & Schedule",
        "Follow-Up Visits & Logs",
        "Support & Vulnerability",
        "Follow-Up Tasks",
        "Reports & Analytics",
        "NISR Population Statistics"
    ]
    
    # Only show User Management & System Controls to Administrators
    if check_permission(current_user, [config.ROLE_ADMIN]):
        nav_options.append("User Management & Admin")
        
    st.sidebar.markdown("<div style='font-size: 0.72rem; font-weight: 700; color: #64748b; text-transform: uppercase; letter-spacing: 0.05em; margin: 12px 0 6px 4px;'>Navigation Modules</div>", unsafe_allow_html=True)
    
    selected_module = st.sidebar.radio(
        "Navigation",
        nav_options,
        label_visibility="collapsed"
    )
    
    # Render Application Top Header Banner
    st.markdown(render_brand_header_html(), unsafe_allow_html=True)
    
    # Route to Selected Module
    if selected_module == "Overview Dashboard":
        render_overview_page()
    elif selected_module == "Patient Management":
        render_patients_page()
    elif selected_module == "Discharge Management":
        render_discharges_page()
    elif selected_module == "Appointments & Schedule":
        render_appointments_page()
    elif selected_module == "Follow-Up Visits & Logs":
        render_followups_page()
    elif selected_module == "Support & Vulnerability":
        render_support_assessment_page()
    elif selected_module == "Follow-Up Tasks":
        render_tasks_page()
    elif selected_module == "Reports & Analytics":
        render_reports_page()
    elif selected_module == "NISR Population Statistics":
        render_statistical_data_page()
    elif selected_module == "User Management & Admin":
        render_user_management_page()

if __name__ == "__main__":
    main()
