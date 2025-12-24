# AI-Powered Narrative Analysis Guide

**Version:** 2.0 (Phase 2)  
**Date:** November 13, 2025  
**Purpose:** Transform qualitative hackathon narratives into quantitative insights using AI

## Overview

This guide shows you how to use AI to analyze hackathon submission narratives and convert qualitative data (personal stories, pitches, project descriptions) into structured, quantitative insights that you can query and analyze.

### What Problem Does This Solve?

Traditional keyword-based analysis misses the nuance in project narratives. People describe their projects in different ways, use varied terminology, and embed insights in personal stories. AI-powered analysis:

- **Extracts themes** from natural language (not just keyword matching)
- **Understands context** (distinguishes "AI for healthcare" from "healthcare app")
- **Analyzes sentiment** (enthusiasm, clarity, impact)
- **Structures qualitative data** into quantitative metrics
- **Enables natural language queries** ("What are the top healthcare trends?")

### The Approach

We use a **hybrid AI system** that combines:

1. **Batch AI Extraction** - Process narratives with Google Gemini to extract structured data
2. **Structured Storage** - Store results in Parquet/BigQuery for quantitative analysis
3. **Natural Language Querying** - Ask questions in plain English and get data-driven answers
4. **Semantic Understanding** - AI understands meaning, not just keywords

---

## Architecture

```
Submission Narratives (Qualitative)
    ↓
Google Gemini AI (Extraction)
    ↓
Structured Data (Quantitative)
    ↓
Local Storage (Parquet) + BigQuery
    ↓
Natural Language Queries + SQL Analysis
    ↓
Insights & Trends
```

---

## Quick Start

### Prerequisites

1. **Processed submission data** (Phase 1 complete)
2. **Google Gemini API key** (free tier available)
3. **Python environment** with dependencies installed

### Step 1: Get Gemini API Key

1. Visit https://makersuite.google.com/app/apikey
2. Sign in with Google account
3. Create API key
4. Add to `.env` file:

```bash
GEMINI_API_KEY=your_api_key_here
```

Or add to Streamlit secrets (`.streamlit/secrets.toml`):

```toml
GEMINI_API_KEY = "your_api_key_here"
```

### Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

New dependencies for AI analysis:
- `google-generativeai` - Gemini API client
- `pydantic` - Data validation
- `tqdm` - Progress bars

### Step 3: Run AI Analysis

#### Option A: Using Streamlit UI (Recommended)

```bash
streamlit run streamlit_app.py
```

1. Navigate to **AI Analysis** page
2. Choose number of narratives to process (start with 100)
3. Click **"Start AI Analysis"**
4. View results in the dashboard

#### Option B: Using Command Line

```bash
python scripts/analyze_narratives.py \
  --input data/submissions/data.parquet \
  --output data/ai_extractions/ \
  --limit 100
```

### Step 4: Explore Results

Results are saved in `data/ai_extractions/` as:
- **Parquet files** - For local analysis
- **NDJSON files** - For BigQuery upload
- **Statistics** - Processing metrics

---

## What Gets Extracted

For each project narrative, the AI extracts:

### 1. Themes (Multi-label)
- `ai_ml` - Artificial intelligence, machine learning
- `healthcare` - Medical, health, wellness
- `education` - Learning, teaching, training
- `climate_sustainability` - Environment, renewable energy
- `finance_fintech` - Banking, payments, investing
- `social_impact` - Community, social good
- `accessibility` - Assistive technology, inclusive design
- `mobility_transportation` - Logistics, delivery, navigation
- `gaming_entertainment` - Games, media, content
- `cybersecurity` - Security, privacy, encryption
- `developer_tools` - IDEs, debugging, CI/CD
- `data_platforms` - Analytics, BI, visualization
- `ecommerce_retail` - Shopping, marketplace
- `agriculture_food` - Farming, food production
- `government_civic` - Public services, civic engagement
- `communication_collaboration` - Messaging, team tools
- `productivity` - Task management, workflow
- `iot_hardware` - IoT, sensors, robotics
- `ar_vr` - Augmented/virtual reality
- `blockchain_web3` - Blockchain, crypto, NFTs

