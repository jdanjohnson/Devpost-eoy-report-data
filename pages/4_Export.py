import streamlit as st
import os
from datetime import datetime
from app.aggregate import DataAggregator
from app.export import ExcelExporter
from app.ui import inject_global_css

st.set_page_config(
    page_title="Export - Hackathon Analysis",
    page_icon="📥",
    layout="wide"
)

inject_global_css()

st.title("📥 Export Data")
st.markdown("---")

aggregator = DataAggregator()
exporter = ExcelExporter(aggregator)

if not aggregator.data_exists():
    st.warning("⚠️ No data available to export. Please upload and process files first.")
    st.info("👉 Navigate to the **Upload** page to get started!")
    st.stop()

st.markdown("""
Generate Excel reports for submission data and registrant data separately, or generate a combined report with all aggregated data.
""")

st.markdown("---")

st.subheader("📊 Generate Reports")

col1, col2 = st.columns(2)

with col1:
    st.markdown("#### 📤 Submission Report")
    st.markdown("""
    **Includes:**
    - All Technologies (full dataset)
    - Submissions by Hackathon
    - Team Size Distribution
    - Time Trends
    - Summary Statistics
    """)
    
    submission_filename = st.text_input(
        "Custom Filename (optional):",
        placeholder="submission_report_YYYYMMDD_HHMMSS.xlsx",
        help="Leave empty to use default timestamp-based filename",
        key="submission_filename"
    )
    
    if st.button("🚀 Generate Submission Report", type="primary", key="generate_submission"):
        with st.spinner("Generating Submission Report..."):
            try:
                filename = submission_filename if submission_filename else None
                
                if filename and not filename.endswith('.xlsx'):
                    filename += '.xlsx'
                
                output_path = exporter.generate_submission_report(filename)
                
                st.success(f"✅ Submission Report generated successfully!")
                
                st.markdown(f"**File:** `{os.path.basename(output_path)}`")
                st.markdown(f"**Location:** `{output_path}`")
                
                with open(output_path, 'rb') as f:
                    file_data = f.read()
                
                st.download_button(
                    label="⬇️ Download Submission Report",
                    data=file_data,
                    file_name=os.path.basename(output_path),
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key="download_submission"
                )
                
                file_size = os.path.getsize(output_path) / 1024
                st.info(f"📊 File size: {file_size:.2f} KB")
            
            except Exception as e:
                st.error(f"❌ Error generating submission report: {str(e)}")

with col2:
    st.markdown("#### 👥 Registrant Report")
    st.markdown("""
    **Includes:**
    - All Skills (full dataset)
    - All Countries (full dataset)
    - All Occupations (full dataset)
    - Specialty Distribution
    - Work Experience Distribution
    """)
    
    registrant_filename = st.text_input(
        "Custom Filename (optional):",
        placeholder="registrant_report_YYYYMMDD_HHMMSS.xlsx",
        help="Leave empty to use default timestamp-based filename",
        key="registrant_filename"
    )
    
    if st.button("🚀 Generate Registrant Report", type="primary", key="generate_registrant"):
        with st.spinner("Generating Registrant Report..."):
            try:
                filename = registrant_filename if registrant_filename else None
                
                if filename and not filename.endswith('.xlsx'):
                    filename += '.xlsx'
                
                output_path = exporter.generate_registrant_report(filename)
                
                st.success(f"✅ Registrant Report generated successfully!")
                
                st.markdown(f"**File:** `{os.path.basename(output_path)}`")
                st.markdown(f"**Location:** `{output_path}`")
                
                with open(output_path, 'rb') as f:
                    file_data = f.read()
                
                st.download_button(
                    label="⬇️ Download Registrant Report",
                    data=file_data,
                    file_name=os.path.basename(output_path),
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key="download_registrant"
                )
                
                file_size = os.path.getsize(output_path) / 1024
                st.info(f"📊 File size: {file_size:.2f} KB")
            
            except Exception as e:
                st.error(f"❌ Error generating registrant report: {str(e)}")

st.markdown("---")

st.markdown("#### 📊 Combined Report (All Data)")
st.markdown("Generate a comprehensive report with both submission and registrant data.")

combined_filename = st.text_input(
    "Custom Filename (optional):",
    placeholder="hackathon_aggregations_YYYYMMDD_HHMMSS.xlsx",
    help="Leave empty to use default timestamp-based filename",
    key="combined_filename"
)

if st.button("🚀 Generate Combined Report", key="generate_combined"):
    with st.spinner("Generating Combined Report..."):
        try:
            filename = combined_filename if combined_filename else None
            
            if filename and not filename.endswith('.xlsx'):
                filename += '.xlsx'
            
            output_path = exporter.generate_excel_workbook(filename)
            
            st.success(f"✅ Combined Report generated successfully!")
            
            st.markdown(f"**File:** `{os.path.basename(output_path)}`")
            st.markdown(f"**Location:** `{output_path}`")
            
            with open(output_path, 'rb') as f:
                file_data = f.read()
            
            st.download_button(
                label="⬇️ Download Combined Report",
                data=file_data,
                file_name=os.path.basename(output_path),
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="download_combined"
            )
            
            file_size = os.path.getsize(output_path) / 1024
            st.info(f"📊 File size: {file_size:.2f} KB")
        
        except Exception as e:
            st.error(f"❌ Error generating combined report: {str(e)}")

