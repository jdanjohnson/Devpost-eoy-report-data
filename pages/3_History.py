import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="History - Hackathon Analysis",
    page_icon="📜",
    layout="wide"
)

@st.cache_resource
def get_database():
    """Lazily initialize database connection."""
    from app.database import Database
    return Database()

@st.cache_resource
def get_ingestor(_db):
    """Lazily initialize data ingestor."""
    from app.ingest import DataIngestor
    return DataIngestor(_db)

def inject_css():
    """Lazily inject global CSS."""
    from app.ui import inject_global_css
    inject_global_css()

inject_css()

st.title("📜 Processing History")
st.markdown("---")

db = get_database()
ingestor = get_ingestor(db)

st.markdown("""
View the history of all file processing jobs, including their status, row counts, and any errors encountered.
""")

st.markdown("---")

job_history = db.get_job_history()

if job_history.empty:
    st.info("📭 No processing jobs found. Upload and process files to see history here.")
    st.stop()

st.subheader("🗄️ Job Statistics")

stats = db.get_summary_stats()

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric("Total Jobs", stats['total_jobs'])

with col2:
    st.metric("Completed", stats['completed_jobs'])

with col3:
    st.metric("Failed", stats['failed_jobs'])

with col4:
    st.metric("Processing", stats['processing_jobs'])

with col5:
    st.metric("Total Rows", f"{stats['total_rows']:,}")

st.markdown("---")

st.subheader("🔍 Filter Jobs")

col1, col2, col3 = st.columns(3)

with col1:
    status_filter = st.multiselect(
        "Filter by Status:",
        options=['completed', 'failed', 'processing'],
        default=['completed', 'failed', 'processing']
    )

with col2:
    file_type_filter = st.multiselect(
        "Filter by File Type:",
        options=job_history['file_type'].unique().tolist() if 'file_type' in job_history.columns else [],
        default=job_history['file_type'].unique().tolist() if 'file_type' in job_history.columns else []
    )

with col3:
    search_term = st.text_input("Search by Filename:", "")

filtered_history = job_history.copy()

if status_filter:
    filtered_history = filtered_history[filtered_history['status'].isin(status_filter)]

if file_type_filter:
    filtered_history = filtered_history[filtered_history['file_type'].isin(file_type_filter)]

if search_term:
    filtered_history = filtered_history[
        filtered_history['file_name'].str.contains(search_term, case=False, na=False)
    ]

st.markdown("---")

failed_in_filter = filtered_history[filtered_history['status'] == 'failed']
if not failed_in_filter.empty:
    col1, col2 = st.columns([1, 4])
    
    with col1:
        if st.button("🔄 Retry All Failed", type="primary"):
            st.session_state['retry_all'] = True
            st.rerun()
    
    with col2:
        st.info(f"💡 {len(failed_in_filter)} failed job(s) can be retried")

if 'retry_all' in st.session_state and st.session_state['retry_all']:
    st.markdown("### Retry All Failed Files")
    
    retry_progress_bar = st.progress(0)
    retry_status_text = st.empty()
    
    def update_retry_progress(current, total, filename):
        progress = current / total if total > 0 else 0
        retry_progress_bar.progress(progress)
        retry_status_text.text(f"Retrying file {current}/{total}: {filename}")
    
    with st.spinner("Retrying all failed files..."):
        retry_results = ingestor.retry_failed_files(None, update_retry_progress)
    
    retry_progress_bar.progress(1.0)
    retry_status_text.text("Retry complete!")
    
    st.success("✅ Retry completed!")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Retried", retry_results['total_files'])
    
    with col2:
        st.metric("Processed", retry_results['processed_files'])
    
    with col3:
        st.metric("Skipped", retry_results['skipped_files'])
    
    with col4:
        st.metric("Failed", retry_results['failed_files'])
    
    if retry_results['errors']:
        st.warning(f"⚠️ {len(retry_results['errors'])} file(s) still failed:")
        with st.expander("View Retry Errors"):
            for error in retry_results['errors']:
                st.error(f"**{error['file']}**: {error['error']}")
    
    del st.session_state['retry_all']
    
    if st.button("🔄 Refresh History"):
        st.rerun()

st.markdown("---")

