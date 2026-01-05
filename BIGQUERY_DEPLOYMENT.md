# BigQuery Deployment Guide - Phase 2: Custom Submission Data Analysis

**Version:** 2.0  
**Date:** November 13, 2025  
**Purpose:** Deploy Devpost hackathon data to BigQuery for advanced analysis of custom submission narratives

## Overview

This guide walks you through deploying your processed hackathon data to Google BigQuery, specifically focusing on **Phase 2** capabilities: analyzing custom submission data to understand what people are building through their project narratives.

### What is Phase 2?

Phase 2 focuses on analyzing the **"About The Project"** field in submission data to gain insights into:
- What types of projects participants are building
- Common themes and topics across submissions
- Technology combinations and use cases
- Project complexity and innovation patterns
- Trends in problem-solving approaches

### Why BigQuery?

BigQuery provides powerful capabilities for analyzing large datasets:
- **SQL-based analysis** - Familiar query language for data exploration
- **Scalability** - Handle millions of records efficiently
- **Built-in ML** - Use BigQuery ML for sentiment analysis, topic modeling, and text classification
- **Integration** - Connect to Data Studio, Looker, and other BI tools
- **Cost-effective** - Pay only for queries you run (first 1TB/month free)

---

## Architecture

```
Streamlit App (Phase 1)
    ↓
Export Data (Parquet/CSV)
    ↓
Google Cloud Storage
    ↓
BigQuery Tables
    ↓
SQL Analysis + BigQuery ML
    ↓
Insights & Reports
```

---

## Prerequisites

### 1. Google Cloud Setup

- **Google Cloud Account** with billing enabled
- **Project created** in Google Cloud Console
- **gcloud CLI** installed and authenticated

```bash
# Install gcloud CLI (if not already installed)
# Visit: https://cloud.google.com/sdk/docs/install

# Authenticate
gcloud auth login

# Set your project
export PROJECT_ID="your-project-id"
gcloud config set project $PROJECT_ID

# Enable required APIs
gcloud services enable bigquery.googleapis.com
gcloud services enable storage.googleapis.com
gcloud services enable bigquerydatatransfer.googleapis.com
```

### 2. Processed Data

You need to have already processed your hackathon data using the Streamlit app (Phase 1). This guide assumes you have:
- Submission data with "About The Project" narratives
- Registrant data (optional, for demographic analysis)
- Data processed and deduplicated

---

## Step 1: Export Data from Streamlit App

### 1.1 Start the Streamlit Application

```bash
cd /path/to/Devpost-eoy-report-data
source venv/bin/activate
streamlit run streamlit_app.py
```

### 1.2 Export Submissions Data

1. Navigate to the **Export** page in the Streamlit app
2. Under "📦 Raw Data Exports (for BigQuery)", select the **Submissions Data** section
3. Choose export format:
   - **Parquet** (recommended) - Most efficient for BigQuery, smaller file size
   - **CSV** - Universal format, easier to inspect manually
   - **XLSX** - Excel format, good for manual review but not recommended for BigQuery

4. Click **"📥 Export All Submissions"**
5. Download the generated file (e.g., `submissions_consolidated_20251113_223000.parquet`)

### 1.3 Export Registrants Data (Optional)

Repeat the same process for registrants data if you want to correlate project narratives with participant demographics.

### 1.4 Verify Export

