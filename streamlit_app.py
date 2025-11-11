import streamlit as st
import os
from dotenv import load_dotenv
from app.database import Database
from app.aggregate import DataAggregator

load_dotenv()

st.set_page_config(
    page_title="Hackathon Data Aggregation Tool",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("📊 Hackathon Data Aggregation Tool")
st.markdown("---")

db = Database()
aggregator = DataAggregator()

st.markdown("""

This tool helps you process and analyze hackathon participation data from Excel files. 
Upload your files, view interactive dashboards, and export comprehensive reports.

- **Upload & Process**: Upload ZIP files or process local folders containing Excel files
- **Interactive Dashboard**: View aggregated data with interactive charts
- **Job History**: Track processing jobs and view logs
- **Export Reports**: Generate Excel workbooks with all aggregations

1. Navigate to the **Upload** page to process your Excel files
2. Once processing is complete, view the **Dashboard** for insights
3. Use the **Export** page to download comprehensive reports
4. Check the **History** page to review past processing jobs
""")

st.markdown("---")

if aggregator.data_exists():
    st.subheader("📈 Quick Statistics")
    
    summary = aggregator.get_summary_statistics()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Total Submissions",
            value=f"{summary['total_submissions']:,}"
        )
    
    with col2:
        st.metric(
            label="Total Registrants",
            value=f"{summary['total_registrants']:,}"
        )
    
    with col3:
        st.metric(
            label="Unique Hackathons",
            value=f"{summary['unique_hackathons']:,}"
        )
    
    with col4:
        st.metric(
            label="Unique Organizations",
            value=f"{summary['unique_organizations']:,}"
        )
    
    st.markdown("---")
    
    col5, col6, col7 = st.columns(3)
    
    with col5:
        if summary['most_popular_technology']:
            st.info(f"🔧 **Most Popular Technology**: {summary['most_popular_technology']}")
    
    with col6:
        if summary['most_popular_skill']:
            st.info(f"💡 **Most Popular Skill**: {summary['most_popular_skill']}")
    
    with col7:
        if summary['top_country']:
            st.info(f"🌍 **Top Country**: {summary['top_country']}")
    
    if summary['date_range']['start'] and summary['date_range']['end']:
        st.markdown(f"📅 **Data Range**: {summary['date_range']['start']} to {summary['date_range']['end']}")
    
    if summary['avg_team_size'] > 0:
        st.markdown(f"👥 **Average Team Size**: {summary['avg_team_size']}")

else:
    st.info("👆 No data has been processed yet. Navigate to the **Upload** page to get started!")

st.markdown("---")

db_stats = db.get_summary_stats()

st.subheader("🗄️ Database Statistics")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        label="Total Jobs",
        value=db_stats['total_jobs']
    )

with col2:
    st.metric(
        label="Completed",
        value=db_stats['completed_jobs'],
        delta=None
    )

with col3:
    st.metric(
        label="Failed",
        value=db_stats['failed_jobs'],
        delta=None
    )

with col4:
    st.metric(
        label="Processing",
        value=db_stats['processing_jobs'],
        delta=None
    )

st.markdown("---")

with st.expander("ℹ️ About This Tool"):
    st.markdown("""
    **Version**: 1.0  
    **Phase**: 1 of 3
    
    This tool is designed to process hackathon participation data from Excel files and generate 
    comprehensive analytics reports. It handles data cleaning, deduplication, normalization, 
    and produces interactive visualizations.
    
    **Supported File Types**:
    - Submission data (export_2025_09.xlsx format)
    - Registrant data (registrants_2025_09.xlsx format)
    
    **Key Capabilities**:
    - Automatic header normalization
    - Deduplication across multiple files
    - Technology and skills normalization
    - Interactive visualizations
    - Excel export with multiple sheets
    
    **Future Phases**:
    - Phase 2: NLP analysis of project narratives
    - Phase 3: Conversational querying interface
    """)

st.sidebar.success("Select a page above to get started!")
