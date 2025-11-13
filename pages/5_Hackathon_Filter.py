import streamlit as st
import os
from datetime import datetime
from app.hackathon_source import HackathonSource
from app.hackathon_filter import HackathonFilter
from app.aggregate import DataAggregator
from app.ui import inject_global_css

st.set_page_config(
    page_title="Hackathon Filter - Hackathon Analysis",
    page_icon="🔍",
    layout="wide"
)

inject_global_css()

st.title("🔍 Hackathon & Organizer Filter")
st.markdown("---")

source = HackathonSource()
aggregator = DataAggregator()
filter_tool = HackathonFilter(aggregator, source)

if not source.is_loaded():
    st.error("⚠️ Hackathon source data not found. Please ensure 'hackathons_source.xlsx' is in the data directory.")
    st.info("📁 Expected location: `./data/hackathons_source.xlsx`")
    st.stop()

if not aggregator.data_exists():
    st.warning("⚠️ No processed data available. Please upload and process files first.")
    st.info("👉 Navigate to the **Upload** page to get started!")
    st.stop()

st.success(f"✅ Source data loaded: {len(source.get_all_hackathons())} hackathons from {len(source.get_all_organizers())} organizers")

st.markdown("---")

tab1, tab2, tab3 = st.tabs(["🏆 Filter by Hackathon", "🏢 Filter by Organizer", "📊 Source Data Overview"])

with tab1:
    st.markdown("### 🏆 Filter Data by Hackathon")
    st.markdown("Select a hackathon to view all submissions, registrants, and validation against source data.")
    
    hackathon_list = source.get_hackathon_list()
    
    if not hackathon_list:
        st.warning("No hackathons found in source data.")
    else:
        selected_hackathon = st.selectbox(
            "Select Hackathon:",
            options=[""] + hackathon_list,
            help="Choose a hackathon to filter data"
        )
        
        if selected_hackathon:
            with st.spinner(f"Loading data for {selected_hackathon}..."):
                summary = filter_tool.get_hackathon_summary(selected_hackathon)
                
                st.markdown("#### 📋 Source of Truth Data")
                if summary['source_data']:
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("Organization", summary['source_data']['organization_name'])
                        st.metric("Event Type", summary['source_data']['event_type'])
                    
                    with col2:
                        st.metric("Source Participants", summary['source_data']['participant_count'])
                        st.metric("Source Valid Submissions", summary['source_data']['valid_submissions'])
                    
                    with col3:
                        st.metric("Processed Submissions", summary['processed_data']['submissions'])
                        st.metric("Processed Registrants", summary['processed_data']['registrants'])
                    
                    st.markdown(f"**Hackathon URL:** [{summary['source_data']['hackathon_url']}]({summary['source_data']['hackathon_url']})")
                    st.markdown(f"**Published Date:** {summary['source_data']['published_date']}")
                else:
                    st.warning("No source data found for this hackathon.")
                
                st.markdown("---")
                st.markdown("#### ✅ Data Validation")
                
                if summary['validation']:
                    if summary['validation']['valid']:
                        st.success("✅ Data validated against source of truth")
                        
                        if summary['validation']['warnings']:
                            st.warning("⚠️ Validation Warnings:")
                            for warning in summary['validation']['warnings']:
                                st.markdown(f"- {warning}")
                    else:
                        st.error(f"❌ {summary['validation']['error']}")
                
                st.markdown("---")
                st.markdown("#### 📊 Data Attribution")
                st.markdown("Shows where each piece of data comes from:")
                
                attribution_data = []
                for attr in summary['data_attribution']:
                    attribution_data.append({
                        'Field': attr['field'],
                        'Value': attr['value'],
                        'Source': attr['source']
                    })
                
                import pandas as pd
                attribution_df = pd.DataFrame(attribution_data)
                st.dataframe(attribution_df, width='stretch', hide_index=True)
                
                st.markdown("---")
                st.markdown("#### 💾 Export Hackathon Data")
                
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    export_filename = st.text_input(
                        "Export Filename:",
                        value=f"{selected_hackathon.replace(' ', '_')}_data.xlsx",
                        help="Filename for the exported Excel file"
                    )
                
                with col2:
                    st.markdown("&nbsp;")
                    st.markdown("&nbsp;")
                    if st.button("📥 Export to Excel", key="export_hackathon"):
                        export_dir = os.getenv('EXPORT_DIR', './data/processed')
                        output_path = os.path.join(export_dir, export_filename)
                        
                        if filter_tool.export_hackathon_data(selected_hackathon, output_path):
                            st.success(f"✅ Exported to: {output_path}")
                            
                            with open(output_path, 'rb') as f:
                                st.download_button(
                                    label="⬇️ Download File",
                                    data=f.read(),
                                    file_name=export_filename,
                                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                                )
                        else:
                            st.error("❌ Failed to export data")