The exported submissions file should contain these key columns:
- `Organization Name` - Hackathon organizer
- `Challenge Title` - Hackathon name
- `Challenge Published At` - Hackathon date
- `Project Title` - Submission title
- `Submission Url` - Unique identifier
- `Project Created At` - Submission timestamp
- **`About The Project`** - Project narrative (this is what we'll analyze in Phase 2)
- `Built With` - Technologies used
- `Additional Team Member Count` - Team size

---

## Step 2: Upload Data to Google Cloud Storage

### 2.1 Create a Cloud Storage Bucket

```bash
# Set variables
export PROJECT_ID="your-project-id"
export BUCKET_NAME="${PROJECT_ID}-devpost-data"
export REGION="us-central1"

# Create bucket
gsutil mb -p $PROJECT_ID -l $REGION gs://${BUCKET_NAME}

# Create directory structure
gsutil -m cp /dev/null gs://${BUCKET_NAME}/raw/submissions/.keep
gsutil -m cp /dev/null gs://${BUCKET_NAME}/raw/registrants/.keep
gsutil -m cp /dev/null gs://${BUCKET_NAME}/processed/.keep
```

### 2.2 Upload Exported Data

```bash
# Upload submissions data (adjust filename as needed)
gsutil cp submissions_consolidated_20251113_223000.parquet \
  gs://${BUCKET_NAME}/raw/submissions/

# Upload registrants data (optional)
gsutil cp registrants_consolidated_20251113_223000.parquet \
  gs://${BUCKET_NAME}/raw/registrants/

# Verify upload
gsutil ls -lh gs://${BUCKET_NAME}/raw/submissions/
```

---

## Step 3: Create BigQuery Dataset and Tables

### 3.1 Create Dataset

```bash
# Create dataset for hackathon data
bq mk --dataset \
  --location=$REGION \
  --description="Devpost hackathon data for analysis" \
  ${PROJECT_ID}:devpost_data
```

### 3.2 Load Submissions Data into BigQuery

#### Option A: Load from Parquet (Recommended)

```bash
# Load submissions from Parquet file
bq load \
  --source_format=PARQUET \
  --autodetect \
  --replace \
  devpost_data.submissions \
  gs://${BUCKET_NAME}/raw/submissions/submissions_consolidated_*.parquet
```

#### Option B: Load from CSV

```bash
# Load submissions from CSV file
bq load \
  --source_format=CSV \
  --autodetect \
  --skip_leading_rows=1 \
  --replace \
  devpost_data.submissions \
  gs://${BUCKET_NAME}/raw/submissions/submissions_consolidated_*.csv
```

### 3.3 Load Registrants Data (Optional)

```bash
# Load registrants from Parquet
bq load \
  --source_format=PARQUET \
  --autodetect \
  --replace \
  devpost_data.registrants \
  gs://${BUCKET_NAME}/raw/registrants/registrants_consolidated_*.parquet
```

### 3.4 Verify Tables

```bash
# List tables in dataset
bq ls devpost_data

# Show table schema
bq show devpost_data.submissions

# Preview data
bq head -n 10 devpost_data.submissions
```

---

## Step 4: Explore Data with SQL

### 4.1 Basic Data Exploration

```sql
-- Count total submissions
SELECT COUNT(*) as total_submissions
FROM `devpost_data.submissions`;

-- Count submissions by hackathon
SELECT 
  `Challenge Title` as hackathon,
  COUNT(*) as submission_count
FROM `devpost_data.submissions`
GROUP BY hackathon
ORDER BY submission_count DESC
LIMIT 20;

-- View sample project narratives
SELECT 
  `Project Title`,
  `About The Project`,
  `Built With`,
  `Challenge Title`
FROM `devpost_data.submissions`
WHERE `About The Project` IS NOT NULL
LIMIT 10;
```

### 4.2 Analyze Project Narratives

```sql
-- Count submissions with narratives
SELECT 
  COUNT(*) as total_submissions,
  COUNTIF(`About The Project` IS NOT NULL AND LENGTH(`About The Project`) > 0) as with_narrative,
  COUNTIF(`About The Project` IS NULL OR LENGTH(`About The Project`) = 0) as without_narrative,
  ROUND(COUNTIF(`About The Project` IS NOT NULL AND LENGTH(`About The Project`) > 0) * 100.0 / COUNT(*), 2) as narrative_percentage
FROM `devpost_data.submissions`;

-- Average narrative length
SELECT 
  AVG(LENGTH(`About The Project`)) as avg_narrative_length,
  MIN(LENGTH(`About The Project`)) as min_length,
  MAX(LENGTH(`About The Project`)) as max_length,
  APPROX_QUANTILES(LENGTH(`About The Project`), 100)[OFFSET(50)] as median_length
FROM `devpost_data.submissions`
WHERE `About The Project` IS NOT NULL;

-- Narrative length distribution
SELECT 
  CASE 
    WHEN LENGTH(`About The Project`) < 100 THEN '0-100 chars'
    WHEN LENGTH(`About The Project`) < 500 THEN '100-500 chars'
    WHEN LENGTH(`About The Project`) < 1000 THEN '500-1000 chars'
    WHEN LENGTH(`About The Project`) < 2000 THEN '1000-2000 chars'
    ELSE '2000+ chars'
  END as length_range,
  COUNT(*) as count
FROM `devpost_data.submissions`
WHERE `About The Project` IS NOT NULL
GROUP BY length_range
ORDER BY MIN(LENGTH(`About The Project`));
```

---

## Step 5: Phase 2 Analysis - Understanding What People Are Building

### 5.1 Keyword and Theme Analysis

```sql
-- Find projects mentioning specific keywords (e.g., "AI", "machine learning")
SELECT 
  `Project Title`,
  `About The Project`,
  `Built With`,
  `Challenge Title`
FROM `devpost_data.submissions`
WHERE LOWER(`About The Project`) LIKE '%machine learning%'
   OR LOWER(`About The Project`) LIKE '%artificial intelligence%'
   OR LOWER(`About The Project`) LIKE '%ai%'
LIMIT 100;

-- Count projects by common themes
SELECT 
  'AI/ML' as theme,
  COUNT(*) as project_count
FROM `devpost_data.submissions`
WHERE LOWER(`About The Project`) LIKE '%machine learning%'
   OR LOWER(`About The Project`) LIKE '%artificial intelligence%'
   OR LOWER(`About The Project`) LIKE '%neural network%'
   OR LOWER(`About The Project`) LIKE '%deep learning%'

UNION ALL

SELECT 
  'Healthcare' as theme,
  COUNT(*) as project_count
FROM `devpost_data.submissions`
WHERE LOWER(`About The Project`) LIKE '%health%'
   OR LOWER(`About The Project`) LIKE '%medical%'
   OR LOWER(`About The Project`) LIKE '%patient%'
   OR LOWER(`About The Project`) LIKE '%diagnosis%'

UNION ALL

SELECT 
  'Education' as theme,
  COUNT(*) as project_count
FROM `devpost_data.submissions`
WHERE LOWER(`About The Project`) LIKE '%education%'
   OR LOWER(`About The Project`) LIKE '%learning%'
   OR LOWER(`About The Project`) LIKE '%student%'
   OR LOWER(`About The Project`) LIKE '%teaching%'

UNION ALL

SELECT 
  'Climate/Sustainability' as theme,
  COUNT(*) as project_count
FROM `devpost_data.submissions`
WHERE LOWER(`About The Project`) LIKE '%climate%'
   OR LOWER(`About The Project`) LIKE '%sustainability%'
   OR LOWER(`About The Project`) LIKE '%environment%'
   OR LOWER(`About The Project`) LIKE '%carbon%'

ORDER BY project_count DESC;
```

### 5.2 Technology and Use Case Correlation

```sql
-- Analyze what technologies are used for different project types
SELECT 
  CASE 
    WHEN LOWER(`About The Project`) LIKE '%mobile app%' OR LOWER(`About The Project`) LIKE '%ios%' OR LOWER(`About The Project`) LIKE '%android%' THEN 'Mobile App'
    WHEN LOWER(`About The Project`) LIKE '%web app%' OR LOWER(`About The Project`) LIKE '%website%' THEN 'Web App'
    WHEN LOWER(`About The Project`) LIKE '%game%' OR LOWER(`About The Project`) LIKE '%gaming%' THEN 'Game'
    WHEN LOWER(`About The Project`) LIKE '%api%' OR LOWER(`About The Project`) LIKE '%backend%' THEN 'API/Backend'
    WHEN LOWER(`About The Project`) LIKE '%dashboard%' OR LOWER(`About The Project`) LIKE '%visualization%' THEN 'Dashboard/Viz'
    ELSE 'Other'
  END as project_type,
  COUNT(*) as count,
  ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) as percentage
FROM `devpost_data.submissions`
WHERE `About The Project` IS NOT NULL
GROUP BY project_type
ORDER BY count DESC;
```

### 5.3 Problem-Solution Analysis

```sql
-- Extract projects that mention specific problem domains
CREATE OR REPLACE TABLE `devpost_data.project_themes` AS
SELECT 
  `Submission Url`,
  `Project Title`,
  `About The Project`,
  `Built With`,
  `Challenge Title`,
  `Organization Name`,
  `Project Created At`,
  
  -- Theme flags
  CASE WHEN LOWER(`About The Project`) LIKE '%ai%' OR LOWER(`About The Project`) LIKE '%machine learning%' OR LOWER(`About The Project`) LIKE '%artificial intelligence%' THEN 1 ELSE 0 END as has_ai_ml,
  CASE WHEN LOWER(`About The Project`) LIKE '%health%' OR LOWER(`About The Project`) LIKE '%medical%' THEN 1 ELSE 0 END as has_healthcare,
  CASE WHEN LOWER(`About The Project`) LIKE '%education%' OR LOWER(`About The Project`) LIKE '%learning%' OR LOWER(`About The Project`) LIKE '%student%' THEN 1 ELSE 0 END as has_education,
  CASE WHEN LOWER(`About The Project`) LIKE '%climate%' OR LOWER(`About The Project`) LIKE '%sustainability%' OR LOWER(`About The Project`) LIKE '%environment%' THEN 1 ELSE 0 END as has_climate,
  CASE WHEN LOWER(`About The Project`) LIKE '%finance%' OR LOWER(`About The Project`) LIKE '%payment%' OR LOWER(`About The Project`) LIKE '%banking%' THEN 1 ELSE 0 END as has_finance,
  CASE WHEN LOWER(`About The Project`) LIKE '%social%' OR LOWER(`About The Project`) LIKE '%community%' THEN 1 ELSE 0 END as has_social,
  CASE WHEN LOWER(`About The Project`) LIKE '%accessibility%' OR LOWER(`About The Project`) LIKE '%disability%' THEN 1 ELSE 0 END as has_accessibility,
  
  -- Project type flags
  CASE WHEN LOWER(`About The Project`) LIKE '%mobile%' OR LOWER(`About The Project`) LIKE '%ios%' OR LOWER(`About The Project`) LIKE '%android%' THEN 1 ELSE 0 END as is_mobile,
  CASE WHEN LOWER(`About The Project`) LIKE '%web%' OR LOWER(`About The Project`) LIKE '%website%' THEN 1 ELSE 0 END as is_web,
  CASE WHEN LOWER(`About The Project`) LIKE '%game%' THEN 1 ELSE 0 END as is_game,
  
  LENGTH(`About The Project`) as narrative_length

FROM `devpost_data.submissions`
WHERE `About The Project` IS NOT NULL;

-- Analyze theme distribution
SELECT 
  SUM(has_ai_ml) as ai_ml_projects,
  SUM(has_healthcare) as healthcare_projects,
  SUM(has_education) as education_projects,
  SUM(has_climate) as climate_projects,
  SUM(has_finance) as finance_projects,
  SUM(has_social) as social_projects,
  SUM(has_accessibility) as accessibility_projects
FROM `devpost_data.project_themes`;
```

### 5.4 Time-based Trend Analysis

```sql
-- Analyze how project themes change over time
SELECT 
  EXTRACT(YEAR FROM `Project Created At`) as year,
  EXTRACT(MONTH FROM `Project Created At`) as month,
  SUM(has_ai_ml) as ai_ml_count,
  SUM(has_healthcare) as healthcare_count,
  SUM(has_education) as education_count,
  SUM(has_climate) as climate_count,
  COUNT(*) as total_projects
FROM `devpost_data.project_themes`
WHERE `Project Created At` IS NOT NULL
GROUP BY year, month
ORDER BY year DESC, month DESC;
```

---

## Step 6: Advanced Analysis with BigQuery ML

### 6.1 Sentiment Analysis

Analyze the sentiment of project narratives to understand enthusiasm and tone:

```sql
-- Create sentiment analysis model
CREATE OR REPLACE MODEL `devpost_data.narrative_sentiment`
OPTIONS(
  model_type='SENTIMENT_ANALYSIS'
) AS
SELECT `About The Project` as text_content
FROM `devpost_data.submissions`
WHERE `About The Project` IS NOT NULL
LIMIT 1000;  -- Start with a sample

-- Apply sentiment analysis
SELECT 
  `Project Title`,
  `About The Project`,
  ml.sentiment as sentiment_score,
  ml.magnitude as sentiment_magnitude
FROM 
  ML.ANALYZE_SENTIMENT(
    MODEL `devpost_data.narrative_sentiment`,
    (SELECT `Project Title`, `About The Project` 
     FROM `devpost_data.submissions` 
     WHERE `About The Project` IS NOT NULL
     LIMIT 100)
  );
```

### 6.2 Topic Modeling

Discover common topics across project narratives:

```sql
-- Create topic model
CREATE OR REPLACE MODEL `devpost_data.narrative_topics`
OPTIONS(
  model_type='TOPIC_MODEL',
  num_topics=10
) AS
SELECT `About The Project` as text_content
FROM `devpost_data.submissions`
WHERE `About The Project` IS NOT NULL
  AND LENGTH(`About The Project`) > 100;

-- Extract topics
SELECT * 
FROM ML.PREDICT(
  MODEL `devpost_data.narrative_topics`,
  (SELECT `About The Project` as text_content 
   FROM `devpost_data.submissions` 
   WHERE `About The Project` IS NOT NULL
   LIMIT 100)
);
```

### 6.3 Text Classification

Classify projects into categories based on narratives:

```sql
-- First, create a training dataset with labeled examples
-- You'll need to manually label some examples or use keyword-based labels

CREATE OR REPLACE TABLE `devpost_data.labeled_projects` AS
SELECT 
  `About The Project`,
  CASE 
    WHEN LOWER(`About The Project`) LIKE '%health%' OR LOWER(`About The Project`) LIKE '%medical%' THEN 'Healthcare'
    WHEN LOWER(`About The Project`) LIKE '%education%' OR LOWER(`About The Project`) LIKE '%learning%' THEN 'Education'
    WHEN LOWER(`About The Project`) LIKE '%climate%' OR LOWER(`About The Project`) LIKE '%environment%' THEN 'Climate'
    WHEN LOWER(`About The Project`) LIKE '%finance%' OR LOWER(`About The Project`) LIKE '%payment%' THEN 'Finance'
    ELSE 'Other'
  END as category
FROM `devpost_data.submissions`
WHERE `About The Project` IS NOT NULL
  AND LENGTH(`About The Project`) > 50;

-- Create classification model
CREATE OR REPLACE MODEL `devpost_data.project_classifier`
OPTIONS(
  model_type='LOGISTIC_REG',
  input_label_cols=['category']
) AS
SELECT 
  `About The Project`,
  category
FROM `devpost_data.labeled_projects`;

-- Evaluate model
SELECT *
FROM ML.EVALUATE(MODEL `devpost_data.project_classifier`);

-- Classify new projects
SELECT 
  `Project Title`,
  `About The Project`,
  predicted_category,
  predicted_category_probs
FROM ML.PREDICT(
  MODEL `devpost_data.project_classifier`,
  (SELECT `Project Title`, `About The Project` 
   FROM `devpost_data.submissions` 
   WHERE `About The Project` IS NOT NULL
   LIMIT 100)
);
```

---

## Step 7: Create Analysis Views and Reports

### 7.1 Create Useful Views

```sql
-- View: Project summary with themes
CREATE OR REPLACE VIEW `devpost_data.project_summary` AS
SELECT 
  s.`Submission Url`,
  s.`Project Title`,
  s.`Challenge Title`,
  s.`Organization Name`,
  s.`Project Created At`,
  s.`Built With`,
  LENGTH(s.`About The Project`) as narrative_length,
  pt.has_ai_ml,
  pt.has_healthcare,
  pt.has_education,
  pt.has_climate,
  pt.has_finance,
  pt.has_social,
  pt.is_mobile,
  pt.is_web,
  pt.is_game
FROM `devpost_data.submissions` s
LEFT JOIN `devpost_data.project_themes` pt
  ON s.`Submission Url` = pt.`Submission Url`;

-- View: Hackathon-level aggregations
CREATE OR REPLACE VIEW `devpost_data.hackathon_themes` AS
SELECT 
  `Challenge Title` as hackathon,
  `Organization Name` as organizer,
  COUNT(*) as total_submissions,
  SUM(has_ai_ml) as ai_ml_projects,
  SUM(has_healthcare) as healthcare_projects,
  SUM(has_education) as education_projects,
  SUM(has_climate) as climate_projects,
  ROUND(SUM(has_ai_ml) * 100.0 / COUNT(*), 2) as ai_ml_percentage,
  ROUND(SUM(has_healthcare) * 100.0 / COUNT(*), 2) as healthcare_percentage,
  ROUND(SUM(has_education) * 100.0 / COUNT(*), 2) as education_percentage,
  ROUND(SUM(has_climate) * 100.0 / COUNT(*), 2) as climate_percentage
FROM `devpost_data.project_themes`
GROUP BY hackathon, organizer
ORDER BY total_submissions DESC;
```

### 7.2 Export Results

```bash
# Export analysis results to CSV
bq extract \
  --destination_format=CSV \
  devpost_data.hackathon_themes \
  gs://${BUCKET_NAME}/processed/hackathon_themes.csv

# Download to local machine
gsutil cp gs://${BUCKET_NAME}/processed/hackathon_themes.csv ./
```

---

## Step 8: Connect to Visualization Tools

### 8.1 Google Data Studio

1. Go to [Google Data Studio](https://datastudio.google.com/)
2. Create a new report
3. Add data source → BigQuery
4. Select your project → `devpost_data` dataset
5. Choose tables or views to visualize
6. Create dashboards with:
   - Theme distribution over time
   - Top hackathons by theme
   - Technology usage by project type
   - Narrative length trends

### 8.2 Looker Studio

Similar to Data Studio, connect your BigQuery dataset and create interactive dashboards.

### 8.3 Export to Spreadsheets

```sql
-- Create a summary for export
SELECT 
  `Challenge Title`,
  COUNT(*) as submissions,
  SUM(has_ai_ml) as ai_projects,
  SUM(has_healthcare) as health_projects,
  SUM(has_education) as edu_projects,
  AVG(narrative_length) as avg_narrative_length
FROM `devpost_data.project_themes`
GROUP BY `Challenge Title`
ORDER BY submissions DESC;
```

---

## Cost Optimization

### Query Cost Estimation

```bash
# Estimate query cost before running
bq query --dry_run --use_legacy_sql=false \
  'SELECT COUNT(*) FROM `devpost_data.submissions`'
```

### Best Practices

1. **Use LIMIT** when exploring data
2. **Partition tables** by date for time-based queries
3. **Cluster tables** by frequently filtered columns
4. **Use views** to avoid rewriting complex queries
5. **Monitor costs** in Google Cloud Console

### Free Tier

- First 1 TB of query data processed per month is free
- 10 GB of storage per month is free
- Most analysis queries will stay within free tier

---

## Common Analysis Queries

### Find Most Innovative Projects

```sql
-- Projects with longest narratives (often more detailed/innovative)
SELECT 
  `Project Title`,
  `Challenge Title`,
  LENGTH(`About The Project`) as narrative_length,
  `Built With`,
  `Submission Url`
FROM `devpost_data.submissions`
WHERE `About The Project` IS NOT NULL
ORDER BY narrative_length DESC
LIMIT 50;
```

### Technology Combinations

```sql
-- Find common technology combinations
SELECT 
  `Built With`,
  COUNT(*) as usage_count,
  ARRAY_AGG(`Project Title` LIMIT 5) as example_projects
FROM `devpost_data.submissions`
WHERE `Built With` IS NOT NULL
GROUP BY `Built With`
HAVING COUNT(*) > 5
ORDER BY usage_count DESC
LIMIT 100;
```

### Cross-Theme Projects

```sql
-- Projects that span multiple themes
SELECT 
  `Project Title`,
  `Challenge Title`,
  (has_ai_ml + has_healthcare + has_education + has_climate + has_finance + has_social) as theme_count,
  CONCAT(
    IF(has_ai_ml = 1, 'AI/ML, ', ''),
    IF(has_healthcare = 1, 'Healthcare, ', ''),
    IF(has_education = 1, 'Education, ', ''),
    IF(has_climate = 1, 'Climate, ', ''),
    IF(has_finance = 1, 'Finance, ', ''),
    IF(has_social = 1, 'Social, ', '')
  ) as themes
FROM `devpost_data.project_themes`
WHERE (has_ai_ml + has_healthcare + has_education + has_climate + has_finance + has_social) >= 2
ORDER BY theme_count DESC
LIMIT 100;
```

---

## Troubleshooting

### Issue: Table not found

**Solution:** Verify dataset and table names:
```bash
bq ls devpost_data
bq show devpost_data.submissions
```

### Issue: Permission denied

**Solution:** Grant yourself BigQuery permissions:
```bash
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="user:your-email@example.com" \
  --role="roles/bigquery.admin"
```

### Issue: Query timeout

**Solution:** Add LIMIT clause or optimize query:
```sql
-- Instead of scanning all rows
SELECT * FROM `devpost_data.submissions` LIMIT 1000;
```

### Issue: Schema mismatch

**Solution:** Recreate table with explicit schema:
```bash
bq rm -f devpost_data.submissions
bq load --source_format=PARQUET --autodetect devpost_data.submissions gs://...
```

---

## Next Steps

### Phase 3: Conversational Querying

After analyzing your data in BigQuery, you can build:
- Natural language query interface
- AI-powered insights generation
- Automated report generation
- Predictive analytics for future hackathons

### Integration Ideas

1. **Slack Bot** - Query BigQuery from Slack
2. **Email Reports** - Scheduled analysis reports
3. **API Endpoints** - Expose insights via REST API
4. **Real-time Dashboard** - Live metrics and trends

---

## Resources

- [BigQuery Documentation](https://cloud.google.com/bigquery/docs)
- [BigQuery ML Documentation](https://cloud.google.com/bigquery-ml/docs)
- [BigQuery Pricing](https://cloud.google.com/bigquery/pricing)
- [SQL Reference](https://cloud.google.com/bigquery/docs/reference/standard-sql/query-syntax)
- [Data Studio](https://datastudio.google.com/)

---

## Summary

This guide walked you through:
1. ✅ Exporting processed data from Streamlit app
2. ✅ Uploading data to Google Cloud Storage
3. ✅ Creating BigQuery tables
4. ✅ Analyzing custom submission narratives (Phase 2)
5. ✅ Using BigQuery ML for advanced analysis
6. ✅ Creating views and reports
7. ✅ Connecting to visualization tools

You now have a complete pipeline for understanding what people are building through their hackathon submissions!

---

**Questions or Issues?**  
Refer to the main README.md or contact the development team.
