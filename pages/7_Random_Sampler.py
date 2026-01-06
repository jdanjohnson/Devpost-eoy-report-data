import streamlit as st
import os
import io
import pandas as pd
from datetime import datetime

st.set_page_config(
    page_title="Random Sampler - Hackathon Analysis",
    page_icon="🎲",
    layout="wide"
)

@st.cache_resource
def get_aggregator():
    """Lazily initialize data aggregator."""
    from app.aggregate import DataAggregator
    return DataAggregator()

@st.cache_resource
def get_sampler(_aggregator):
    """Lazily initialize random sampler."""
    from app.random_sampler import RandomSampler
    return RandomSampler(_aggregator)

def inject_css():
    """Lazily inject global CSS."""
    from app.ui import inject_global_css
    inject_global_css()

inject_css()

st.title("🎲 Random Submission Sampler")
st.markdown("---")

aggregator = get_aggregator()
sampler = get_sampler(aggregator)

# Check if data exists
data_available = aggregator.data_exists()

if not data_available:
    st.warning("⚠️ No processed submission data available.")
    
    # Show data loading options
    with st.expander("📥 Load Submission Data", expanded=True):
        st.markdown("""
        **Option 1:** Navigate to the **Upload** page to upload and process submission files.
        
        **Option 2:** Load data from Google Drive (if you have a shared zip file with parquet data).
        """)
        
        # Google Drive data loading
        st.markdown("#### Load from Google Drive")
        gdrive_url = st.text_input(
            "Google Drive File ID or URL:",
            placeholder="e.g., 18UQBsGwCxEnZG46NOaJn6Q68Jn2s6ZyJ or full URL",
            help="Enter the Google Drive file ID or full sharing URL for a zip file containing submission parquet data"
        )
        
        if st.button("📥 Download and Load Data", type="primary", disabled=not gdrive_url):
            import re
            import subprocess
            import zipfile
            
            # Extract file ID from URL if needed
            file_id = gdrive_url.strip()
            if 'drive.google.com' in file_id:
                match = re.search(r'/d/([a-zA-Z0-9_-]+)', file_id)
                if match:
                    file_id = match.group(1)
            
            with st.spinner("Downloading data from Google Drive..."):
                try:
                    # Download using gdown
                    zip_path = "/tmp/submissions_data.zip"
                    result = subprocess.run(
                        ["gdown", file_id, "-O", zip_path],
                        capture_output=True,
                        text=True,
                        timeout=300
                    )
                    
                    if result.returncode != 0:
                        st.error(f"Download failed: {result.stderr}")
                        st.info("Make sure the Google Drive file is shared with 'Anyone with the link' permission.")
                    else:
                        # Extract zip file
                        extract_dir = "./data/submissions/parts"
                        os.makedirs(extract_dir, exist_ok=True)
                        
                        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                            zip_ref.extractall(extract_dir)
                        
                        # Clear the cache so the sampler reloads with new data
                        get_aggregator.clear()
                        get_sampler.clear()
                        
                        st.success("✅ Data loaded successfully! Reloading...")
                        st.rerun()
                except subprocess.TimeoutExpired:
                    st.error("Download timed out. The file may be too large or the connection is slow.")
                except Exception as e:
                    st.error(f"Error loading data: {e}")
    
    st.markdown("---")

st.markdown("""
This tool allows you to extract random samples of submissions from hackathons in the dataset.
Use **Single Hackathon** mode for individual sampling, **Batch Processing** to process an entire list of hackathons at once,
or **AI Hackathon Export** to export data from all AI/ML hackathons in the built-in list.
""")

st.markdown("---")

# Create tabs for single, batch, and AI hackathon processing
tab1, tab2, tab3 = st.tabs(["🎯 Single Hackathon", "📋 Batch Processing", "🤖 AI Hackathon Export"])

