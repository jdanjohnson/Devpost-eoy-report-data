import streamlit as st
import os
from datetime import datetime
from app.aggregate import DataAggregator
from app.export import ExcelExporter

st.set_page_config(
    page_title="Export - Hackathon Analysis",
    page_icon="📥",
    layout="wide"
)

st.title("📥 Export Data")
st.markdown("---")

aggregator = DataAggregator()
exporter = ExcelExporter(aggregator)

if not aggregator.data_exists():
    st.warning("⚠️ No data available to export. Please upload and process files first.")
    st.info("👉 Navigate to the **Upload** page to get started!")
    st.stop()

st.markdown("""
Generate comprehensive Excel reports with all aggregated data, including:
- Top 50 Technologies
- Top 50 Skills
- Submissions by Hackathon
- Team Size Distribution
- Country Distribution
- Occupation Breakdown
- Specialty Distribution
- Work Experience Distribution
- Time Trends
- Summary Statistics
""")

st.markdown("---")

st.subheader("📊 Generate New Export")

col1, col2 = st.columns([2, 1])

with col1:
    custom_filename = st.text_input(
        "Custom Filename (optional):",
        placeholder="hackathon_aggregations_YYYYMMDD_HHMMSS.xlsx",
        help="Leave empty to use default timestamp-based filename"
    )

with col2:
    st.markdown("#### Export Format")
    st.info("📄 Excel (.xlsx)")

if st.button("🚀 Generate Export", type="primary"):
    with st.spinner("Generating Excel workbook..."):
        try:
            filename = custom_filename if custom_filename else None
            
            if filename and not filename.endswith('.xlsx'):
                filename += '.xlsx'
            
            output_path = exporter.generate_excel_workbook(filename)
            
            st.success(f"✅ Export generated successfully!")
            
            st.markdown(f"**File:** `{os.path.basename(output_path)}`")
            st.markdown(f"**Location:** `{output_path}`")
            
            with open(output_path, 'rb') as f:
                file_data = f.read()
            
            st.download_button(
                label="⬇️ Download Excel File",
                data=file_data,
                file_name=os.path.basename(output_path),
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            
            file_size = os.path.getsize(output_path) / 1024
            st.info(f"📊 File size: {file_size:.2f} KB")
        
        except Exception as e:
            st.error(f"❌ Error generating export: {str(e)}")

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
        st.dataframe(tech_df, use_container_width=True)
    else:
        st.info("No data available")

with st.expander("💡 Top Skills (Preview)"):
    skills_df = aggregator.get_top_skills(limit=10)
    if not skills_df.empty:
        st.dataframe(skills_df, use_container_width=True)
    else:
        st.info("No data available")

with st.expander("🏆 Submissions by Hackathon (Preview)"):
    hackathon_df = aggregator.get_submissions_by_hackathon()
    if not hackathon_df.empty:
        st.dataframe(hackathon_df.head(10), use_container_width=True)
    else:
        st.info("No data available")

with st.expander("👥 Team Size Distribution (Preview)"):
    team_size_df = aggregator.get_team_size_distribution()
    if not team_size_df.empty:
        st.dataframe(team_size_df, use_container_width=True)
    else:
        st.info("No data available")

with st.expander("🌍 Country Distribution (Preview)"):
    country_df = aggregator.get_country_distribution(limit=10)
    if not country_df.empty:
        st.dataframe(country_df, use_container_width=True)
    else:
        st.info("No data available")

with st.expander("💼 Occupation Breakdown (Preview)"):
    occupation_df = aggregator.get_occupation_breakdown(limit=10)
    if not occupation_df.empty:
        st.dataframe(occupation_df, use_container_width=True)
    else:
        st.info("No data available")

with st.expander("🎓 Specialty Distribution (Preview)"):
    specialty_df = aggregator.get_specialty_distribution()
    if not specialty_df.empty:
        st.dataframe(specialty_df, use_container_width=True)
    else:
        st.info("No data available")

with st.expander("💼 Work Experience Distribution (Preview)"):
    work_exp_df = aggregator.get_work_experience_distribution()
    if not work_exp_df.empty:
        st.dataframe(work_exp_df, use_container_width=True)
    else:
        st.info("No data available")

with st.expander("📅 Time Trends (Preview)"):
    time_trends_df = aggregator.get_time_trends(period='weekly')
    if not time_trends_df.empty:
        st.dataframe(time_trends_df.head(10), use_container_width=True)
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
