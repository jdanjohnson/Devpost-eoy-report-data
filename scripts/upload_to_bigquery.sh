#!/bin/bash
# 
#
#

set -e

PROJECT_ID="${PROJECT_ID:-your-project-id}"
DATASET="devpost_data"
TABLE="ai_extractions"
REGION="${REGION:-us-central1}"
BUCKET_NAME="${BUCKET_NAME:-${PROJECT_ID}-devpost-data}"

GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}BigQuery Upload Script${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}Error: gcloud CLI not found${NC}"
    echo "Install from: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

if ! command -v bq &> /dev/null; then
    echo -e "${RED}Error: bq command not found${NC}"
    echo "Install BigQuery CLI: gcloud components install bq"
    exit 1
fi

if ! command -v gsutil &> /dev/null; then
    echo -e "${RED}Error: gsutil not found${NC}"
    echo "Install from: https://cloud.google.com/storage/docs/gsutil_install"
    exit 1
fi

if [ "$PROJECT_ID" = "your-project-id" ]; then
    read -p "Enter your Google Cloud Project ID: " PROJECT_ID
fi

echo -e "${GREEN}Using Project ID: ${PROJECT_ID}${NC}"
echo -e "${GREEN}Dataset: ${DATASET}${NC}"
echo -e "${GREEN}Table: ${TABLE}${NC}"
echo ""

gcloud config set project $PROJECT_ID

EXTRACTION_FILE=$(ls -t data/ai_extractions/ai_extractions_*.ndjson 2>/dev/null | head -1)

if [ -z "$EXTRACTION_FILE" ]; then
    echo -e "${RED}Error: No AI extraction files found${NC}"
    echo "Run: python scripts/analyze_narratives.py first"
    exit 1
fi

echo -e "${GREEN}Found extraction file: ${EXTRACTION_FILE}${NC}"
echo ""

echo -e "${BLUE}Step 1: Setting up Cloud Storage...${NC}"
if gsutil ls -b gs://${BUCKET_NAME} &> /dev/null; then
    echo "Bucket already exists: gs://${BUCKET_NAME}"
else
    echo "Creating bucket: gs://${BUCKET_NAME}"
    gsutil mb -p $PROJECT_ID -l $REGION gs://${BUCKET_NAME}
fi
echo ""

echo -e "${BLUE}Step 2: Uploading to Cloud Storage...${NC}"
GCS_PATH="gs://${BUCKET_NAME}/ai_extractions/$(basename $EXTRACTION_FILE)"
gsutil cp $EXTRACTION_FILE $GCS_PATH
echo -e "${GREEN}Uploaded to: ${GCS_PATH}${NC}"
echo ""

echo -e "${BLUE}Step 3: Setting up BigQuery dataset...${NC}"
if bq ls -d $DATASET &> /dev/null; then
    echo "Dataset already exists: ${DATASET}"
else
    echo "Creating dataset: ${DATASET}"
    bq mk --dataset --location=$REGION --description="Devpost hackathon data" ${PROJECT_ID}:${DATASET}
fi
echo ""

echo -e "${BLUE}Step 4: Creating table schema...${NC}"
cat > /tmp/ai_extractions_schema.json <<EOF
[
  {"name": "submission_url", "type": "STRING", "mode": "REQUIRED"},
  {"name": "project_title", "type": "STRING", "mode": "NULLABLE"},
  {"name": "hackathon", "type": "STRING", "mode": "NULLABLE"},
  {"name": "themes", "type": "STRING", "mode": "REPEATED"},
  {"name": "project_type", "type": "STRING", "mode": "NULLABLE"},
  {"name": "use_cases", "type": "STRING", "mode": "REPEATED"},
  {"name": "target_audience", "type": "STRING", "mode": "REPEATED"},
  {"name": "technologies_mentioned", "type": "STRING", "mode": "REPEATED"},
  {"name": "sentiment_score", "type": "FLOAT", "mode": "NULLABLE"},
  {"name": "enthusiasm_level", "type": "STRING", "mode": "NULLABLE"},
  {"name": "summary_200", "type": "STRING", "mode": "NULLABLE"},
  {"name": "key_innovation", "type": "STRING", "mode": "NULLABLE"},
  {"name": "problem_addressed", "type": "STRING", "mode": "NULLABLE"},
  {"name": "solution_approach", "type": "STRING", "mode": "NULLABLE"},
  {"name": "narrative_length", "type": "INTEGER", "mode": "NULLABLE"},
  {"name": "has_clear_problem", "type": "BOOLEAN", "mode": "NULLABLE"},
  {"name": "has_clear_solution", "type": "BOOLEAN", "mode": "NULLABLE"},
  {"name": "has_impact_metrics", "type": "BOOLEAN", "mode": "NULLABLE"},
  {"name": "contains_pii", "type": "BOOLEAN", "mode": "NULLABLE"},
  {"name": "processed_at", "type": "TIMESTAMP", "mode": "NULLABLE"},
  {"name": "model_version", "type": "STRING", "mode": "NULLABLE"}
]
EOF
echo "Schema created"
echo ""