### 2. Project Characteristics
- **Project Type**: mobile_app, web_app, api_backend, game, dashboard, etc.
- **Use Cases**: What the project does (short phrases)
- **Target Audience**: Who it's for (consumers, businesses, developers, etc.)
- **Technologies**: Normalized tech stack mentioned in narrative

### 3. Sentiment & Quality
- **Sentiment Score**: -1.0 (negative) to 1.0 (positive)
- **Enthusiasm Level**: low, neutral, high
- **Has Clear Problem**: Boolean flag
- **Has Clear Solution**: Boolean flag
- **Has Impact Metrics**: Whether narrative mentions impact/metrics

### 4. Summaries
- **Summary (200 chars)**: Concise project description
- **Key Innovation**: Main innovation or unique aspect
- **Problem Addressed**: What problem does it solve
- **Solution Approach**: How it solves the problem

### 5. Privacy & Metadata
- **Contains PII**: Flags potential privacy issues
- **Narrative Length**: Character count
- **Processed At**: Timestamp
- **Model Version**: AI model used

---

## Using the Streamlit Interface

### Tab 1: Run Analysis

1. **Choose batch size** - Start with 100-500 for testing
2. **View existing extractions** - See previous runs
3. **Click "Start AI Analysis"** - Process narratives
4. **Monitor progress** - Real-time progress bar
5. **View statistics** - Processed, cached, failed counts

**Cost Estimate**: ~$0.0001 per narrative (Gemini Flash)  
**Processing Speed**: ~1.5 seconds per narrative  
**Caching**: Results cached to avoid reprocessing

### Tab 2: View Results

Visualize extracted data:

- **Theme Distribution** - Bar chart of projects by theme
- **Project Types** - Pie chart of project type distribution
- **Sentiment Analysis** - Histogram of sentiment scores
- **Quality Indicators** - Metrics on clarity and completeness
- **Sample Extractions** - Preview of extracted data
- **Export Options** - Download as CSV or JSON

### Tab 3: Ask Questions

Natural language querying:

**Example Questions:**
- "What are the top 5 themes in healthcare projects?"
- "How many projects focus on climate and sustainability?"
- "What's the average sentiment for AI/ML projects?"
- "Which hackathons had the most innovative projects?"
- "What technologies are most commonly used in education projects?"
- "Show me projects with high enthusiasm that address accessibility"

The AI analyzes your structured data and provides data-driven answers with specific numbers and percentages.

### Tab 4: Documentation

Built-in documentation and troubleshooting guide.

---

## Command Line Usage

### Basic Analysis

```bash
# Analyze all narratives
python scripts/analyze_narratives.py \
  --input data/submissions/data.parquet \
  --output data/ai_extractions/

# Analyze first 500 (for testing)
python scripts/analyze_narratives.py \
  --input data/submissions/data.parquet \
  --output data/ai_extractions/ \
  --limit 500

# Custom taxonomy
python scripts/analyze_narratives.py \
  --input data/submissions/data.parquet \
  --output data/ai_extractions/ \
  --taxonomy custom_taxonomy.json

# Custom cache directory
python scripts/analyze_narratives.py \
  --input data/submissions/data.parquet \
  --output data/ai_extractions/ \
  --cache-dir .cache/my_cache
```

### Output Files

The script generates:
- `ai_extractions_YYYYMMDD_HHMMSS.parquet` - Structured data
- `ai_extractions_YYYYMMDD_HHMMSS.ndjson` - For BigQuery
- `stats_YYYYMMDD_HHMMSS.json` - Processing statistics

---

## Analyzing Results Locally

### Using Pandas

