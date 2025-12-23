import streamlit as st
import os
import pandas as pd
from datetime import datetime
from app.random_sampler import RandomSampler
from app.aggregate import DataAggregator
from app.ui import inject_global_css

st.set_page_config(
    page_title="Random Sampler - Hackathon Analysis",
    page_icon="🎲",
    layout="wide"
)

inject_global_css()

st.title("🎲 Random Submission Sampler")
st.markdown("---")

aggregator = DataAggregator()
sampler = RandomSampler(aggregator)

if not aggregator.data_exists():
    st.warning("⚠️ No processed data available. Please upload and process files first.")
    st.info("👉 Navigate to the **Upload** page to get started!")
    st.stop()

st.markdown("""
This tool allows you to extract random samples of submissions from hackathons in the dataset.
Use **Single Hackathon** mode for individual sampling, or **Batch Processing** to process an entire list of hackathons at once.
""")

st.markdown("---")

# Create tabs for single and batch processing
tab1, tab2 = st.tabs(["🎯 Single Hackathon", "📋 Batch Processing"])

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
        sample_size = st.number_input(
            "Sample Size:",
            min_value=1,
            max_value=100,
            value=30,
            help="Number of random submissions to extract",
            key="single_sample_size"
        )
    
    # Advanced options
    with st.expander("⚙️ Advanced Options"):
        col1, col2 = st.columns(2)
        
        with col1:
            use_seed = st.checkbox("Use fixed random seed", value=False, help="Enable for reproducible results", key="single_use_seed")
        
        with col2:
            if use_seed:
                random_seed = st.number_input("Random Seed:", min_value=0, value=42, key="single_random_seed")
            else:
                random_seed = None
    
    # Search/Sample button
    if st.button("🎲 Generate Random Sample", type="primary", disabled=not hackathon_input, key="single_generate"):
        if hackathon_input:
            with st.spinner(f"Searching for hackathon and generating sample..."):
                sampled_df, info = sampler.get_random_sample(
                    hackathon_input, 
                    sample_size=sample_size,
                    random_state=random_seed
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
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                batch_sample_size = st.number_input(
                    "Sample Size per Hackathon:",
                    min_value=1,
                    max_value=100,
                    value=30,
                    help="Number of random submissions to extract from each hackathon",
                    key="batch_sample_size"
                )
            
            with col2:
                batch_use_seed = st.checkbox(
                    "Use fixed random seed",
                    value=True,
                    help="Enable for reproducible results across all hackathons",
                    key="batch_use_seed"
                )
            
            with col3:
                if batch_use_seed:
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
            
            # Process button
            if st.button("🚀 Process All Hackathons", type="primary", key="batch_process"):
                # Initialize progress tracking
                progress_bar = st.progress(0)
                status_text = st.empty()
                results_container = st.container()
                
                results = []
                
                # Process hackathons with filter applied
                for result in sampler.batch_sample_from_file(
                    temp_path,
                    sample_size=batch_sample_size,
                    random_state=batch_random_seed,
                    filter_column=filter_column,
                    filter_value=filter_value
                ):
                    results.append(result)
                    
                    # Update progress
                    progress = len(results) / total_count
                    progress_bar.progress(progress)
                    
                    status_icon = "✅" if result['status'] == 'success' else "❌"
                    status_text.text(f"Processing {len(results)}/{total_count}: {status_icon} {result['slug']}")
                
                progress_bar.progress(1.0)
                status_text.text(f"✅ Completed processing {total_count} hackathons!")
                
                # Store results in session state
                st.session_state['batch_results'] = results
                
                # Show summary
                with results_container:
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
                    
                    # Export section
                    st.markdown("### 💾 Export All Samples")
                    
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        batch_export_filename = st.text_input(
                            "Export Filename:",
                            value=f"batch_random_samples_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                            help="Filename for the exported Excel file containing all samples",
                            key="batch_export_filename"
                        )
                    
                    with col2:
                        st.markdown("&nbsp;")
                        st.markdown("&nbsp;")
                        if st.button("📥 Export All to Excel", key="batch_export"):
                            export_dir = os.getenv('EXPORT_DIR', './data/processed')
                            os.makedirs(export_dir, exist_ok=True)
                            output_path = os.path.join(export_dir, batch_export_filename)
                            
                            with st.spinner("Exporting all samples..."):
                                if sampler.export_batch_samples(results, output_path):
                                    st.success(f"✅ Exported to: {output_path}")
                                    
                                    with open(output_path, 'rb') as f:
                                        st.download_button(
                                            label="⬇️ Download File",
                                            data=f.read(),
                                            file_name=batch_export_filename,
                                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                            key="batch_download"
                                        )
                                else:
                                    st.error("❌ Failed to export data")
        
        except Exception as e:
            st.error(f"❌ Error loading file: {e}")
            st.info("Make sure the file contains a column with hackathon URLs (e.g., 'Hackathon url' or similar)")

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
    
    **Single Hackathon Mode:**
    1. Enter a hackathon URL (e.g., `https://hackonomics.devpost.com`) or name
    2. Set the desired sample size (default: 30)
    3. Click "Generate Random Sample" to extract random submissions
    4. Export the results to Excel for further analysis
    
    **Batch Processing Mode:**
    1. Upload an Excel file containing hackathon URLs
    2. Set the sample size per hackathon
    3. Click "Process All Hackathons" to extract samples from all hackathons
    4. Export all samples to a single Excel file with summary sheets
    
    **Features:**
    - **Flexible Input:** Accepts full URLs, subdomains, or hackathon names
    - **Smart Matching:** Finds hackathons even with partial matches
    - **Reproducible Results:** Use a fixed random seed for consistent sampling
    - **Batch Processing:** Process hundreds of hackathons at once
    - **Export Capability:** Download samples as Excel files with metadata
    
    **Output Format (Batch):**
    - **All Samples sheet:** Combined samples from all hackathons with URL identifiers
    - **Summary sheet:** Status of each hackathon (found/not found, sample counts)
    - **Statistics sheet:** Overall processing statistics
    
    **Note:** The samples are drawn from the processed submission data. Make sure you've uploaded and processed the relevant files first.
    """)