# ============== SINGLE HACKATHON TAB ==============
with tab1:
    st.markdown("### Sample from a Single Hackathon")
    
    # Input section
    col1, col2 = st.columns([3, 1])
    
    with col1:
        hackathon_input = st.text_input(
            "Enter Hackathon URL or Name:",
            placeholder="e.g., https://hackonomics.devpost.com or Hackonomics 2024",
            help="You can enter a full Devpost URL, just the subdomain (e.g., hackonomics), or the hackathon name"
        )
    
    with col2:
        export_all_single = st.checkbox(
            "Export All Data",
            value=False,
            help="Export all submissions instead of a random sample",
            key="single_export_all"
        )
        
        sample_size = st.number_input(
            "Sample Size:",
            min_value=1,
            max_value=100,
            value=30,
            help="Number of random submissions to extract (ignored if 'Export All Data' is checked)",
            key="single_sample_size",
            disabled=export_all_single
        )
    
    # Advanced options
    with st.expander("⚙️ Advanced Options"):
        col1, col2 = st.columns(2)
        
        with col1:
            use_seed = st.checkbox("Use fixed random seed", value=False, help="Enable for reproducible results", key="single_use_seed", disabled=export_all_single)
        
        with col2:
            if use_seed and not export_all_single:
                random_seed = st.number_input("Random Seed:", min_value=0, value=42, key="single_random_seed")
            else:
                random_seed = None
    
    # Search/Sample button
    button_label = "📦 Export All Submissions" if export_all_single else "🎲 Generate Random Sample"
    if st.button(button_label, type="primary", disabled=not hackathon_input, key="single_generate"):
        if hackathon_input:
            spinner_text = "Exporting all submissions..." if export_all_single else "Searching for hackathon and generating sample..."
            with st.spinner(spinner_text):
                sampled_df, info = sampler.get_random_sample(
                    hackathon_input, 
                    sample_size=sample_size,
                    random_state=random_seed,
                    export_all=export_all_single
                )
                
                if 'error' in info:
                    st.error(f"❌ {info['error']}")
                    
                    # Show search suggestions
                    st.markdown("### 🔍 Did you mean one of these?")
                    suggestions = sampler.search_hackathons(hackathon_input, limit=10)
                    
                    if suggestions:
                        for s in suggestions:
                            st.markdown(f"- **{s['challenge_title']}** ({s['submission_count']} submissions) - `{s['url']}`")
                    else:
                        st.info("No similar hackathons found. Try a different search term.")
                else:
                    # Success - show results
                    st.success(f"✅ Found {info['total_submissions']} submissions for **{info['challenge_title']}**")
                    
                    # Display hackathon info
                    st.markdown("### 📋 Hackathon Information")
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("Hackathon", info.get('challenge_title', 'N/A'))
                    
                    with col2:
                        st.metric("Organization", info.get('organization', 'N/A'))
                    
                    with col3:
                        st.metric("Total Submissions", info.get('total_submissions', 0))
                    
                    with col4:
                        st.metric("Sample Size", info.get('sample_size', 0))
                    
                    if info.get('url'):
                        st.markdown(f"**URL:** [{info['url']}]({info['url']})")
                    
                    st.markdown("---")
                    
                    # Display sample
                    st.markdown("### 🎯 Random Sample")
                    st.dataframe(sampled_df, use_container_width=True, hide_index=True)
                    
                    # Store in session state for export
                    st.session_state['sampled_df'] = sampled_df
                    st.session_state['hackathon_info'] = info
                    st.session_state['random_seed'] = random_seed
                    
                    st.markdown("---")
                    
                    # Export section
                    st.markdown("### 💾 Export Sample")
                    
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        default_filename = f"{info.get('slug', 'hackathon')}_random_sample_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                        export_filename = st.text_input(
                            "Export Filename:",
                            value=default_filename,
                            help="Filename for the exported Excel file"
                        )
                    
                    with col2:
                        st.markdown("&nbsp;")
                        st.markdown("&nbsp;")
                        if st.button("📥 Export to Excel", key="export_sample"):
                            export_dir = os.getenv('EXPORT_DIR', './data/processed')
                            os.makedirs(export_dir, exist_ok=True)
                            output_path = os.path.join(export_dir, export_filename)
                            
                            if sampler.export_sample(
                                hackathon_input, 
                                output_path, 
                                sample_size=sample_size,
                                random_state=random_seed
                            ):
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

