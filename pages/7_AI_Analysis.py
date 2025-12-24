import streamlit as st
import os
import pandas as pd
import json
from pathlib import Path
from datetime import datetime
from app.ui import inject_global_css
import google.generativeai as genai

st.set_page_config(
    page_title="AI Analysis - Hackathon Analysis",
    page_icon="🤖",
    layout="wide"
)

inject_global_css()

st.title("🤖 AI-Powered Narrative Analysis")
st.markdown("---")

st.markdown("""
Transform qualitative project narratives into quantitative insights using AI. 
This page helps you analyze what people are building by extracting structured data from their project descriptions.
""")

gemini_key = os.getenv('GEMINI_API_KEY')
if not gemini_key:
    st.error("⚠️ GEMINI_API_KEY environment variable not set. Please add it to your .env file or Streamlit secrets.")
    st.info("Get your API key from: https://makersuite.google.com/app/apikey")
    st.stop()

submissions_file = './data/submissions/data.parquet'
if not os.path.exists(submissions_file):
    st.warning("⚠️ No submission data available. Please upload and process files first.")
    st.info("👉 Navigate to the **Upload** page to get started!")
    st.stop()

@st.cache_data
def load_submissions():
    return pd.read_parquet(submissions_file)

df = load_submissions()

extractions_dir = Path('./data/ai_extractions')
extractions_dir.mkdir(parents=True, exist_ok=True)

existing_extractions = list(extractions_dir.glob('ai_extractions_*.parquet'))

st.markdown("---")

tab1, tab2, tab3, tab4 = st.tabs(["📊 Run Analysis", "📈 View Results", "💬 Ask Questions", "📚 Documentation"])

with tab1:
    st.subheader("📊 Run AI Analysis")
    
    st.markdown("""
    Process project narratives with AI to extract structured data including:
    - **Themes** - AI/ML, healthcare, education, climate, finance, etc.
    - **Project Types** - Mobile app, web app, game, API, etc.
    - **Use Cases** - What the project does
    - **Sentiment** - Enthusiasm and tone analysis
    - **Problem-Solution** - What problem is solved and how
    - **Quality Indicators** - Clarity, completeness, impact metrics
    """)
    
    narratives_count = df['About The Project'].notna().sum()
    st.info(f"📝 Found {narratives_count:,} submissions with project narratives")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Analysis Settings")
        
        limit = st.number_input(
            "Number of narratives to process:",
            min_value=1,
            max_value=narratives_count,
            value=min(100, narratives_count),
            help="Start with a small batch to test. Processing is cached so you can run multiple times."
        )
        
        st.markdown(f"**Estimated time:** ~{limit * 1.5 / 60:.1f} minutes")
        st.markdown(f"**Estimated cost:** ~${limit * 0.0001:.4f} (Gemini API)")
    
    with col2:
        st.markdown("#### Existing Extractions")
        
        if existing_extractions:
            st.success(f"✅ Found {len(existing_extractions)} previous extraction(s)")
            for extraction_file in sorted(existing_extractions, reverse=True)[:5]:
                extraction_df = pd.read_parquet(extraction_file)
                timestamp = extraction_file.stem.replace('ai_extractions_', '')
                st.markdown(f"- `{timestamp}`: {len(extraction_df):,} extractions")
        else:
            st.info("No previous extractions found")
    
    st.markdown("---")
    
    if st.button("🚀 Start AI Analysis", type="primary"):
        with st.spinner(f"Processing {limit} narratives with AI..."):
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            try:
                import sys
                sys.path.insert(0, str(Path(__file__).parent.parent))
                from scripts.analyze_narratives import NarrativeAnalyzer
                
                status_text.text("Initializing AI analyzer...")
                analyzer = NarrativeAnalyzer(
                    api_key=gemini_key,
                    taxonomy_path='taxonomy.json',
                    cache_dir='.cache/narratives'
                )
                
                status_text.text("Processing narratives...")
                extractions_df = analyzer.analyze_batch(df, limit=limit)
                
                if extractions_df.empty:
                    st.error("❌ No extractions generated")
                else:
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    output_path = extractions_dir / f"ai_extractions_{timestamp}.parquet"
                    extractions_df.to_parquet(output_path, index=False)
                    
                    progress_bar.progress(100)
                    status_text.text("Complete!")
                    
                    st.success(f"✅ Successfully processed {len(extractions_df):,} narratives!")
                    
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Processed", analyzer.stats['processed'])
                    with col2:
                        st.metric("Cached", analyzer.stats['cached'])
                    with col3:
                        st.metric("Failed", analyzer.stats['failed'])
                    with col4:
                        st.metric("Validation Errors", analyzer.stats['validation_errors'])
                    
                    st.markdown(f"**Saved to:** `{output_path}`")
                    
                    st.cache_data.clear()
                    st.rerun()
            
            except Exception as e:
                st.error(f"❌ Error during analysis: {str(e)}")
                import traceback
                st.code(traceback.format_exc())