```python
import pandas as pd

# Load extractions
df = pd.read_parquet('data/ai_extractions/ai_extractions_20251113_223000.parquet')

# Count projects by theme
themes_exploded = df.explode('themes')
theme_counts = themes_exploded['themes'].value_counts()
print(theme_counts.head(10))

# Average sentiment by project type
sentiment_by_type = df.groupby('project_type')['sentiment_score'].mean()
print(sentiment_by_type)

# Projects with high enthusiasm and clear problem
high_quality = df[
    (df['enthusiasm_level'] == 'high') & 
    (df['has_clear_problem'] == True)
]
print(f"High quality projects: {len(high_quality)}")

# Most common use cases
use_cases_exploded = df.explode('use_cases')
use_case_counts = use_cases_exploded['use_cases'].value_counts()
print(use_case_counts.head(20))
```

### Using DuckDB

```python
import duckdb

# Query extractions with SQL
con = duckdb.connect()

# Theme distribution
result = con.execute("""
    SELECT 
        UNNEST(themes) as theme,
        COUNT(*) as count
    FROM 'data/ai_extractions/ai_extractions_*.parquet'
    GROUP BY theme
    ORDER BY count DESC
""").fetchdf()

print(result)
```

---

## Uploading to BigQuery

### Step 1: Prepare Data

Ensure you have NDJSON output:

```bash
python scripts/analyze_narratives.py \
  --input data/submissions/data.parquet \
  --output data/ai_extractions/
```

### Step 2: Upload to BigQuery

```bash
# Set environment variables
export PROJECT_ID="your-project-id"
export REGION="us-central1"

# Run upload script
./scripts/upload_to_bigquery.sh
```

The script will:
1. Create Cloud Storage bucket
2. Upload NDJSON file
3. Create BigQuery dataset
4. Load data into table
5. Create analysis views

### Step 3: Query in BigQuery

```sql
-- Theme distribution
SELECT * FROM `your-project.devpost_data.theme_summary`
ORDER BY project_count DESC;

-- Project type summary
SELECT * FROM `your-project.devpost_data.project_type_summary`;

-- Quality metrics
SELECT * FROM `your-project.devpost_data.quality_metrics`;

-- Custom queries
SELECT 
  theme,
  COUNT(*) as projects,
  ROUND(AVG(sentiment_score), 2) as avg_sentiment
FROM `your-project.devpost_data.ai_extractions`,
UNNEST(themes) as theme
WHERE 'healthcare' IN UNNEST(themes)
GROUP BY theme
ORDER BY projects DESC;
```

See `BIGQUERY_DEPLOYMENT.md` for more advanced queries.

---

## Customizing the Taxonomy

Edit `taxonomy.json` to customize themes and categories:

```json
{
  "themes": [
    "your_custom_theme",
    "another_theme"
  ],
  "theme_descriptions": {
    "your_custom_theme": "Description for AI to understand this theme"
  }
}
```

**Best Practices:**
- Keep themes specific but not too narrow
- Provide clear descriptions for AI
- Use 10-25 themes (too many reduces accuracy)
- Test with small batch before full run

---

## Cost & Performance

### Gemini API Costs

- **Model**: Gemini 1.5 Flash
- **Cost per narrative**: ~$0.0001
- **1,000 narratives**: ~$0.10
- **10,000 narratives**: ~$1.00

**Free Tier**: 15 requests per minute, 1,500 requests per day

### Processing Speed

- **Average**: 1.5 seconds per narrative
- **100 narratives**: ~2.5 minutes
- **1,000 narratives**: ~25 minutes
- **10,000 narratives**: ~4 hours

**Optimization:**
- Results are cached (reprocessing is instant)
- Process in batches during testing
- Run full analysis overnight

### Storage

- **Parquet**: ~1KB per extraction
- **10,000 extractions**: ~10MB
- **BigQuery**: First 10GB free

---

## Privacy & Security

### Data Handling

- **API Calls**: Narratives sent to Google Gemini API
- **Storage**: Results stored locally in Parquet format
- **PII Detection**: AI flags potential PII in narratives
- **No Sharing**: Data not shared with third parties

### Best Practices