# ============== BATCH PROCESSING TAB ==============
with tab2:
    st.markdown("### Batch Process Multiple Hackathons")
    st.markdown("""
    Upload an Excel file containing a list of hackathon URLs to extract random samples from all of them at once.
    The file should have a column containing Devpost URLs (e.g., `https://hackonomics.devpost.com`).
    
    **Note:** If your file has an `Include_in_Sample` column, only hackathons marked as "YES" will be processed.
    """)
    
    # File upload
    uploaded_file = st.file_uploader(
        "Upload Hackathon List (Excel)",
        type=['xlsx', 'xls'],
        help="Excel file with a column containing hackathon URLs"
    )
    
    if uploaded_file:
        # Save uploaded file temporarily
        temp_path = f"/tmp/{uploaded_file.name}"
        with open(temp_path, 'wb') as f:
            f.write(uploaded_file.getbuffer())
        
        try:
            # Check if file has Include_in_Sample column
            temp_df = pd.read_excel(temp_path)
            has_include_column = 'Include_in_Sample' in temp_df.columns
            
            # Set filter parameters
            filter_column = 'Include_in_Sample' if has_include_column else None
            filter_value = 'YES' if has_include_column else None
            
            # Preview the file with filter applied
            preview, total_count = sampler.get_batch_preview(
                temp_path, 
                limit=10,
                filter_column=filter_column,
                filter_value=filter_value
            )
            
            if has_include_column:
                total_in_file = len(temp_df)
                st.success(f"✅ Found {total_count} hackathons marked for sampling (out of {total_in_file} total in file)")
                st.info("ℹ️ Only processing hackathons where `Include_in_Sample` = 'YES'")
            else:
                st.success(f"✅ Loaded {total_count} hackathons from the file")
            
            # Show preview
            st.markdown("#### 📋 Preview (first 10 hackathons)")
            preview_df = pd.DataFrame(preview)
            preview_df['Status'] = preview_df['found'].apply(lambda x: '✅ Found' if x else '❌ Not in dataset')
            preview_df = preview_df[['url', 'slug', 'hackathon_name', 'submission_count', 'Status']]
            preview_df.columns = ['URL', 'Slug', 'Hackathon Name', 'Submissions', 'Status']
            st.dataframe(preview_df, use_container_width=True, hide_index=True)
            
            found_count = sum(1 for p in preview if p['found'])
            st.info(f"ℹ️ Preview: {found_count}/{len(preview)} hackathons found in dataset. Full processing will check all {total_count} hackathons.")
            
            st.markdown("---")
            
            # Batch processing options
            st.markdown("#### ⚙️ Batch Processing Options")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                batch_export_all = st.checkbox(
                    "Export All Data",
                    value=False,
                    help="Export all submissions instead of random samples",
                    key="batch_export_all"
                )
            
            with col2:
                batch_sample_size = st.number_input(
                    "Sample Size per Hackathon:",
                    min_value=1,
                    max_value=100,
                    value=30,
                    help="Number of random submissions to extract from each hackathon (ignored if 'Export All Data' is checked)",
                    key="batch_sample_size",
                    disabled=batch_export_all
                )
            
            with col3:
                batch_use_seed = st.checkbox(
                    "Use fixed random seed",
                    value=True,
                    help="Enable for reproducible results across all hackathons",
                    key="batch_use_seed",
                    disabled=batch_export_all
                )
            
            with col4:
                if batch_use_seed and not batch_export_all:
                    batch_random_seed = st.number_input(
                        "Base Random Seed:",
                        min_value=0,
                        value=42,
                        help="Each hackathon will use seed + index for reproducibility",
                        key="batch_random_seed"
                    )
                else:
                    batch_random_seed = None
            
            st.markdown("---")
            
            # Process button - only runs the batch processing, results are shown separately
            batch_button_label = "📦 Export All Submissions" if batch_export_all else "🚀 Process All Hackathons"
            if st.button(batch_button_label, type="primary", key="batch_process"):
                # Initialize progress tracking
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                results = []
                
                # Process hackathons with filter applied
                for result in sampler.batch_sample_from_file(
                    temp_path,
                    sample_size=batch_sample_size,
                    random_state=batch_random_seed,
                    filter_column=filter_column,
                    filter_value=filter_value,
                    export_all=batch_export_all
                ):
                    results.append(result)
                    
                    # Update progress
                    progress = len(results) / total_count
                    progress_bar.progress(progress)
                    
                    status_icon = "✅" if result['status'] == 'success' else "❌"
                    status_text.text(f"Processing {len(results)}/{total_count}: {status_icon} {result['slug']}")
                
                progress_bar.progress(1.0)
                status_text.text(f"✅ Completed processing {total_count} hackathons!")
                
                # Store results in session state so they persist across reruns
                st.session_state['batch_results'] = results
                st.session_state['batch_processed'] = True
            
            # Display results if they exist in session state (persists across reruns)
            if st.session_state.get('batch_results'):
                results = st.session_state['batch_results']
                
                st.markdown("---")
                st.markdown("### 📊 Processing Results")
                
                success_count = sum(1 for r in results if r['status'] == 'success')
                not_found_count = sum(1 for r in results if r['status'] == 'not_found')
                total_samples = sum(r['sample_size'] for r in results)
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Total Hackathons", len(results))
                
                with col2:
                    st.metric("Found in Dataset", success_count)
                
                with col3:
                    st.metric("Not Found", not_found_count)
                
                with col4:
                    st.metric("Total Samples", total_samples)
                
                # Show detailed results
                st.markdown("#### 📋 Detailed Results")
                
                results_df = pd.DataFrame([{
                    'URL': r['url'],
                    'Hackathon': r['hackathon_name'] or 'N/A',
                    'Organization': r['organization'] or 'N/A',
                    'Total Submissions': r['total_submissions'],
                    'Sampled': r['sample_size'],
                    'Status': '✅ Success' if r['status'] == 'success' else '❌ Not Found'
                } for r in results])
                
                st.dataframe(results_df, use_container_width=True, hide_index=True)
                
                st.markdown("---")
                
                # Export section - generate Excel in memory and provide direct download
                st.markdown("### 💾 Export All Samples")
                
                # Generate the Excel file in memory
                output_buffer = io.BytesIO()
                
                # Combine all samples into one DataFrame
                all_samples = []
                for r in results:
                    if r['status'] == 'success' and r['sample_df'] is not None:
                        sample_df = r['sample_df'].copy()
                        sample_df['Hackathon URL'] = r['url']
                        sample_df['Hackathon Slug'] = r['slug']
                        all_samples.append(sample_df)
                
                if all_samples:
                    combined_samples = pd.concat(all_samples, ignore_index=True)
                else:
                    combined_samples = pd.DataFrame()
                
                # Create summary DataFrame
                summary_df = pd.DataFrame([{
                    'Hackathon URL': r['url'],
                    'Hackathon Slug': r['slug'],
                    'Hackathon Name': r['hackathon_name'] or 'N/A',
                    'Organization': r['organization'] or 'N/A',
                    'Total Submissions': r['total_submissions'],
                    'Sample Size': r['sample_size'],
                    'Status': r['status'],
                    'Error': r.get('error', '')
                } for r in results])
                
                # Create statistics DataFrame
                stats_df = pd.DataFrame([{
                    'Total Hackathons Processed': len(results),
                    'Hackathons Found': success_count,
                    'Hackathons Not Found': not_found_count,
                    'Total Samples Collected': total_samples
                }])
                
                # Write to Excel buffer
                with pd.ExcelWriter(output_buffer, engine='openpyxl') as writer:
                    combined_samples.to_excel(writer, sheet_name='All Samples', index=False)
                    summary_df.to_excel(writer, sheet_name='Summary', index=False)
                    stats_df.to_excel(writer, sheet_name='Statistics', index=False)
                
                output_buffer.seek(0)
                
                # Provide direct download button (no separate export step needed)
                default_filename = f"batch_random_samples_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                st.download_button(
                    label="📥 Download All Samples (Excel)",
                    data=output_buffer,
                    file_name=default_filename,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key="batch_download"
                )
                
                # Option to clear results and start fresh
                if st.button("🔄 Clear Results & Start Over", key="clear_batch"):
                    del st.session_state['batch_results']
                    if 'batch_processed' in st.session_state:
                        del st.session_state['batch_processed']
                    st.rerun()
        
        except Exception as e:
            st.error(f"❌ Error loading file: {e}")
            st.info("Make sure the file contains a column with hackathon URLs (e.g., 'Hackathon url' or similar)")

