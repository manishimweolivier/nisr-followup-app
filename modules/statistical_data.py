"""
NISR Statistical Data & Population Insights Module for FollowUp
Presents official aggregate socioeconomic and health access indicators from Rwanda's
National Institute of Statistics (NISR) EICV7 survey (2023/24) with strict separation
between population survey statistics and individual patient clinical records.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

import config
from services.statistical_service import (
    get_nisr_district_indicators,
    get_nisr_national_summary,
    get_registered_patients_by_district,
    import_custom_nisr_dataset,
    list_imported_datasets
)
from services.auth_service import check_permission
from utils.formatting import format_date, get_status_badge_html

def render_statistical_data_page():
    """Render the official NISR statistical data and population insights module."""
    user = st.session_state.get(config.SESSION_USER)
    can_import = check_permission(user, [config.ROLE_ADMIN, config.ROLE_PROVIDER])
    
    st.markdown(
        """
        <div style="margin-bottom: 16px;">
            <h2 style="color: #1e3a8a; margin-bottom: 2px; font-weight: 700;">NISR Population Statistics & Socioeconomic Context</h2>
            <div style="font-size: 0.85rem; color: #475569;">
                Official population-level indicators from Rwanda's National Institute of Statistics (NISR) EICV7 survey.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Mandatory Data Source & Privacy Distinction Notice
    st.markdown(
        """
        <div class="health-notice-banner" style="border-left-color: #0284c7;">
            <strong>Important Statistical Distinction & Privacy Standards:</strong>
            <br>
            &bull; <strong>Statistical Survey Data:</strong> Describes aggregate population demographics, household living conditions, and geographic patterns across Rwanda's 30 districts (NISR EICV7 2023/24).
            <br>
            &bull; <strong>Patient Clinical Records:</strong> Describe individual patients receiving continuing care at local partner hospitals.
            <br>
            <em>These are distinct data sources. NISR household survey datasets do not contain individual patient identities, clinical charts, hospital discharges, or real-time appointment records.</em>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    tab_overview, tab_district_explorer, tab_catchment_cross, tab_import, tab_metadata = st.tabs([
        "National Aggregate Benchmarks", "District Indicator Explorer", "Catchment & Vulnerability Cross-Analysis", "Import Statistical CSV", "Dataset Metadata & Source"
    ])
    
    # ---------------- TAB 1: NATIONAL SUMMARY ----------------
    with tab_overview:
        summary = get_nisr_national_summary()
        if not summary:
            st.info("No NISR indicators loaded. Please check database initialization.")
        else:
            st.markdown(
                f"""
                <div class="metric-container-grid">
                    <div class="metric-card-pro">
                        <div class="metric-card-label">Surveyed Districts</div>
                        <div class="metric-card-value">{summary['total_districts']}</div>
                        <div class="metric-card-caption">All 30 administrative districts</div>
                    </div>
                    <div class="metric-card-pro">
                        <div class="metric-card-label">Avg Health Insurance</div>
                        <div class="metric-card-value" style="color: #047857;">{summary['avg_insurance_coverage']}%</div>
                        <div class="metric-card-caption">CBHI / Mutuelle, RAMA, MMI</div>
                    </div>
                    <div class="metric-card-pro">
                        <div class="metric-card-label">Avg Travel Time > 1hr</div>
                        <div class="metric-card-value" style="color: #b45309;">{summary['avg_travel_time_over_1hr']}%</div>
                        <div class="metric-card-caption">Population > 1hr to health center</div>
                    </div>
                    <div class="metric-card-pro">
                        <div class="metric-card-label">Avg Poverty Rate</div>
                        <div class="metric-card-value" style="color: #1e3a8a;">{summary['avg_poverty_rate']}%</div>
                        <div class="metric-card-caption">National household poverty rate</div>
                    </div>
                    <div class="metric-card-pro">
                        <div class="metric-card-label">Chronic Illness Reporting</div>
                        <div class="metric-card-value" style="color: #7c3aed;">{summary['avg_chronic_illness_reported']}%</div>
                        <div class="metric-card-caption">Households reporting chronic conditions</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
            
            # Key Findings Callout
            st.markdown(
                f"""
                <div style="background: #ffffff; border: 1px solid #cbd5e1; border-radius: 6px; padding: 16px; margin-top: 14px;">
                    <div style="font-weight: 600; font-size: 0.92rem; color: #1e3a8a; margin-bottom: 6px;">
                        NISR EICV7 Evidence Summary for Continuity Planning:
                    </div>
                    <ul style="font-size: 0.85rem; color: #334155; margin-bottom: 0; padding-left: 20px; line-height: 1.6;">
                        <li><strong>Geographic Access Disparity:</strong> The district with highest travel time to health facilities is <strong>{summary['max_travel_time_district']}</strong> ({summary['max_travel_time_pct']}% of residents travel > 1 hour to reach care). Catchment facilities serving this district require reinforced community health worker outreach.</li>
                        <li><strong>Financial Determinants:</strong> Highest household poverty is documented in <strong>{summary['highest_poverty_district']}</strong> ({summary['highest_poverty_pct']}%), highlighting the necessity of assessing patient medication refill costs and transport subsidies.</li>
                        <li><strong>Health Protection:</strong> High health insurance coverage nationwide ({summary['avg_insurance_coverage']}%) provides a solid foundation, with <strong>{summary['highest_insurance_district']}</strong> leading at {summary['highest_insurance_pct']}%.</li>
                    </ul>
                </div>
                """,
                unsafe_allow_html=True
            )

    # ---------------- TAB 2: DISTRICT EXPLORER ----------------
    with tab_district_explorer:
        c_p, c_i = st.columns([1.5, 2])
        with c_p:
            sel_prov = st.selectbox("Filter Province", ["All Provinces", "City of Kigali", "Southern Province", "Western Province", "Northern Province", "Eastern Province"])
        with c_i:
            indicator_metric = st.selectbox(
                "Rank Districts By Indicator",
                [
                    ("travel_time_over_1hr_pct", "Population Traveling > 1 Hour to Health Facility (%)"),
                    ("poverty_rate_pct", "Household Poverty Rate (%)"),
                    ("health_insurance_coverage_pct", "Health Insurance Coverage (%)"),
                    ("chronic_illness_reported_pct", "Households Reporting Chronic Conditions (%)")
                ],
                format_func=lambda x: x[1]
            )
            
        df_dist = get_nisr_district_indicators(province=sel_prov)
        if not df_dist.empty:
            metric_col = indicator_metric[0]
            metric_label = indicator_metric[1]
            
            df_sorted = df_dist.sort_values(by=metric_col, ascending=False)
            
            # Interactive Bar Chart
            fig_dist = px.bar(
                df_sorted,
                x=metric_col,
                y="district",
                orientation="h",
                color=metric_col,
                color_continuous_scale="Blues" if "insurance" in metric_col else "Reds",
                labels={metric_col: metric_label, "district": "District"},
                title=f"{metric_label} Across Districts"
            )
            fig_dist.update_layout(margin=dict(l=10, r=10, t=30, b=10), height=550, yaxis=dict(autorange="reversed"))
            st.plotly_chart(fig_dist, use_container_width=True)
            
            # Data Table
            st.markdown("<div style='font-weight: 600; font-size: 0.9rem; color: #1e3a8a; margin-top: 10px; margin-bottom: 6px;'>Official Indicator Records</div>", unsafe_allow_html=True)
            st.dataframe(
                df_dist[[
                    "district", "province", "travel_time_over_1hr_pct",
                    "poverty_rate_pct", "health_insurance_coverage_pct",
                    "chronic_illness_reported_pct"
                ]].rename(columns={
                    "district": "District",
                    "province": "Province",
                    "travel_time_over_1hr_pct": ">1hr Travel (%)",
                    "poverty_rate_pct": "Poverty (%)",
                    "health_insurance_coverage_pct": "Insurance (%)",
                    "chronic_illness_reported_pct": "Chronic Conditions (%)"
                }),
                use_container_width=True,
                hide_index=True
            )

    # ---------------- TAB 3: CATCHMENT CROSS-ANALYSIS ----------------
    with tab_catchment_cross:
        st.markdown("<div style='font-weight: 600; font-size: 0.92rem; color: #1e3a8a; margin-bottom: 8px;'>Catchment Vulnerability vs. Active Patient Distribution</div>", unsafe_allow_html=True)
        st.write("Cross-reference official population vulnerability indicators against local registered patient cohorts:")
        
        df_pts_dist = get_registered_patients_by_district()
        df_nisr = get_nisr_district_indicators()
        
        if df_pts_dist.empty:
            st.info("No registered patients found to overlay with statistical data.")
        else:
            merged = pd.merge(df_nisr, df_pts_dist, on="district", how="inner")
            if merged.empty:
                st.info("Registered patients reside in districts currently not mapped in the indicator dataset.")
            else:
                col_cross1, col_cross2 = st.columns(2)
                with col_cross1:
                    # Scatter Plot: Travel Time vs Registered Patients
                    fig_scatter = px.scatter(
                        merged,
                        x="travel_time_over_1hr_pct",
                        y="registered_patients_count",
                        size="review_needed_count" if merged["review_needed_count"].sum() > 0 else "registered_patients_count",
                        color="province",
                        hover_name="district",
                        labels={
                            "travel_time_over_1hr_pct": "Population Traveling >1hr to Health Center (%)",
                            "registered_patients_count": "Registered Patients (FollowUp)",
                            "review_needed_count": "Patients Flagged for Review"
                        },
                        title="Registered Patients vs. Geographic Isolation (>1hr travel)"
                    )
                    fig_scatter.update_layout(margin=dict(l=10, r=10, t=30, b=10), height=320)
                    st.plotly_chart(fig_scatter, use_container_width=True)
                    
                with col_cross2:
                    # Scatter Plot: Poverty vs Review Flags
                    fig_scat2 = px.scatter(
                        merged,
                        x="poverty_rate_pct",
                        y="registered_patients_count",
                        color="province",
                        hover_name="district",
                        labels={
                            "poverty_rate_pct": "District Poverty Rate (%)",
                            "registered_patients_count": "Registered Patients"
                        },
                        title="Registered Patients vs. District Poverty Level"
                    )
                    fig_scat2.update_layout(margin=dict(l=10, r=10, t=30, b=10), height=320)
                    st.plotly_chart(fig_scat2, use_container_width=True)

    # ---------------- TAB 4: IMPORT STATISTICAL CSV ----------------
    with tab_import:
        st.markdown("<div style='font-weight: 600; font-size: 0.92rem; color: #1e3a8a; margin-bottom: 6px;'>Import Official Statistical Dataset (CSV)</div>", unsafe_allow_html=True)
        st.write("Upload official public health or household survey aggregate CSV files published by the National Institute of Statistics of Rwanda.")
        
        with st.expander("Required CSV Structure & Field Format Guidance", expanded=False):
            st.markdown(
                """
                Uploaded CSV files must include the following column headers:
                - `district` (District Name, e.g. Nyarugenge, Gasabo, Huye)
                - `province` (Province Name, e.g. City of Kigali, Southern Province)
                - `poverty_rate_pct` (Floating point percentage, e.g. 11.2)
                - `health_insurance_coverage_pct` (Floating point percentage, e.g. 89.5)
                - `travel_time_over_1hr_pct` (Floating point percentage, e.g. 8.2)
                - `chronic_illness_reported_pct` (Optional floating point, e.g. 14.8)
                - `unimproved_sanitation_pct` (Optional floating point, e.g. 12.1)
                """
            )
            
        if not can_import:
            st.warning("Only Administrators or Healthcare Providers can import official statistical datasets.")
        else:
            with st.form("import_nisr_form"):
                uploaded_file = st.file_uploader("Select Statistical CSV File", type=["csv"])
                dataset_name = st.text_input("Dataset Title *", value="NISR EICV7 Living Conditions & Health Access 2024")
                source_url = st.text_input("Official Publication URL *", value="https://www.statistics.gov.rw/data-sources/surveys/EICV/integrated-household-living-conditions-survey-7-eicv-7")
                ref_period = st.text_input("Survey Reference Period *", value="2023 - 2024")
                geo_coverage = st.text_input("Geographic Coverage *", value="National (30 Districts)")
                ind_desc = st.text_area("Indicator Definitions *", value="Household poverty rates, extreme poverty, health insurance coverage, travel time > 1hr to nearest health facility, and chronic condition reporting.")
                
                sub_import_btn = st.form_submit_button("Import & Validate Statistical Dataset", type="primary")
                if sub_import_btn:
                    if not uploaded_file:
                        st.error("Please select a valid CSV file to upload.")
                    else:
                        ok, msg = import_custom_nisr_dataset(
                            csv_file_obj=uploaded_file,
                            dataset_name=dataset_name,
                            source_url=source_url,
                            reference_period=ref_period,
                            geographic_coverage=geo_coverage,
                            indicator_description=ind_desc,
                            actor_username=user.get("username", "system"),
                            actor_role=user.get("role", "Administrator")
                        )
                        if ok:
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(msg)

    # ---------------- TAB 5: DATASET METADATA ----------------
    with tab_metadata:
        datasets = list_imported_datasets()
        if not datasets:
            st.info("No dataset metadata records found.")
        else:
            for d in datasets:
                st.markdown(
                    f"""
                    <div style="background: #ffffff; border: 1px solid #cbd5e1; border-radius: 6px; padding: 14px; margin-bottom: 12px;">
                        <div style="font-weight: 700; font-size: 1rem; color: #1e3a8a;">{d['dataset_name']}</div>
                        <div style="font-size: 0.82rem; color: #475569; margin-top: 4px; line-height: 1.5;">
                            <strong>Publishing Institution:</strong> {d['publishing_institution']}<br>
                            <strong>Reference Period:</strong> {d['reference_period']} &bull; <strong>Coverage:</strong> {d['geographic_coverage']}<br>
                            <strong>Indicators:</strong> {d['indicator_description']}<br>
                            <strong>Source Documentation:</strong> <a href="{d['source_url']}" target="_blank">{d['source_url']}</a><br>
                            <strong>Total Processed Records:</strong> {d['row_count']} district observations &bull; <strong>Import Date:</strong> {format_date(d['imported_at'])}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