1. **Review PII flags** before uploading to BigQuery
2. **Redact sensitive data** if needed
3. **Use private BigQuery datasets** for sensitive data
4. **Audit API usage** in Google Cloud Console
5. **Rotate API keys** regularly

---

## Troubleshooting

### API Key Issues

**Error**: "GEMINI_API_KEY environment variable not set"

**Solution**:
```bash
# Add to .env file
echo "GEMINI_API_KEY=your_key_here" >> .env

# Or export in shell
export GEMINI_API_KEY=your_key_here
```

### Rate Limiting

**Error**: "429 Too Many Requests"

**Solution**:
- Free tier: 15 requests/minute
- Script automatically rate limits
- Increase `min_request_interval` in code if needed

### JSON Parsing Errors

**Error**: "JSON decode error"

**Solution**:
- AI occasionally returns malformed JSON
- Errors are logged and skipped
- Check cache directory for failed extractions
- Adjust prompt in `scripts/analyze_narratives.py` if many failures

### Validation Errors

**Error**: "Validation error"

**Solution**:
- Pydantic validates extracted data
- Check `ProjectExtraction` schema
- Review error logs for specific field issues

### Cache Issues

**Error**: "Permission denied" on cache directory

**Solution**:
```bash
# Create cache directory with proper permissions
mkdir -p .cache/narratives
chmod 755 .cache/narratives
```

---

## Advanced Usage

### Custom Prompts

Edit `scripts/analyze_narratives.py` to customize the AI prompt:

```python
def _build_prompt(self, row: pd.Series) -> str:
    # Customize prompt here
    prompt = f"""Your custom instructions..."""
    return prompt
```

### Batch Processing

Process multiple files:

```bash
for file in data/submissions/*.parquet; do
    python scripts/analyze_narratives.py \
        --input "$file" \
        --output data/ai_extractions/
done
```

### Parallel Processing

For large datasets, process in parallel:

```bash
# Split data into chunks
# Process each chunk in parallel
# Combine results
```

---

## Integration with Phase 3

After AI analysis, you can build:

1. **Conversational Interface** - Chat with your data
2. **Automated Reports** - Generate insights automatically
3. **Predictive Analytics** - Forecast trends
4. **Recommendation Engine** - Suggest similar projects

---

## Examples & Use Cases

### Use Case 1: Annual Report

**Goal**: Understand what people built in 2024

**Steps**:
1. Run AI analysis on all 2024 submissions
2. Upload to BigQuery
3. Query theme distribution by quarter
4. Generate visualizations in Data Studio
5. Export insights for report

### Use Case 2: Hackathon Planning

**Goal**: Identify trending themes for next hackathon

**Steps**:
1. Analyze recent submissions
2. Compare themes year-over-year
3. Identify emerging topics
4. Design challenges around trends

### Use Case 3: Sponsor Insights

**Goal**: Show sponsors what participants are building

**Steps**:
1. Filter by sponsor's industry (e.g., healthcare)
2. Extract key innovations
3. Analyze sentiment and quality
4. Create sponsor-specific report

---

## Resources

- **Gemini API**: https://ai.google.dev/
- **API Key**: https://makersuite.google.com/app/apikey
- **Pricing**: https://ai.google.dev/pricing
- **Documentation**: https://ai.google.dev/docs

---

## Summary

This AI-powered analysis system transforms qualitative hackathon narratives into quantitative insights:

✅ **Extract structured data** from natural language  
✅ **Analyze themes, sentiment, and quality** automatically  
✅ **Query with natural language** ("What are the top trends?")  
✅ **Store in BigQuery** for advanced analysis  
✅ **Generate insights** that inform decisions  

**Next Steps**:
1. Get Gemini API key
2. Run analysis on sample data (100 narratives)
3. Review results and refine taxonomy
4. Process full dataset
5. Upload to BigQuery
6. Build dashboards and reports

---

**Questions or Issues?**  
See the main README.md or BIGQUERY_DEPLOYMENT.md for more information.