st.subheader(f"📋 Job History ({len(filtered_history)} jobs)")

if filtered_history.empty:
    st.info("No jobs match the selected filters.")
else:
    for idx, row in filtered_history.iterrows():
        with st.expander(
            f"{'✅' if row['status'] == 'completed' else '❌' if row['status'] == 'failed' else '⏳'} "
            f"{row['file_name']} - {row['status'].upper()}"
        ):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(f"**Job ID:** {row['id']}")
                st.markdown(f"**File Name:** {row['file_name']}")
                st.markdown(f"**File Type:** {row['file_type']}")
                st.markdown(f"**Status:** {row['status']}")
                st.markdown(f"**Row Count:** {row['row_count']:,}")
            
            with col2:
                st.markdown(f"**Created At:** {row['created_at']}")
                st.markdown(f"**Completed At:** {row['completed_at'] if pd.notna(row['completed_at']) else 'N/A'}")
                
                if 'attempts' in row and pd.notna(row['attempts']) and row['attempts'] > 1:
                    st.markdown(f"**Attempts:** {int(row['attempts'])}")
                
                if row['status'] == 'failed' and pd.notna(row['error_message']):
                    st.error(f"**Error:** {row['error_message']}")
            
            col3, col4, col5 = st.columns([1, 1, 3])
            
            with col3:
                if st.button(f"🗑️ Delete", key=f"delete_{row['id']}"):
                    db.delete_job(row['id'])
                    st.success("Job deleted!")
                    st.rerun()
            
            with col4:
                if row['status'] == 'failed':
                    if st.button(f"🔄 Retry", key=f"retry_{row['id']}"):
                        job = db.get_job_by_id(row['id'])
                        if job and job.get('file_hash'):
                            with st.spinner(f"Retrying {row['file_name']}..."):
                                retry_results = ingestor.retry_failed_files([job['file_hash']])
                            
                            if retry_results['processed_files'] > 0:
                                st.success("✅ File processed successfully!")
                                st.rerun()
                            elif retry_results['failed_files'] > 0:
                                if retry_results['errors']:
                                    st.error(f"❌ Retry failed: {retry_results['errors'][0]['error']}")
                            else:
                                st.info("File was skipped (already processed)")
                        else:
                            st.error("Could not find job details for retry")

st.markdown("---")

st.subheader("📊 Job Statistics by Type")

if not job_history.empty and 'file_type' in job_history.columns:
    type_stats = job_history.groupby(['file_type', 'status']).size().reset_index(name='count')
    
    if not type_stats.empty:
        pivot_stats = type_stats.pivot(index='file_type', columns='status', values='count').fillna(0)
        st.dataframe(pivot_stats, width='stretch')

st.markdown("---")

st.subheader("📈 Recent Activity")

if not job_history.empty:
    recent_jobs = job_history.head(10)
    
    st.dataframe(
        recent_jobs[['file_name', 'file_type', 'status', 'row_count', 'created_at']],
        width='stretch',
        hide_index=True
    )

st.markdown("---")

with st.expander("⚙️ Advanced Actions"):
    st.warning("⚠️ These actions are irreversible!")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🗑️ Clear All Failed Jobs", type="secondary"):
            failed_jobs = job_history[job_history['status'] == 'failed']
            for job_id in failed_jobs['id']:
                db.delete_job(job_id)
            st.success(f"Deleted {len(failed_jobs)} failed jobs!")
            st.rerun()
    
    with col2:
        if st.button("🗑️ Clear All Completed Jobs", type="secondary"):
            completed_jobs = job_history[job_history['status'] == 'completed']
            for job_id in completed_jobs['id']:
                db.delete_job(job_id)
            st.success(f"Deleted {len(completed_jobs)} completed jobs!")
            st.rerun()

st.markdown("---")

with st.expander("ℹ️ About Job History"):
    st.markdown("""
    **Job Status Meanings:**
    - ✅ **Completed**: File was successfully processed and data was stored
    - ❌ **Failed**: File processing encountered an error
    - ⏳ **Processing**: File is currently being processed
    
    **Notes:**
    - Jobs track individual file processing operations
    - Duplicate files (based on file hash) are automatically skipped
    - Failed jobs can be retried by re-uploading the file
    - Deleting a job does not delete the processed data
    """)