with tab2:
    st.markdown("### 🏢 Filter Data by Organizer")
    st.markdown("Select an organizer to view all their hackathons with aggregated data. Handles case-insensitive matching (e.g., 'MHacks' and 'mhacks' are treated as the same).")
    
    organizers = source.get_all_organizers()
    
    if not organizers:
        st.warning("No organizers found in source data.")
    else:
        organizer_options = [""] + [
            f"{org['canonical_name']} ({org['hackathon_count']} hackathons)"
            for org in organizers
        ]
        
        selected_organizer_display = st.selectbox(
            "Select Organizer:",
            options=organizer_options,
            help="Choose an organizer to filter data"
        )
        
        if selected_organizer_display:
            selected_organizer = selected_organizer_display.split(" (")[0]
            
            with st.spinner(f"Loading data for {selected_organizer}..."):
                summary = filter_tool.get_organizer_summary(selected_organizer)
                
                st.markdown("#### 🏢 Organizer Information")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Canonical Name", summary['canonical_name'])
                    st.metric("Name Variations", len(summary['name_variations']))
                
                with col2:
                    st.metric("Total Hackathons", summary['hackathon_count'])
                    st.metric("Total Submissions", summary['total_submissions'])
                
                with col3:
                    st.metric("Total Registrants", summary['total_registrants'])
                
                if len(summary['name_variations']) > 1:
                    st.markdown("**Name Variations Found:**")
                    st.markdown(", ".join(summary['name_variations']))
                    st.info("ℹ️ All variations are grouped together and attributed to the canonical name.")
                
                st.markdown("---")
                st.markdown("#### 🏆 Hackathons by This Organizer")
                
                hackathons_data = []
                for h in summary['hackathons']:
                    validation_status = "✅" if h['validation'] and h['validation']['valid'] else "⚠️"
                    
                    hackathons_data.append({
                        'Status': validation_status,
                        'Hackathon Name': h['hackathon_name'],
                        'Processed Submissions': h['submission_count'],
                        'Processed Registrants': h['registrant_count'],
                        'Source Submissions': h['source_data']['valid_submissions'] if h['source_data'] else 'N/A',
                        'Source Participants': h['source_data']['participant_count'] if h['source_data'] else 'N/A'
                    })
                
                import pandas as pd
                hackathons_df = pd.DataFrame(hackathons_data)
                st.dataframe(hackathons_df, width='stretch', hide_index=True)
                
                warnings_found = False
                for h in summary['hackathons']:
                    if h['validation'] and h['validation'].get('warnings'):
                        if not warnings_found:
                            st.markdown("---")
                            st.markdown("#### ⚠️ Validation Warnings")
                            warnings_found = True
                        
                        with st.expander(f"⚠️ {h['hackathon_name']}"):
                            for warning in h['validation']['warnings']:
                                st.markdown(f"- {warning}")
                
                st.markdown("---")
                st.markdown("#### 💾 Export Organizer Data")
                
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    export_filename = st.text_input(
                        "Export Filename:",
                        value=f"{summary['canonical_name'].replace(' ', '_')}_data.xlsx",
                        help="Filename for the exported Excel file",
                        key="organizer_export_filename"
                    )
                
                with col2:
                    st.markdown("&nbsp;")
                    st.markdown("&nbsp;")
                    if st.button("📥 Export to Excel", key="export_organizer"):
                        export_dir = os.getenv('EXPORT_DIR', './data/processed')
                        output_path = os.path.join(export_dir, export_filename)
                        
                        if filter_tool.export_organizer_data(selected_organizer, output_path):
                            st.success(f"✅ Exported to: {output_path}")
                            
                            with open(output_path, 'rb') as f:
                                st.download_button(
                                    label="⬇️ Download File",
                                    data=f.read(),
                                    file_name=export_filename,
                                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                    key="download_organizer"
                                )
                        else:
                            st.error("❌ Failed to export data")

