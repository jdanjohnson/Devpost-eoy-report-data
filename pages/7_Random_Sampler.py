import streamlit as st
import os
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
This tool allows you to extract a random sample of submissions from any hackathon in the dataset.
Simply enter a hackathon URL or name to get started.
""")

st.markdown("---")

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
        help="Number of random submissions to extract"
    )

# Advanced options
with st.expander("⚙️ Advanced Options"):
    col1, col2 = st.columns(2)
    
    with col1:
        use_seed = st.checkbox("Use fixed random seed", value=False, help="Enable for reproducible results")
    
    with col2:
        if use_seed:
            random_seed = st.number_input("Random Seed:", min_value=0, value=42)
        else:
            random_seed = None

# Search/Sample button
if st.button("🎲 Generate Random Sample", type="primary", disabled=not hackathon_input):
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
            import pandas as pd
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
    
    This tool extracts a random sample of submissions from any hackathon in the processed dataset.
    
    **How to Use:**
    1. Enter a hackathon URL (e.g., `https://hackonomics.devpost.com`) or name
    2. Set the desired sample size (default: 30)
    3. Click "Generate Random Sample" to extract random submissions
    4. Export the results to Excel for further analysis
    
    **Features:**
    - **Flexible Input:** Accepts full URLs, subdomains, or hackathon names
    - **Smart Matching:** Finds hackathons even with partial matches
    - **Reproducible Results:** Use a fixed random seed for consistent sampling
    - **Export Capability:** Download samples as Excel files with metadata
    
    **Use Cases:**
    - Quality assurance sampling for hackathon submissions
    - Creating representative samples for analysis
    - Spot-checking submission data
    - Generating sample datasets for reports
    
    **Note:** The sample is drawn from the processed submission data. Make sure you've uploaded and processed the relevant files first.
    """)