# ============== AI HACKATHON EXPORT TAB ==============
with tab3:
    st.markdown("### Export AI/ML Hackathon Submissions")
    st.markdown("""
    Export submission data from all AI/ML hackathons in the built-in list.
    This list contains **{:,}** hackathons focused on AI, ML, and related technologies.
    """.format(sampler.get_ai_hackathons_count()))
    
    # Check if submission data is available
    if not data_available:
        st.error("⚠️ **No submission data loaded!** The AI Hackathon Export requires submission data to be loaded first.")
        st.info("👉 Use the **Load Submission Data** section at the top of this page to load your submission data from Google Drive or navigate to the **Upload** page.")
        st.markdown("---")
        st.markdown("The AI hackathons list is ready, but without submission data, there's nothing to export.")
    
    # Check if AI hackathons list exists
    ai_hackathon_count = sampler.get_ai_hackathons_count()
    
    if ai_hackathon_count == 0:
        st.warning("⚠️ No AI hackathons list found. Please ensure the ai_hackathons_list.xlsx file is in the data directory.")
    elif data_available:
        st.success(f"✅ Found {ai_hackathon_count:,} AI/ML hackathons in the built-in list")
        
        st.markdown("---")
        
        # Processing options
        st.markdown("#### ⚙️ Export Options")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            ai_export_all = st.checkbox(
                "Export All Data",
                value=True,
                help="Export all submissions instead of random samples",
                key="ai_export_all"
            )
        
        with col2:
            ai_sample_size = st.number_input(
                "Sample Size per Hackathon:",
                min_value=1,
                max_value=100,
                value=30,
                help="Number of random submissions to extract from each hackathon (ignored if 'Export All Data' is checked)",
                key="ai_sample_size",
                disabled=ai_export_all
            )
        
        with col3:
            ai_use_seed = st.checkbox(
                "Use fixed random seed",
                value=True,
                help="Enable for reproducible results across all hackathons",
                key="ai_use_seed",
                disabled=ai_export_all
            )
        
        with col4:
            if ai_use_seed and not ai_export_all:
                ai_random_seed = st.number_input(
                    "Base Random Seed:",
                    min_value=0,
                    value=42,
                    help="Each hackathon will use seed + index for reproducibility",
                    key="ai_random_seed"
                )
            else:
                ai_random_seed = None
        
        st.markdown("---")
        
        # Process button
        ai_button_label = "📦 Export All AI Hackathon Submissions" if ai_export_all else "🚀 Process All AI Hackathons"
        if st.button(ai_button_label, type="primary", key="ai_process"):
            # Initialize progress tracking
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            results = []
            
            # Process AI hackathons
            for result in sampler.batch_sample_ai_hackathons(
                sample_size=ai_sample_size,
                random_state=ai_random_seed,
                export_all=ai_export_all
            ):
                results.append(result)
                
                # Update progress
                progress = len(results) / ai_hackathon_count
                progress_bar.progress(progress)
                
                status_icon = "✅" if result['status'] == 'success' else "❌"
                status_text.text(f"Processing {len(results)}/{ai_hackathon_count}: {status_icon} {result['slug']}")
            
            progress_bar.progress(1.0)
            status_text.text(f"✅ Completed processing {ai_hackathon_count} AI hackathons!")
            
            # Store results in session state
            st.session_state['ai_batch_results'] = results
            st.session_state['ai_batch_processed'] = True
        
        # Display results if they exist in session state
        if st.session_state.get('ai_batch_results'):
            results = st.session_state['ai_batch_results']
            
            st.markdown("---")
            st.markdown("### 📊 Processing Results")
            
            success_count = sum(1 for r in results if r['status'] == 'success')
            not_found_count = sum(1 for r in results if r['status'] == 'not_found')
            total_samples = sum(r['sample_size'] for r in results)
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total AI Hackathons", len(results))
            
            with col2:
                st.metric("Found in Dataset", success_count)
            
            with col3:
                st.metric("Not Found", not_found_count)
            
            with col4:
                st.metric("Total Submissions", total_samples)
            
            # Show detailed results
            st.markdown("#### 📋 Detailed Results")
            
            results_df = pd.DataFrame([{
                'URL': r['url'],
                'Hackathon': r['hackathon_name'] or 'N/A',
                'Organization': r['organization'] or 'N/A',
                'Total Submissions': r['total_submissions'],
                'Exported': r['sample_size'],
                'Bucket': r.get('submission_bucket', 'N/A'),
                'Status': '✅ Success' if r['status'] == 'success' else '❌ Not Found'
            } for r in results])
            
            st.dataframe(results_df, use_container_width=True, hide_index=True)
            
            st.markdown("---")
            
            # Export section
            st.markdown("### 💾 Export All AI Hackathon Samples")
            
            # Generate the Excel file in memory
            output_buffer = io.BytesIO()
            
            # Combine all samples into one DataFrame
            all_samples = []
            for r in results:
                if r['status'] == 'success' and r['sample_df'] is not None:
                    sample_df = r['sample_df'].copy()
                    sample_df['Hackathon URL'] = r['url']
                    sample_df['Hackathon Slug'] = r['slug']
                    all_samples.append(sample_df)
            
            if all_samples:
                combined_samples = pd.concat(all_samples, ignore_index=True)
            else:
                combined_samples = pd.DataFrame()
            
            # Create summary DataFrame
            summary_df = pd.DataFrame([{
                'Hackathon URL': r['url'],
                'Hackathon Slug': r['slug'],
                'Hackathon Name': r['hackathon_name'] or 'N/A',
                'Organization': r['organization'] or 'N/A',
                'Total Submissions': r['total_submissions'],
                'Exported Count': r['sample_size'],
                'Submission Bucket': r.get('submission_bucket', ''),
                'Hackathon Year': r.get('hackathon_year', ''),
                'Status': r['status'],
                'Error': r.get('error', '')
            } for r in results])
            
            # Create statistics DataFrame
            stats_df = pd.DataFrame([{
                'Total AI Hackathons Processed': len(results),
                'Hackathons Found': success_count,
                'Hackathons Not Found': not_found_count,
                'Total Submissions Exported': total_samples
            }])
            
            # Write to Excel buffer
            with pd.ExcelWriter(output_buffer, engine='openpyxl') as writer:
                combined_samples.to_excel(writer, sheet_name='All AI Hackathon Samples', index=False)
                summary_df.to_excel(writer, sheet_name='Summary', index=False)
                stats_df.to_excel(writer, sheet_name='Statistics', index=False)
            
            output_buffer.seek(0)
            
            # Provide direct download button
            default_filename = f"ai_hackathon_submissions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            st.download_button(
                label="📥 Download AI Hackathon Submissions (Excel)",
                data=output_buffer,
                file_name=default_filename,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="ai_download"
            )
            
            # Option to clear results and start fresh
            if st.button("🔄 Clear Results & Start Over", key="clear_ai"):
                del st.session_state['ai_batch_results']
                if 'ai_batch_processed' in st.session_state:
                    del st.session_state['ai_batch_processed']
                st.rerun()

