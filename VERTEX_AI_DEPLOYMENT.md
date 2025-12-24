# Vertex AI + BigQuery Deployment Guide

## Overview

This guide provides comprehensive instructions for deploying an AI-powered narrative analysis system using **Vertex AI** and **BigQuery** to process large-scale hackathon submission data. This architecture is designed for scalability, cost-efficiency, and seamless integration with your existing data infrastructure.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Intelligence Structure & Mathematics](#intelligence-structure--mathematics)
3. [Prerequisites & Setup](#prerequisites--setup)
4. [Step-by-Step Deployment](#step-by-step-deployment)
5. [Processing Pipeline](#processing-pipeline)
6. [Natural Language Querying](#natural-language-querying)
7. [Cost Optimization](#cost-optimization)
8. [Monitoring & Maintenance](#monitoring--maintenance)
9. [Troubleshooting](#troubleshooting)
10. [Next Steps](#next-steps)

---

## Architecture Overview

### System Design

```
┌─────────────────────────────────────────────────────────────────┐
│                     Data Ingestion Layer                         │
│  Streamlit App → Export Parquet → Cloud Storage → BigQuery      │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                   Processing Layer (BigQuery)                    │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐     │
│  │ Deduplication│ →  │  Vertex AI   │ →  │   Parsing    │     │
│  │  (SHA256)    │    │   Gemini     │    │  (JSON)      │     │
│  └──────────────┘    └──────────────┘    └──────────────┘     │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                      Storage Layer                               │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐     │
│  │ Raw JSON     │    │  Structured  │    │   Failed     │     │
│  │ Responses    │    │  Extractions │    │   Retries    │     │
│  └──────────────┘    └──────────────┘    └──────────────┘     │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                     Analysis Layer                               │
│  SQL Queries  │  Natural Language Q&A  │  Visualizations        │
└─────────────────────────────────────────────────────────────────┘
```

### Key Components

1. **BigQuery Remote Models**: Call Vertex AI Gemini directly from SQL without moving data
2. **Content-Based Deduplication**: SHA256 hashing to avoid reprocessing unchanged narratives
3. **Batch Processing**: Process thousands of narratives in parallel with BigQuery's distributed engine
4. **Structured Extraction**: Convert qualitative narratives into quantitative data (themes, sentiment, use cases)
5. **Natural Language Interface**: Query results using plain English

### Why This Architecture?

- **Scalability**: BigQuery handles massive parallelism; process 10,000+ narratives efficiently
- **Cost-Effective**: Dedupe by hash, only process new/changed narratives; Gemini Flash is $0.0001/narrative
- **No Infrastructure**: No servers to manage; pure SQL + scheduled queries
- **Integrated**: Results stay in BigQuery for immediate SQL analysis, Data Studio dashboards, etc.
- **Reliable**: Built-in retry logic, error handling, and monitoring

---

## Intelligence Structure & Mathematics

### AI Model: Gemini 1.5 Flash

**Model Architecture**: Gemini 1.5 Flash is a multimodal large language model optimized for speed and efficiency. It uses a transformer-based architecture with:
- **Context Window**: 1 million tokens (sufficient for long narratives)
- **Output Format**: Structured JSON with schema validation
- **Temperature**: 0.1 (low temperature for deterministic, consistent extraction)
- **Top-K Sampling**: 1 (greedy decoding for reproducibility)

### Extraction Schema

The model extracts 21 structured fields from each narrative:

```json
{
  "themes": ["array of themes from taxonomy"],
  "theme_confidence": 0.85,
  "project_type": "web_app",
  "use_cases": ["specific use cases"],
  "target_audience": ["who this is for"],
  "technologies_mentioned": ["normalized tech names"],
  "sentiment_score": 0.7,
  "enthusiasm_level": "high",
  "summary_200": "concise summary",
  "key_innovation": "main innovation",
  "problem_addressed": "problem statement",
  "solution_approach": "solution description",
  "has_clear_problem": true,
  "has_clear_solution": true,
  "has_impact_metrics": false,
  "contains_pii": false
}
```

### Theme Taxonomy

The system uses a curated taxonomy of **20 themes** covering major domains:

1. **artificial_intelligence_ml**: AI, machine learning, neural networks, LLMs
2. **healthcare_medical**: Health, medical, wellness, fitness, mental health
3. **education_learning**: Education, e-learning, tutoring, skill development
4. **climate_sustainability**: Climate, environment, sustainability, green tech
5. **finance_fintech**: Finance, banking, payments, investing, budgeting
6. **social_impact**: Social good, community, accessibility, inclusion
7. **productivity_tools**: Productivity, workflow, automation, organization
8. **gaming_entertainment**: Games, entertainment, media, content creation
9. **communication_collaboration**: Chat, messaging, collaboration, social networking
10. **data_analytics**: Data analysis, visualization, business intelligence
11. **cybersecurity_privacy**: Security, privacy, encryption, authentication
12. **iot_hardware**: IoT, hardware, embedded systems, robotics
13. **blockchain_web3**: Blockchain, crypto, NFT, decentralized apps
14. **ar_vr**: AR, VR, mixed reality, spatial computing
15. **developer_tools**: Dev tools, APIs, SDKs, infrastructure
16. **ecommerce_retail**: E-commerce, shopping, retail, marketplace
17. **transportation_mobility**: Transportation, logistics, travel, navigation
18. **food_agriculture**: Food, agriculture, farming, nutrition
19. **real_estate_housing**: Real estate, housing, property management
20. **other**: Projects that don't fit other categories

### Sentiment Analysis Mathematics

**Sentiment Score Calculation**: The model analyzes the narrative's tone and enthusiasm using a continuous scale:

```
sentiment_score ∈ [-1.0, 1.0]

Where:
  -1.0 to -0.5: Very Negative (frustration, criticism, problems)
  -0.5 to -0.2: Negative (challenges, concerns)
  -0.2 to  0.2: Neutral (factual, descriptive)
   0.2 to  0.5: Positive (optimistic, hopeful)
   0.5 to  1.0: Very Positive (excited, enthusiastic, impactful)
```

**Enthusiasm Level**: Categorical classification based on linguistic markers:
- **Low**: Minimal excitement, factual description
- **Neutral**: Balanced tone, standard pitch
- **High**: Strong excitement, passionate language, exclamation marks

### Confidence Scoring

**Theme Confidence**: The model assigns a confidence score (0-1) to each extraction:

```
theme_confidence = P(themes are correct | narrative, taxonomy)

Threshold Strategy:
  confidence >= 0.8: High confidence (accept)
  confidence >= 0.6: Medium confidence (accept with review)
  confidence <  0.6: Low confidence (flag for manual review)
```

**Confidence Factors**:
- Narrative clarity and length
- Explicit theme mentions vs. inference
- Ambiguity in project description
- Multi-theme complexity

### Deduplication Algorithm

**Content Hashing**: SHA256 cryptographic hash function for deduplication:

```
content_hash = SHA256(narrative_text)

Properties:
  - Deterministic: Same input → same hash
  - Collision-resistant: Different inputs → different hashes (with high probability)
  - Fast: O(n) where n = narrative length
  - Storage-efficient: 64 hex characters regardless of input size
```

**Deduplication Logic**:
```sql
-- Only process narratives not yet in ai_extractions_raw
WHERE content_hash NOT IN (
  SELECT DISTINCT content_hash
  FROM ai_extractions_raw
)
```

This ensures:
- No duplicate API calls for identical narratives
- Cost savings (only pay for new/changed content)
- Consistent results (same narrative → same extraction)

---

## Prerequisites & Setup

### Required GCP Services

1. **BigQuery** - Data warehouse and processing engine
2. **Vertex AI** - AI/ML platform for Gemini access
3. **Cloud Storage** - Temporary storage for data uploads
4. **IAM** - Identity and access management

### Required Permissions

Your GCP account needs these roles:
- `roles/bigquery.admin` - Create datasets, tables, models
- `roles/aiplatform.user` - Call Vertex AI models
- `roles/storage.admin` - Create and manage Cloud Storage buckets
- `roles/iam.serviceAccountAdmin` - Grant permissions to service accounts

### Enable APIs

```bash
# Set your project
export PROJECT_ID="your-project-id"
gcloud config set project $PROJECT_ID

# Enable required APIs
gcloud services enable bigquery.googleapis.com
gcloud services enable aiplatform.googleapis.com
gcloud services enable storage.googleapis.com
```

### Choose Region

**Recommended**: `us-central1` (Iowa)

**Why?**
- Vertex AI Gemini availability
- BigQuery and Vertex AI in same region (lower latency, no egress costs)
- Competitive pricing

**Verify Gemini availability**:
```bash
gcloud ai models list --region=us-central1 | grep gemini
```

---

## Step-by-Step Deployment

### Phase 1: Infrastructure Setup (15 minutes)

#### 1.1 Create Vertex AI Connection

```bash
# Navigate to BigQuery Console
# https://console.cloud.google.com/bigquery

# Run this SQL in BigQuery Console:
```

```sql
CREATE OR REPLACE CONNECTION `us-central1.vertex_ai_connection`
LOCATION 'us-central1'
OPTIONS (
  connection_type = 'CLOUD_RESOURCE'
);
```

#### 1.2 Grant Permissions to Connection Service Account

```bash
# Get the service account email from the connection
# BigQuery Console > External Connections > vertex_ai_connection
# Copy the service account (format: bqcx-xxx@gcp-sa-bigquery-condel.iam.gserviceaccount.com)

export SERVICE_ACCOUNT="bqcx-xxx@gcp-sa-bigquery-condel.iam.gserviceaccount.com"

# Grant Vertex AI User role
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SERVICE_ACCOUNT" \
  --role="roles/aiplatform.user"
```

#### 1.3 Create BigQuery Dataset

```sql
CREATE SCHEMA IF NOT EXISTS `devpost_ai`
OPTIONS (
  location = 'us-central1',
  description = 'AI-powered analysis of hackathon narratives'
);
```

#### 1.4 Create Remote Model

```sql
CREATE OR REPLACE MODEL `devpost_ai.gemini_flash`
REMOTE WITH CONNECTION `us-central1.vertex_ai_connection`
OPTIONS (
  endpoint = 'gemini-1.5-flash'
);
```

#### 1.5 Verify Setup

```sql
-- Check connection exists
SELECT * FROM `us-central1.INFORMATION_SCHEMA.CONNECTIONS`
WHERE connection_name = 'vertex_ai_connection';

-- Check model exists
SELECT * FROM `devpost_ai.INFORMATION_SCHEMA.MODELS`
WHERE model_name = 'gemini_flash';
```

**Expected Output**: Both queries should return 1 row each.

### Phase 2: Data Loading (10 minutes)

#### 2.1 Export Data from Streamlit App

```bash
# Run Streamlit app locally
cd /path/to/Devpost-eoy-report-data
streamlit run streamlit_app.py

# Navigate to Export page
# Under "Raw Data Exports (for BigQuery)", select Parquet format
# Click "Export Submissions"
# Download file: submissions_consolidated_YYYYMMDD_HHMMSS.parquet
```

#### 2.2 Upload to Cloud Storage

```bash
# Create bucket
export BUCKET_NAME="${PROJECT_ID}-devpost-data"
gsutil mb -l us-central1 gs://${BUCKET_NAME}

# Upload data
gsutil cp submissions_consolidated_*.parquet gs://${BUCKET_NAME}/raw/submissions/
```

#### 2.3 Load into BigQuery

Run the SQL from `sql/02_load_submissions.sql`:

```sql
-- Create submissions table
CREATE OR REPLACE TABLE `devpost_ai.submissions` (
  submission_url STRING,
  project_title STRING,
  tagline STRING,
  challenge_title STRING,
  built_with STRING,
  about_the_project STRING,
  -- ... (see full schema in 02_load_submissions.sql)
);

-- Load data
LOAD DATA OVERWRITE `devpost_ai.submissions`
FROM FILES (
  format = 'PARQUET',
  uris = ['gs://YOUR_BUCKET/raw/submissions_*.parquet']
);

-- Add content hash
UPDATE `devpost_ai.submissions`
SET content_hash = TO_HEX(SHA256(CAST(about_the_project AS BYTES)))
WHERE content_hash IS NULL AND about_the_project IS NOT NULL;
```

#### 2.4 Verify Data Loaded

```sql
SELECT
  COUNT(*) AS total_submissions,
  COUNT(DISTINCT challenge_title) AS unique_hackathons,
  COUNT(DISTINCT content_hash) AS unique_narratives,
  MIN(submitted_at) AS earliest_submission,
  MAX(submitted_at) AS latest_submission
FROM `devpost_ai.submissions`;
```

### Phase 3: Processing Pipeline (30 minutes for first batch)

#### 3.1 Test Single Narrative

Run a test extraction to verify the pipeline:

```sql
-- Test with one narrative (from 03_extract_narratives.sql)
WITH test_narrative AS (
  SELECT
    submission_url,
    project_title,
    challenge_title,
    built_with,
    about_the_project
  FROM `devpost_ai.submissions`
  WHERE about_the_project IS NOT NULL
  LIMIT 1
),
test_prompt AS (
  SELECT
    CONCAT(
      'Project: ', project_title, '\n',
      'Hackathon: ', challenge_title, '\n',
      'Technologies: ', COALESCE(built_with, 'Not specified'), '\n',
      'Narrative: ', about_the_project
    ) AS prompt
  FROM test_narrative
)
SELECT
  ml_generate_text_llm_result AS response,
  ml_generate_text_status AS status
FROM
  ML.GENERATE_TEXT(
    MODEL `devpost_ai.gemini_flash`,
    (SELECT prompt FROM test_prompt),
    STRUCT(
      0.1 AS temperature,
      1024 AS max_output_tokens,
      TRUE AS flatten_json_output
    )
  );
```

**Expected Output**: JSON object with extracted themes, sentiment, etc.

#### 3.2 Process Small Batch (25 narratives)

```sql
-- Wrap in transaction for safety
BEGIN TRANSACTION;

-- Insert extractions
INSERT INTO `devpost_ai.ai_extractions_raw` (
  submission_url,
  project_title,
  challenge_title,
  content_hash,
  prompt_version,
  model_name,
  raw_json,
  processing_status
)
WITH batch_to_process AS (
  SELECT * FROM `devpost_ai.submissions_to_process`
  LIMIT 25
),
-- ... (see full query in 03_extract_narratives.sql)

-- Check results before committing
SELECT processing_status, COUNT(*) 
FROM `devpost_ai.ai_extractions_raw`
GROUP BY processing_status;

-- If looks good, commit; otherwise rollback
COMMIT TRANSACTION;
-- Or: ROLLBACK TRANSACTION;
```

#### 3.3 Parse JSON into Structured Table

```sql
INSERT INTO `devpost_ai.ai_extractions` (
  extraction_id,
  submission_url,
  themes,
  theme_confidence,
  sentiment_score,
  -- ... (see full query in 03_extract_narratives.sql)
)
SELECT
  extraction_id,
  submission_url,
  JSON_QUERY_ARRAY(raw_json, '$.themes') AS themes,
  SAFE_CAST(JSON_VALUE(raw_json, '$.theme_confidence') AS FLOAT64) AS theme_confidence,
  -- ...
FROM `devpost_ai.ai_extractions_raw`
WHERE processing_status = 'completed';
```

#### 3.4 Scale to Full Dataset

After testing, process larger batches:

```sql
-- Process 1000 narratives at a time
-- Adjust LIMIT based on quota and budget
INSERT INTO `devpost_ai.ai_extractions_raw` (...)
WITH batch_to_process AS (
  SELECT * FROM `devpost_ai.submissions_to_process`
  LIMIT 1000
)
-- ... rest of extraction logic
```

**Cost Estimate**:
- 1,000 narratives × $0.0001 = $0.10
- 10,000 narratives × $0.0001 = $1.00
- Processing time: ~1.5 seconds per narrative (parallel in BigQuery)

### Phase 4: Analysis & Querying (Ongoing)

#### 4.1 Create Analysis Views

Run the SQL from `sql/04_analyze_results.sql` to create views:

```sql
-- Theme summary
CREATE OR REPLACE VIEW `devpost_ai.theme_summary` AS
-- ... (see 04_analyze_results.sql)

-- Project type summary
CREATE OR REPLACE VIEW `devpost_ai.project_type_summary` AS
-- ...

-- Quality metrics
CREATE OR REPLACE VIEW `devpost_ai.quality_metrics` AS
-- ...
```

#### 4.2 Run Analysis Queries

```sql
-- Top themes
SELECT * FROM `devpost_ai.theme_summary`
ORDER BY project_count DESC;

-- Sentiment distribution
SELECT * FROM `devpost_ai.sentiment_summary`;

-- Quality metrics
SELECT * FROM `devpost_ai.quality_metrics`;
```

#### 4.3 Natural Language Queries

Examples:

```sql
-- "What are the top 5 healthcare projects?"
SELECT project_title, summary_200, sentiment_score
FROM `devpost_ai.ai_extractions`
WHERE 'healthcare_medical' IN UNNEST(themes)
  AND theme_confidence >= 0.6
ORDER BY sentiment_score DESC
LIMIT 5;

-- "How many AI/ML projects focus on education?"
SELECT COUNT(*) AS project_count
FROM `devpost_ai.ai_extractions`
WHERE 'artificial_intelligence_ml' IN UNNEST(themes)
  AND 'education_learning' IN UNNEST(themes)
  AND theme_confidence >= 0.6;
```

---

## Processing Pipeline

### Workflow Diagram

```
┌─────────────────────┐
│  Raw Submissions    │
│  (about_the_project)│
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Content Hashing    │
│  SHA256(narrative)  │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Deduplication      │
│  Check if processed │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Prompt Building    │
│  Title + Tech + Text│
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  ML.GENERATE_TEXT   │
│  Vertex AI Gemini   │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Store Raw JSON     │
│  ai_extractions_raw │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Parse JSON         │
│  JSON_VALUE/QUERY   │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Structured Data    │
│  ai_extractions     │
└─────────────────────┘
```

### Batch Processing Strategy

**Recommended Batch Sizes**:
- **Testing**: 25-100 narratives
- **Production**: 1,000-5,000 narratives per batch
- **Large Scale**: 10,000+ narratives (monitor quotas)

**Scheduling**:
```sql
-- Create scheduled query (BigQuery Console > Scheduled Queries)
-- Schedule: Daily at 2 AM
-- Destination: devpost_ai.ai_extractions_raw (append)

INSERT INTO `devpost_ai.ai_extractions_raw` (...)
WITH new_submissions AS (
  SELECT * FROM `devpost_ai.submissions_to_process`
  LIMIT 1000
)
-- ... extraction logic
```

---

## Natural Language Querying

### Query Templates

The system supports natural language queries that are translated to SQL:

**Pattern 1: "What are the top N [theme] projects?"**
```sql
SELECT project_title, summary_200, sentiment_score
FROM `devpost_ai.ai_extractions`
WHERE '[theme]' IN UNNEST(themes)
  AND theme_confidence >= 0.6
ORDER BY sentiment_score DESC
LIMIT N;
```

**Pattern 2: "How many projects focus on [theme1] and [theme2]?"**
```sql
SELECT COUNT(*) AS project_count
FROM `devpost_ai.ai_extractions`
WHERE '[theme1]' IN UNNEST(themes)
  AND '[theme2]' IN UNNEST(themes)
  AND theme_confidence >= 0.6;
```

**Pattern 3: "What technologies are used in [theme] projects?"**
```sql
SELECT tech, COUNT(*) AS count
FROM `devpost_ai.ai_extractions`,
UNNEST(technologies_mentioned) AS tech
WHERE '[theme]' IN UNNEST(themes)
  AND theme_confidence >= 0.6
GROUP BY tech
ORDER BY count DESC
LIMIT 20;
```

### Advanced: AI-Powered Query Generation

For complex queries, use Gemini to generate SQL:

```sql
-- Use the model to generate SQL from natural language
WITH user_question AS (
  SELECT 'Show me projects with high enthusiasm but low sentiment' AS question
),
sql_generation AS (
  SELECT
    ml_generate_text_llm_result AS generated_sql
  FROM
    ML.GENERATE_TEXT(
      MODEL `devpost_ai.gemini_flash`,
      (SELECT CONCAT(
        'Generate a BigQuery SQL query to answer: ', question,
        '\n\nAvailable table: devpost_ai.ai_extractions',
        '\n\nSchema: submission_url, project_title, themes (ARRAY<STRING>), ',
        'sentiment_score (FLOAT64), enthusiasm_level (STRING), ...',
        '\n\nReturn ONLY the SQL query, no explanation.'
      ) FROM user_question),
      STRUCT(0.2 AS temperature, 512 AS max_output_tokens)
    )
)
SELECT generated_sql FROM sql_generation;
```

---

## Cost Optimization

### Cost Breakdown

**Vertex AI Gemini 1.5 Flash Pricing** (as of 2025):
- Input: $0.000125 per 1K characters
- Output: $0.000375 per 1K characters
- Average narrative: 800 characters input, 200 characters output
- **Cost per narrative**: ~$0.0001 (1/100th of a cent)

**BigQuery Pricing**:
- Storage: $0.02 per GB per month (negligible for this use case)
- Queries: $6.25 per TB processed (most queries < 1 GB)
- ML.GENERATE_TEXT: Charged as Vertex AI calls (above)

**Example Costs**:
- 1,000 narratives: $0.10
- 10,000 narratives: $1.00
- 100,000 narratives: $10.00

### Cost Optimization Strategies

1. **Deduplication**: SHA256 hashing ensures you never process the same narrative twice
2. **Batch Processing**: Process in batches to monitor costs incrementally
3. **Confidence Thresholds**: Filter low-confidence results to reduce downstream processing
4. **Scheduled Queries**: Process only new submissions daily (not full dataset)
5. **Gemini Flash vs Pro**: Use Flash (10x cheaper) for extraction; reserve Pro for complex reasoning

### Quota Management

**Vertex AI Quotas** (default):
- Requests per minute: 300
- Requests per day: 30,000

**Monitor Usage**:
```bash
gcloud ai quotas list --region=us-central1 --filter="metric:aiplatform.googleapis.com"
```

**Request Quota Increase**:
```bash
# If you need higher throughput
gcloud alpha services quota update \
  --service=aiplatform.googleapis.com \
  --consumer=projects/$PROJECT_ID \
  --metric=aiplatform.googleapis.com/generate_content_requests_per_minute \
  --value=1000
```

---

## Monitoring & Maintenance

### Key Metrics to Track

1. **Processing Coverage**:
```sql
SELECT
  ROUND((SELECT COUNT(*) FROM `devpost_ai.ai_extractions`) * 100.0 /
    NULLIF((SELECT COUNT(*) FROM `devpost_ai.submissions` 
            WHERE about_the_project IS NOT NULL), 0), 2) AS coverage_pct;
```

2. **Extraction Quality**:
```sql
SELECT
  AVG(theme_confidence) AS avg_confidence,
  AVG(ARRAY_LENGTH(themes)) AS avg_themes_per_project,
  AVG(sentiment_score) AS avg_sentiment
FROM `devpost_ai.ai_extractions`;
```

3. **Failure Rate**:
```sql
SELECT
  processing_status,
  COUNT(*) AS count,
  ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) AS pct
FROM `devpost_ai.ai_extractions_raw`
GROUP BY processing_status;
```

4. **Cost Tracking**:
```sql
SELECT
  DATE(processed_at) AS date,
  COUNT(*) AS narratives_processed,
  COUNT(*) * 0.0001 AS estimated_cost_usd
FROM `devpost_ai.ai_extractions_raw`
WHERE processing_status = 'completed'
GROUP BY date
ORDER BY date DESC;
```

### Alerts & Notifications

Set up BigQuery scheduled queries with email notifications:

```sql
-- Alert if failure rate > 5%
WITH failure_rate AS (
  SELECT
    COUNT(CASE WHEN processing_status = 'failed' THEN 1 END) * 100.0 / COUNT(*) AS pct
  FROM `devpost_ai.ai_extractions_raw`
  WHERE processed_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 DAY)
)
SELECT
  CASE
    WHEN pct > 5 THEN 'ALERT: High failure rate'
    ELSE 'OK'
  END AS status,
  pct
FROM failure_rate;
```

---

## Troubleshooting

### Common Issues

#### Issue 1: "Permission denied" when creating connection

**Cause**: Insufficient permissions

**Solution**:
```bash
# Grant yourself BigQuery Admin role
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="user:YOUR_EMAIL@example.com" \
  --role="roles/bigquery.admin"
```

#### Issue 2: "Model not found" or "Endpoint not available"

**Cause**: Gemini not available in your region

**Solution**: Use `us-central1` region or check availability:
```bash
gcloud ai models list --region=us-central1 | grep gemini
```

#### Issue 3: ML.GENERATE_TEXT returns errors

**Cause**: Service account lacks Vertex AI permissions

**Solution**:
```bash
# Get service account from connection
export SA="bqcx-xxx@gcp-sa-bigquery-condel.iam.gserviceaccount.com"

# Grant Vertex AI User role
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SA" \
  --role="roles/aiplatform.user"
```

#### Issue 4: JSON parsing failures

**Cause**: Model returns malformed JSON

**Solution**: Use SAFE.PARSE_JSON and retry logic:
```sql
-- Check failed parses
SELECT
  extraction_id,
  raw_json,
  error_message
FROM `devpost_ai.ai_extractions_failed`
LIMIT 10;

-- Retry with repair prompt
-- (implement retry logic with stricter instructions)
```

#### Issue 5: High costs

**Cause**: Processing duplicates or too many narratives

**Solution**:
- Verify deduplication is working (check content_hash)
- Process in smaller batches
- Apply confidence thresholds to reduce low-quality extractions

---

## Next Steps

### Immediate Actions

1. ✅ Complete infrastructure setup (Phase 1)
2. ✅ Load submission data (Phase 2)
3. ✅ Test with small batch (25 narratives)
4. ✅ Review results and adjust prompts if needed
5. ✅ Scale to full dataset (1000+ narratives)

### Short-Term Enhancements

1. **Prompt Tuning**: Refine system instructions based on extraction quality
2. **Confidence Thresholds**: Implement automated filtering for low-confidence extractions
3. **Retry Logic**: Build automated retry for failed extractions
4. **Dashboards**: Create Data Studio dashboards for visualization
5. **Scheduled Processing**: Set up daily scheduled queries for new submissions

### Long-Term Roadmap

1. **Embeddings & Semantic Search**: Add vector embeddings for similarity search
2. **Fine-Tuning**: Fine-tune Gemini on your specific domain for better accuracy
3. **Multi-Language Support**: Detect and translate non-English narratives
4. **Real-Time Processing**: Stream processing for live hackathon submissions
5. **Advanced Analytics**: Predictive models for project success, trend forecasting

---

## Additional Resources

### Documentation
- [BigQuery Remote Models](https://cloud.google.com/bigquery/docs/remote-models)
- [Vertex AI Gemini API](https://cloud.google.com/vertex-ai/docs/generative-ai/model-reference/gemini)
- [BigQuery ML.GENERATE_TEXT](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-generate-text)

### SQL Scripts
- `sql/01_setup_vertex_ai.sql` - Infrastructure setup
- `sql/02_load_submissions.sql` - Data loading
- `sql/03_extract_narratives.sql` - Processing pipeline
- `sql/04_analyze_results.sql` - Analysis queries

### Support
- GitHub Issues: [jdanjohnson/Devpost-eoy-report-data/issues](https://github.com/jdanjohnson/Devpost-eoy-report-data/issues)
- GCP Support: https://cloud.google.com/support

---

## Summary

You now have a complete, production-ready system for AI-powered narrative analysis at scale using Vertex AI and BigQuery. This architecture:

- ✅ Processes thousands of narratives efficiently
- ✅ Extracts structured, quantitative data from qualitative text
- ✅ Enables natural language querying
- ✅ Integrates seamlessly with your existing BigQuery infrastructure
- ✅ Optimizes costs through deduplication and batch processing
- ✅ Provides comprehensive monitoring and error handling

**Ready to deploy!** Follow the step-by-step guide above to get started.