echo -e "${BLUE}Step 5: Loading data into BigQuery...${NC}"
bq load \
  --source_format=NEWLINE_DELIMITED_JSON \
  --schema=/tmp/ai_extractions_schema.json \
  --replace \
  ${DATASET}.${TABLE} \
  $GCS_PATH

echo -e "${GREEN}✅ Data loaded successfully!${NC}"
echo ""

echo -e "${BLUE}Step 6: Verifying data...${NC}"
ROW_COUNT=$(bq query --use_legacy_sql=false --format=csv "SELECT COUNT(*) as count FROM \`${PROJECT_ID}.${DATASET}.${TABLE}\`" | tail -1)
echo -e "${GREEN}Total rows in BigQuery: ${ROW_COUNT}${NC}"
echo ""

echo -e "${BLUE}Step 7: Creating analysis views...${NC}"

bq query --use_legacy_sql=false <<EOF
CREATE OR REPLACE VIEW \`${PROJECT_ID}.${DATASET}.theme_summary\` AS
SELECT 
  theme,
  COUNT(*) as project_count,
  ROUND(AVG(sentiment_score), 2) as avg_sentiment,
  ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM \`${PROJECT_ID}.${DATASET}.${TABLE}\`), 2) as percentage
FROM \`${PROJECT_ID}.${DATASET}.${TABLE}\`,
UNNEST(themes) as theme
GROUP BY theme
ORDER BY project_count DESC;
EOF
echo "Created view: theme_summary"

bq query --use_legacy_sql=false <<EOF
CREATE OR REPLACE VIEW \`${PROJECT_ID}.${DATASET}.project_type_summary\` AS
SELECT 
  project_type,
  COUNT(*) as count,
  ROUND(AVG(sentiment_score), 2) as avg_sentiment,
  ROUND(AVG(narrative_length), 0) as avg_narrative_length,
  ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM \`${PROJECT_ID}.${DATASET}.${TABLE}\`), 2) as percentage
FROM \`${PROJECT_ID}.${DATASET}.${TABLE}\`
WHERE project_type IS NOT NULL
GROUP BY project_type
ORDER BY count DESC;
EOF
echo "Created view: project_type_summary"

bq query --use_legacy_sql=false <<EOF
CREATE OR REPLACE VIEW \`${PROJECT_ID}.${DATASET}.quality_metrics\` AS
SELECT 
  COUNTIF(has_clear_problem) as projects_with_clear_problem,
  COUNTIF(has_clear_solution) as projects_with_clear_solution,
  COUNTIF(has_impact_metrics) as projects_with_impact_metrics,
  COUNTIF(enthusiasm_level = 'high') as high_enthusiasm_projects,
  ROUND(AVG(sentiment_score), 2) as avg_sentiment,
  ROUND(AVG(narrative_length), 0) as avg_narrative_length,
  COUNT(*) as total_projects
FROM \`${PROJECT_ID}.${DATASET}.${TABLE}\`;
EOF
echo "Created view: quality_metrics"

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✅ Upload Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Next steps:"
echo "1. View your data in BigQuery Console:"
echo "   https://console.cloud.google.com/bigquery?project=${PROJECT_ID}"
echo ""
echo "2. Run sample queries:"
echo "   bq query --use_legacy_sql=false 'SELECT * FROM \`${PROJECT_ID}.${DATASET}.theme_summary\`'"
echo ""
echo "3. Explore views:"
echo "   - ${DATASET}.theme_summary"
echo "   - ${DATASET}.project_type_summary"
echo "   - ${DATASET}.quality_metrics"
echo ""
echo "4. See BIGQUERY_DEPLOYMENT.md for more analysis examples"
echo ""