with tab2:
    st.subheader("📈 View Analysis Results")
    
    if not existing_extractions:
        st.info("No analysis results yet. Run an analysis in the 'Run Analysis' tab first.")
    else:
        latest_extraction = sorted(existing_extractions, reverse=True)[0]
        extractions_df = pd.read_parquet(latest_extraction)
        
        st.success(f"Showing results from: `{latest_extraction.name}`")
        st.markdown(f"**Total extractions:** {len(extractions_df):,}")
        
        st.markdown("---")
        
        st.markdown("#### 🎯 Theme Distribution")
        
        themes_exploded = extractions_df.explode('themes')
        theme_counts = themes_exploded['themes'].value_counts()
        
        if not theme_counts.empty:
            col1, col2 = st.columns([2, 1])
            
            with col1:
                import plotly.express as px
                fig = px.bar(
                    x=theme_counts.values,
                    y=theme_counts.index,
                    orientation='h',
                    title="Projects by Theme",
                    labels={'x': 'Number of Projects', 'y': 'Theme'}
                )
                fig.update_layout(height=500, showlegend=False)
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                st.markdown("**Top Themes:**")
                for theme, count in theme_counts.head(10).items():
                    percentage = (count / len(extractions_df)) * 100
                    st.markdown(f"- **{theme}**: {count} ({percentage:.1f}%)")
        
        st.markdown("---")
        
        st.markdown("#### 📱 Project Types")
        
        project_type_counts = extractions_df['project_type'].value_counts()
        
        if not project_type_counts.empty:
            col1, col2 = st.columns(2)
            
            with col1:
                fig = px.pie(
                    values=project_type_counts.values,
                    names=project_type_counts.index,
                    title="Project Type Distribution"
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                st.dataframe(
                    pd.DataFrame({
                        'Project Type': project_type_counts.index,
                        'Count': project_type_counts.values,
                        'Percentage': (project_type_counts.values / len(extractions_df) * 100).round(1)
                    }),
                    hide_index=True,
                    use_container_width=True
                )
        
        st.markdown("---")
        
        st.markdown("#### 😊 Sentiment Analysis")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            avg_sentiment = extractions_df['sentiment_score'].mean()
            st.metric("Average Sentiment", f"{avg_sentiment:.2f}", help="Scale: -1 (negative) to 1 (positive)")
        
        with col2:
            enthusiasm_counts = extractions_df['enthusiasm_level'].value_counts()
            st.metric("High Enthusiasm", f"{enthusiasm_counts.get('high', 0)}", 
                     delta=f"{enthusiasm_counts.get('high', 0) / len(extractions_df) * 100:.1f}%")
        
        with col3:
            clear_problem = extractions_df['has_clear_problem'].sum()
            st.metric("Clear Problem Statement", f"{clear_problem}",
                     delta=f"{clear_problem / len(extractions_df) * 100:.1f}%")
        
        fig = px.histogram(
            extractions_df,
            x='sentiment_score',
            nbins=20,
            title="Sentiment Score Distribution",
            labels={'sentiment_score': 'Sentiment Score', 'count': 'Number of Projects'}
        )
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("---")
        
        st.markdown("#### ✨ Quality Indicators")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            clear_solution = extractions_df['has_clear_solution'].sum()
            st.metric("Clear Solution", f"{clear_solution / len(extractions_df) * 100:.1f}%")
        
        with col2:
            impact_metrics = extractions_df['has_impact_metrics'].sum()
            st.metric("Mentions Impact", f"{impact_metrics / len(extractions_df) * 100:.1f}%")
        
        with col3:
            avg_length = extractions_df['narrative_length'].mean()
            st.metric("Avg Narrative Length", f"{avg_length:.0f} chars")
        
        with col4:
            pii_count = extractions_df['contains_pii'].sum()
            st.metric("Contains PII", f"{pii_count}")
        
        st.markdown("---")
        
        st.markdown("#### 📝 Sample Extractions")
        
        sample_df = extractions_df[['project_title', 'hackathon', 'themes', 'summary_200', 'sentiment_score']].head(10)
        st.dataframe(sample_df, use_container_width=True, hide_index=True)
        
        st.markdown("---")
        
        st.markdown("#### 💾 Export Results")
        
        col1, col2 = st.columns(2)
        
        with col1:
            csv_data = extractions_df.to_csv(index=False)
            st.download_button(
                label="⬇️ Download as CSV",
                data=csv_data,
                file_name=f"ai_extractions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
        
        with col2:
            json_data = extractions_df.to_json(orient='records', indent=2)
            st.download_button(
                label="⬇️ Download as JSON",
                data=json_data,
                file_name=f"ai_extractions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )

with tab3:
    st.subheader("💬 Ask Questions About Your Data")
    
    if not existing_extractions:
        st.info("No analysis results yet. Run an analysis in the 'Run Analysis' tab first.")
    else:
        latest_extraction = sorted(existing_extractions, reverse=True)[0]
        extractions_df = pd.read_parquet(latest_extraction)
        
        st.markdown("""
        Ask natural language questions about your hackathon data. The AI will analyze the structured 
        extractions to provide insights.
        """)
        
        with st.expander("💡 Example Questions"):
            st.markdown("""
            - What are the top 5 themes in healthcare projects?
            - How many projects focus on climate and sustainability?
            - What's the average sentiment for AI/ML projects?
            - Which hackathons had the most innovative projects?
            - What technologies are most commonly used in education projects?
            - Show me projects with high enthusiasm that address accessibility
            """)
        
        question = st.text_area(
            "Ask a question:",
            placeholder="What are the top trends in hackathon projects?",
            height=100
        )
        
        if st.button("🔍 Get Answer", type="primary"):
            if not question:
                st.warning("Please enter a question")
            else:
                with st.spinner("Analyzing data..."):
                    try:
                        genai.configure(api_key=gemini_key)
                        model = genai.GenerativeModel('gemini-1.5-flash')
                        
                        context = f"""You are analyzing hackathon project data. Here's a summary of the data:

Total projects: {len(extractions_df)}

Theme distribution:
{extractions_df.explode('themes')['themes'].value_counts().head(10).to_dict()}

Project types:
{extractions_df['project_type'].value_counts().to_dict()}

Average sentiment: {extractions_df['sentiment_score'].mean():.2f}

Quality indicators:
- Clear problem: {extractions_df['has_clear_problem'].sum()} ({extractions_df['has_clear_problem'].sum() / len(extractions_df) * 100:.1f}%)
- Clear solution: {extractions_df['has_clear_solution'].sum()} ({extractions_df['has_clear_solution'].sum() / len(extractions_df) * 100:.1f}%)
- Impact metrics: {extractions_df['has_impact_metrics'].sum()} ({extractions_df['has_impact_metrics'].sum() / len(extractions_df) * 100:.1f}%)

Sample projects:
{extractions_df[['project_title', 'themes', 'summary_200']].head(5).to_dict('records')}

User question: {question}

Provide a clear, data-driven answer based on the information above. Include specific numbers and percentages where relevant.
"""
                        
                        response = model.generate_content(context)
                        
                        st.markdown("### 💡 Answer")
                        st.markdown(response.text)
                        
                    except Exception as e:
                        st.error(f"Error generating answer: {str(e)}")

with tab4:
    st.subheader("📚 Documentation")
    
    st.markdown("""
    
    This tool uses Google Gemini AI to analyze project narratives and extract structured data. Here's the process:
    
    - Each project narrative is sent to Gemini AI
    - AI extracts themes, sentiment, use cases, and other structured data
    - Results are validated and cached for efficiency
    
    The AI extracts:
    - **Themes**: Multi-label classification (AI/ML, healthcare, education, etc.)
    - **Project Type**: Mobile app, web app, game, API, etc.
    - **Use Cases**: What the project does
    - **Target Audience**: Who it's for
    - **Technologies**: Normalized tech stack
    - **Sentiment**: Tone and enthusiasm analysis
    - **Problem-Solution**: What problem is solved and how
    - **Quality Indicators**: Clarity, completeness, impact
    
    Once extracted, you can:
    - Count projects by theme
    - Analyze sentiment trends
    - Identify common use cases
    - Compare across hackathons
    - Export to BigQuery for advanced analysis
    
    
    After running AI analysis, you can:
    1. Export extractions as NDJSON
    2. Upload to Google Cloud Storage
    3. Load into BigQuery
    4. Run SQL queries for deeper analysis
    5. Build dashboards in Data Studio
    
    See `BIGQUERY_DEPLOYMENT.md` for detailed instructions.
    
    
    - **API Cost**: ~$0.0001 per narrative (Gemini Flash)
    - **Processing Speed**: ~1.5 seconds per narrative
    - **Caching**: Results are cached to avoid reprocessing
    - **Batch Size**: Start with 100-500 for testing
    
    
    - Narratives are sent to Google Gemini API
    - PII detection flags potential privacy issues
    - Results are stored locally in Parquet format
    - No data is shared with third parties
    
    
    **API Key Issues:**
    - Ensure `GEMINI_API_KEY` is set in `.env` or Streamlit secrets
    - Get your key from: https://makersuite.google.com/app/apikey
    
    **Processing Errors:**
    - Check cache directory permissions
    - Verify taxonomy.json exists
    - Review error logs for specific issues
    
    **Quality Issues:**
    - Adjust prompts in `scripts/analyze_narratives.py`
    - Refine taxonomy categories
    - Increase sample size for better statistics
    """)

st.markdown("---")
st.markdown("**Note:** AI analysis requires a Gemini API key. Processing is cached so you can run multiple times without reprocessing.")