st.markdown("---")

# Hackathon browser section
st.markdown("### 🔍 Browse Available Hackathons")

with st.expander("View all hackathons in the dataset"):
    hackathons = sampler.get_available_hackathons()
    
    if hackathons:
        # Search filter
        search_query = st.text_input(
            "Filter hackathons:",
            placeholder="Type to filter...",
            key="hackathon_search"
        )
        
        if search_query:
            filtered = sampler.search_hackathons(search_query, limit=50)
        else:
            filtered = hackathons[:50]  # Show top 50 by default
        
        if filtered:
            hackathon_df = pd.DataFrame(filtered)
            hackathon_df = hackathon_df[['challenge_title', 'organization', 'submission_count', 'url']]
            hackathon_df.columns = ['Hackathon', 'Organization', 'Submissions', 'URL']
            
            st.dataframe(hackathon_df, use_container_width=True, hide_index=True)
            st.caption(f"Showing {len(filtered)} of {len(hackathons)} hackathons")
        else:
            st.info("No hackathons match your search.")
    else:
        st.warning("No hackathons found in the dataset.")

st.markdown("---")

with st.expander("ℹ️ About This Feature"):
    st.markdown("""
    **Random Submission Sampler**
    
    This tool extracts random samples of submissions from hackathons in the processed dataset.
    You can also export all submissions instead of random samples.
    
    **Single Hackathon Mode:**
    1. Enter a hackathon URL (e.g., `https://hackonomics.devpost.com`) or name
    2. Check "Export All Data" to get all submissions, or set a sample size for random sampling
    3. Click the button to extract submissions
    4. Export the results to Excel for further analysis
    
    **Batch Processing Mode:**
    1. Upload an Excel file containing hackathon URLs
    2. Check "Export All Data" to get all submissions, or set a sample size per hackathon
    3. Click the button to process all hackathons
    4. Export all samples to a single Excel file with summary sheets
    
    **AI Hackathon Export Mode:**
    1. Uses the built-in list of AI/ML hackathons
    2. Check "Export All Data" to get all submissions (default), or set a sample size
    3. Click the button to process all AI hackathons
    4. Exports include Organization Type and Organization Category from the AI hackathons list
    
    **Features:**
    - **Export All Data:** Option to export all submissions instead of random samples
    - **Flexible Input:** Accepts full URLs, subdomains, or hackathon names
    - **Smart Matching:** Finds hackathons even with partial matches
    - **Reproducible Results:** Use a fixed random seed for consistent sampling
    - **Batch Processing:** Process hundreds of hackathons at once
    - **Export Capability:** Download samples as Excel files with metadata
    
    **Output Columns:**
    - All existing columns (Project Title, Submission URL, Organization, etc.)
    - **Year:** Extracted from the submission date
    - **Submission Bucket:** Classification based on hackathon size:
      - Bucket E (Mega): 300+ submissions
      - Bucket D (Large): 100-299 submissions
      - Bucket C (Mid-Size): 25-99 submissions
      - Bucket B (Small): 10-24 submissions
      - Bucket A (Micro): 1-9 submissions
    - **Hackathon Year:** The year of the hackathon
    
    **Output Format (Batch):**
    - **All Samples sheet:** Combined samples from all hackathons with URL identifiers
    - **Summary sheet:** Status of each hackathon (found/not found, sample counts)
    - **Statistics sheet:** Overall processing statistics
    
    **Note:** The samples are drawn from the processed submission data. Make sure you've uploaded and processed the relevant files first.
    """)
