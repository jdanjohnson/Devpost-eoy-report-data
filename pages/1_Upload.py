import streamlit as st
import os
import tempfile

st.set_page_config(
    page_title="Upload Files - Hackathon Analysis",
    page_icon="📤",
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

st.title("📤 Upload & Process Files")
st.markdown("---")

db = get_database()
ingestor = get_ingestor(db)

st.markdown("""
Upload your hackathon data files for processing. You can either:
- Upload a ZIP file containing multiple Excel (.xlsx) or CSV (.csv) files
- Process files from a local folder
""")

st.markdown("---")

upload_method = st.radio(
    "Select Upload Method:",
    ["ZIP File Upload", "Local Folder Processing"],
    horizontal=True
)

st.markdown("---")

if upload_method == "ZIP File Upload":
    st.subheader("📦 ZIP File Upload")
    
    uploaded_file = st.file_uploader(
        "Choose a ZIP file containing Excel (.xlsx) or CSV (.csv) files",
        type=['zip'],
        help="Maximum file size: 1GB"
    )
    
    if uploaded_file is not None:
        file_size_mb = uploaded_file.size / (1024 * 1024)
        st.info(f"📊 File size: {file_size_mb:.2f} MB")
        
        if file_size_mb > 1024:
            st.error("❌ File size exceeds 1GB limit. Please upload a smaller file.")
        else:
            if st.button("🚀 Start Processing", type="primary"):
                with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as tmp_file:
                    tmp_file.write(uploaded_file.getvalue())
                    tmp_file_path = tmp_file.name
                
                try:
                    st.markdown("### Processing Status")
                    
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    def update_progress(current, total, filename):
                        progress = current / total if total > 0 else 0
                        progress_bar.progress(progress)
                        status_text.text(f"Processing file {current}/{total}: {filename}")
                    
                    with st.spinner("Extracting and processing files..."):
                        results = ingestor.process_zip_file(tmp_file_path, update_progress)
                    
                    progress_bar.progress(1.0)
                    status_text.text("Processing complete!")
                    
                    st.success("✅ Processing completed successfully!")
                    
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("Total Files", results['total_files'])
                    
                    with col2:
                        st.metric("Processed", results['processed_files'])
                    
                    with col3:
                        st.metric("Skipped", results['skipped_files'])
                    
                    with col4:
                        st.metric("Failed", results['failed_files'])
                    
                    if results['errors']:
                        st.warning(f"⚠️ {len(results['errors'])} file(s) encountered errors:")
                        
                        with st.expander("View Errors"):
                            for error in results['errors']:
                                st.error(f"**{error['file']}**: {error['error']}")
                        
                        if st.button("🔄 Retry Failed Files", key="retry_zip"):
                            st.markdown("### Retry Status")
                            
                            retry_progress_bar = st.progress(0)
                            retry_status_text = st.empty()
                            
                            def update_retry_progress(current, total, filename):
                                progress = current / total if total > 0 else 0
                                retry_progress_bar.progress(progress)
                                retry_status_text.text(f"Retrying file {current}/{total}: {filename}")
                            
                            with st.spinner("Retrying failed files..."):
                                retry_results = ingestor.retry_files_from_errors(results['errors'], update_retry_progress)
                            
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
                    
                    st.markdown("---")
                    st.info("👉 Navigate to the **Dashboard** page to view your data!")
                
                except Exception as e:
                    st.error(f"❌ Error processing ZIP file: {str(e)}")
                
                finally:
                    if os.path.exists(tmp_file_path):
                        os.unlink(tmp_file_path)

else:
    st.subheader("📁 Local Folder Processing")
    
    st.markdown("""
    Process Excel (.xlsx) or CSV (.csv) files from local folders. The tool will look for files in:
    - `./incoming/submissions/` - for submission data files
    - `./incoming/registrants/` - for registrant data files
    """)
    
    folder_type = st.selectbox(
        "Select Folder Type:",
        ["Submissions", "Registrants"]
    )
    
    folder_path = f"./incoming/{folder_type.lower()}"
    
    if not os.path.exists(folder_path):
        st.warning(f"⚠️ Folder does not exist: {folder_path}")
        st.info("Creating folder...")
        os.makedirs(folder_path, exist_ok=True)
        st.success(f"✅ Folder created: {folder_path}")
    
    data_files = [
        f for f in os.listdir(folder_path) 
        if (f.lower().endswith('.xlsx') or f.lower().endswith('.csv')) and not f.startswith('~')
    ] if os.path.exists(folder_path) else []
    
    if data_files:
        st.success(f"✅ Found {len(data_files)} data file(s) in {folder_path}")
        
        with st.expander("View Files"):
            for idx, filename in enumerate(data_files, 1):
                file_path = os.path.join(folder_path, filename)
                file_size = os.path.getsize(file_path) / (1024 * 1024)
                st.text(f"{idx}. {filename} ({file_size:.2f} MB)")
        
        if st.button("🚀 Start Processing", type="primary"):
            try:
                st.markdown("### Processing Status")
                
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                def update_progress(current, total, filename):
                    progress = current / total if total > 0 else 0
                    progress_bar.progress(progress)
                    status_text.text(f"Processing file {current}/{total}: {filename}")
                
                with st.spinner("Processing files..."):
                    results = ingestor.process_folder(
                        folder_path, 
                        folder_type.lower().rstrip('s'),
                        update_progress
                    )
                
                progress_bar.progress(1.0)
                status_text.text("Processing complete!")
                
                st.success("✅ Processing completed successfully!")
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Total Files", results['total_files'])
                
                with col2:
                    st.metric("Processed", results['processed_files'])
                
                with col3:
                    st.metric("Skipped", results['skipped_files'])
                
                with col4:
                    st.metric("Failed", results['failed_files'])
                
                if results['errors']:
                    st.warning(f"⚠️ {len(results['errors'])} file(s) encountered errors:")
                    
                    with st.expander("View Errors"):
                        for error in results['errors']:
                            st.error(f"**{error['file']}**: {error['error']}")
                    
                    if st.button("🔄 Retry Failed Files", key="retry_folder"):
                        st.markdown("### Retry Status")
                        
                        retry_progress_bar = st.progress(0)
                        retry_status_text = st.empty()
                        
                        def update_retry_progress(current, total, filename):
                            progress = current / total if total > 0 else 0
                            retry_progress_bar.progress(progress)
                            retry_status_text.text(f"Retrying file {current}/{total}: {filename}")
                        
                        with st.spinner("Retrying failed files..."):
                            retry_results = ingestor.retry_files_from_errors(results['errors'], update_retry_progress)
                        
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
                
                st.markdown("---")
                st.info("👉 Navigate to the **Dashboard** page to view your data!")
            
            except Exception as e:
                st.error(f"❌ Error processing folder: {str(e)}")
    
    else:
        st.info(f"📂 No data files found in {folder_path}")
        st.markdown(f"Please add Excel (.xlsx) or CSV (.csv) files to the folder and refresh this page.")

st.markdown("---")

data_summary = ingestor.get_data_summary()

st.subheader("📊 Current Data Summary")

col1, col2 = st.columns(2)

with col1:
    st.markdown("#### Submissions Data")
    if data_summary['submissions']['exists']:
        st.success(f"✅ {data_summary['submissions']['row_count']:,} rows")
        with st.expander("View Columns"):
            for col in data_summary['submissions']['columns']:
                st.text(f"• {col}")
    else:
        st.info("No submission data processed yet")

with col2:
    st.markdown("#### Registrants Data")
    if data_summary['registrants']['exists']:
        st.success(f"✅ {data_summary['registrants']['row_count']:,} rows")
        with st.expander("View Columns"):
            for col in data_summary['registrants']['columns']:
                st.text(f"• {col}")
    else:
        st.info("No registrant data processed yet")

st.markdown("---")

with st.expander("ℹ️ File Format Requirements"):
    st.markdown("""
    **Supported File Types**: Excel (.xlsx) and CSV (.csv)
    
    **Submission Files** should contain:
    - Organization Name
    - Challenge Title
    - Challenge Published At
    - Project Title
    - Submission Url (used for deduplication)
    - Project Created At
    - About The Project
    - Built With (comma-separated technologies)
    - Additional Team Member Count
    
    **Registrant Files** should contain:
    - Hackathon Name (used for deduplication)
    - User ID (used for deduplication)
    - Country
    - Work Experience
    - Skills (semicolon-separated)
    - Occupation
    - Specialty (Student / Professional / Post Grad)
    
    **Note**: Headers may be in the first data row. The tool will automatically normalize them.
    CSV files will be automatically detected with UTF-8 or Latin-1 encoding.
    """)