with tab3:
    st.markdown("### 📊 Source Data Overview")
    st.markdown("Overview of the hackathon source of truth data.")
    
    all_hackathons = source.get_all_hackathons()
    
    if not all_hackathons.empty:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Hackathons", len(all_hackathons))
        
        with col2:
            st.metric("Total Organizers", len(source.get_all_organizers()))
        
        with col3:
            total_participants = all_hackathons['Total participant count'].sum()
            st.metric("Total Participants", f"{total_participants:,}")
        
        with col4:
            total_submissions = all_hackathons['Total valid submissions (excluding spam)'].sum()
            st.metric("Total Valid Submissions", f"{total_submissions:,}")
        
        st.markdown("---")
        st.markdown("#### 🏢 Top Organizers by Hackathon Count")
        
        top_organizers = source.get_all_organizers()[:10]
        
        organizer_data = []
        for org in top_organizers:
            organizer_data.append({
                'Organizer': org['canonical_name'],
                'Hackathons': org['hackathon_count'],
                'Name Variations': org['variation_count']
            })
        
        import pandas as pd
        organizer_df = pd.DataFrame(organizer_data)
        st.dataframe(organizer_df, width='stretch', hide_index=True)
        
        st.markdown("---")
        st.markdown("#### 📋 All Hackathons")
        st.markdown(f"Showing all {len(all_hackathons)} hackathons from the source data:")
        
        display_df = all_hackathons[[
            'Organization name',
            'Hackathon name',
            'Total participant count',
            'Total valid submissions (excluding spam)',
            'In person vs virtual'
        ]].copy()
        
        display_df.columns = [
            'Organization',
            'Hackathon',
            'Participants',
            'Valid Submissions',
            'Event Type'
        ]
        
        st.dataframe(display_df, width='stretch', hide_index=True)
    else:
        st.warning("No hackathon data available.")

st.markdown("---")

with st.expander("ℹ️ About This Feature"):
    st.markdown("""
    **Hackathon & Organizer Filter**
    
    This feature allows you to filter submission and registrant data by specific hackathons or organizers.
    
    **Key Features:**
    - **Source of Truth:** Uses the "Hackathons List for Report.xlsx" as the authoritative data source
    - **Per-Hackathon Filtering:** View all data for a specific hackathon with validation
    - **Per-Organizer Filtering:** View aggregated data across all hackathons by an organizer
    - **Name Normalization:** Handles case-insensitive matching (e.g., "MHacks" and "mhacks")
    - **Data Validation:** Compares processed data against source participant/submission counts
    - **Clear Attribution:** Shows exactly where each piece of data comes from
    - **Export Capability:** Export filtered data to Excel for further analysis
    
    **Data Sources:**
    - **Source of Truth:** Hackathon metadata (URLs, dates, participant counts)
    - **Processed Data:** Actual submission and registrant records from uploaded files
    
    **Validation:**
    - Compares processed submission counts against source valid submission counts
    - Compares processed registrant counts against source participant counts
    - Flags discrepancies with warnings (may be due to spam filtering or incomplete data)
    
    **Note:** Only hackathons that appear in both the source data AND your processed files will show data.
    """)