st.markdown("---")

st.subheader("📚 Export History")

export_history = exporter.get_export_history()

if not export_history.empty:
    st.markdown(f"**Total Exports:** {len(export_history)}")
    
    for idx, row in export_history.iterrows():
        with st.expander(f"📄 {row['Filename']} - {row['Created At']}"):
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col1:
                st.markdown(f"**Filename:** {row['Filename']}")
                st.markdown(f"**Created At:** {row['Created At']}")
                st.markdown(f"**Size:** {row['Size (KB)']} KB")
            
            with col2:
                file_path = os.path.join(exporter.output_dir, row['Filename'])
                
                if os.path.exists(file_path):
                    with open(file_path, 'rb') as f:
                        file_data = f.read()
                    
                    st.download_button(
                        label="⬇️ Download",
                        data=file_data,
                        file_name=row['Filename'],
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        key=f"download_{idx}"
                    )
            
            with col3:
                if st.button("🗑️ Delete", key=f"delete_{idx}"):
                    if exporter.delete_export(row['Filename']):
                        st.success("File deleted!")
                        st.rerun()
                    else:
                        st.error("Failed to delete file")
else:
    st.info("📭 No exports found. Generate your first export above!")

st.markdown("---")

st.subheader("📋 Export Contents Preview")

summary = aggregator.get_summary_statistics()

with st.expander("📊 Summary Statistics"):
    st.json({
        'Total Submissions': summary['total_submissions'],
        'Total Registrants': summary['total_registrants'],
        'Unique Hackathons': summary['unique_hackathons'],
        'Unique Organizations': summary['unique_organizations'],
        'Date Range': summary['date_range'],
        'Most Popular Technology': summary['most_popular_technology'],
        'Most Popular Skill': summary['most_popular_skill'],
        'Top Country': summary['top_country'],
        'Average Team Size': summary['avg_team_size']
    })

with st.expander("🔧 Top Technologies (Preview)"):
    tech_df = aggregator.get_top_technologies(limit=10)
    if not tech_df.empty:
        st.dataframe(tech_df, width='stretch')
    else:
        st.info("No data available")

with st.expander("💡 Top Skills (Preview)"):
    skills_df = aggregator.get_top_skills(limit=10)
    if not skills_df.empty:
        st.dataframe(skills_df, width='stretch')
    else:
        st.info("No data available")

with st.expander("🏆 Submissions by Hackathon (Preview)"):
    hackathon_df = aggregator.get_submissions_by_hackathon()
    if not hackathon_df.empty:
        st.dataframe(hackathon_df.head(10), width='stretch')
    else:
        st.info("No data available")

with st.expander("👥 Team Size Distribution (Preview)"):
    team_size_df = aggregator.get_team_size_distribution()
    if not team_size_df.empty:
        st.dataframe(team_size_df, width='stretch')
    else:
        st.info("No data available")

with st.expander("🌍 Country Distribution (Preview)"):
    country_df = aggregator.get_country_distribution(limit=10)
    if not country_df.empty:
        st.dataframe(country_df, width='stretch')
    else:
        st.info("No data available")

with st.expander("💼 Occupation Breakdown (Preview)"):
    occupation_df = aggregator.get_occupation_breakdown(limit=10)
    if not occupation_df.empty:
        st.dataframe(occupation_df, width='stretch')
    else:
        st.info("No data available")

with st.expander("🎓 Specialty Distribution (Preview)"):
    specialty_df = aggregator.get_specialty_distribution()
    if not specialty_df.empty:
        st.dataframe(specialty_df, width='stretch')
    else:
        st.info("No data available")

with st.expander("💼 Work Experience Distribution (Preview)"):
    work_exp_df = aggregator.get_work_experience_distribution()
    if not work_exp_df.empty:
        st.dataframe(work_exp_df, width='stretch')
    else:
        st.info("No data available")

with st.expander("📅 Time Trends (Preview)"):
    time_trends_df = aggregator.get_time_trends(period='weekly')
    if not time_trends_df.empty:
        st.dataframe(time_trends_df.head(10), width='stretch')
    else:
        st.info("No data available")

st.markdown("---")

with st.expander("ℹ️ About Excel Exports"):
    st.markdown("""
    **Export Format:**
    - Multi-sheet Excel workbook (.xlsx)
    - Formatted headers with colors
    - Auto-sized columns
    - Frozen header rows
    
    **Included Sheets:**
    1. **Top Technologies** - Top 50 technologies with counts and percentages
    2. **Top Skills** - Top 50 skills with counts and percentages
    3. **Submissions by Hackathon** - All hackathons with submission counts
    4. **Team Size Distribution** - Distribution of team sizes
    5. **Country Distribution** - Top 50 countries with counts
    6. **Occupation Breakdown** - Top 50 occupations with counts
    7. **Specialty Distribution** - Student vs Professional breakdown
    8. **Work Experience** - Work experience distribution by ranges
    9. **Time Trends** - Daily submission trends with cumulative counts
    10. **Summary Statistics** - Overall statistics and key metrics
    
    **Notes:**
    - All data is based on processed files in the database
    - Exports are stored in `./data/processed/` directory
    - Files can be opened in Microsoft Excel, Google Sheets, or any spreadsheet software
    """)
