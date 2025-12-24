#!/bin/bash
#
#

set -e  # Exit on error

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_header() {
    echo -e "\n${BLUE}============================================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}============================================================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}


print_header "Step 1: Configuration"

if ! command -v gcloud &> /dev/null; then
    print_error "gcloud CLI not found. Please install: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

print_success "gcloud CLI found"

CURRENT_PROJECT=$(gcloud config get-value project 2>/dev/null)

if [ -z "$CURRENT_PROJECT" ]; then
    print_error "No GCP project configured. Run: gcloud config set project PROJECT_ID"
    exit 1
fi

print_info "Current project: $CURRENT_PROJECT"
read -p "Use this project? (y/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    read -p "Enter GCP project ID: " PROJECT_ID
    gcloud config set project $PROJECT_ID
else
    PROJECT_ID=$CURRENT_PROJECT
fi

REGION="us-central1"
print_info "Using region: $REGION"
read -p "Use this region? (y/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    read -p "Enter region: " REGION
fi

BUCKET_NAME="${PROJECT_ID}-devpost-data"
print_info "Bucket name: gs://$BUCKET_NAME"

DATASET_NAME="devpost_ai"
print_info "BigQuery dataset: $DATASET_NAME"

print_success "Configuration complete"


print_header "Step 2: Enable Required APIs"

print_info "Enabling BigQuery API..."
gcloud services enable bigquery.googleapis.com --quiet

print_info "Enabling Vertex AI API..."
gcloud services enable aiplatform.googleapis.com --quiet

print_info "Enabling Cloud Storage API..."
gcloud services enable storage.googleapis.com --quiet

print_success "All APIs enabled"


print_header "Step 3: Create Cloud Storage Bucket"

if gsutil ls -b gs://$BUCKET_NAME &> /dev/null; then
    print_warning "Bucket gs://$BUCKET_NAME already exists"
else
    print_info "Creating bucket gs://$BUCKET_NAME..."
    gsutil mb -l $REGION gs://$BUCKET_NAME
    print_success "Bucket created"
fi


print_header "Step 4: Create BigQuery Dataset"

if bq ls -d $PROJECT_ID:$DATASET_NAME &> /dev/null; then
    print_warning "Dataset $DATASET_NAME already exists"
else
    print_info "Creating dataset $DATASET_NAME..."
    bq mk --dataset --location=$REGION --description="AI-powered analysis of hackathon narratives" $PROJECT_ID:$DATASET_NAME
    print_success "Dataset created"
fi


print_header "Step 5: Create Vertex AI Connection"

print_info "Creating Vertex AI connection..."
print_warning "This step must be done in BigQuery Console due to API limitations"
print_info "Please follow these steps:"
echo ""
echo "1. Open BigQuery Console: https://console.cloud.google.com/bigquery?project=$PROJECT_ID"
echo "2. Click the '+' button to create a new query"
echo "3. Run this SQL:"
echo ""
echo "CREATE OR REPLACE CONNECTION \`$REGION.vertex_ai_connection\`"
echo "LOCATION '$REGION'"
echo "OPTIONS (connection_type = 'CLOUD_RESOURCE');"
echo ""
read -p "Press Enter after creating the connection..."


print_header "Step 6: Grant Permissions to Connection Service Account"

print_info "Getting service account from connection..."
print_warning "Please get the service account email from BigQuery Console:"
echo ""
echo "1. Go to: https://console.cloud.google.com/bigquery/connections?project=$PROJECT_ID"
echo "2. Click on 'vertex_ai_connection'"
echo "3. Copy the service account email (format: bqcx-xxx@gcp-sa-bigquery-condel.iam.gserviceaccount.com)"
echo ""
read -p "Enter service account email: " SERVICE_ACCOUNT

if [ -z "$SERVICE_ACCOUNT" ]; then
    print_error "Service account email is required"
    exit 1
fi

print_info "Granting Vertex AI User role to $SERVICE_ACCOUNT..."
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT" \
    --role="roles/aiplatform.user" \
    --quiet

print_success "Permissions granted"


print_header "Step 7: Create Remote Model for Gemini"

print_info "Creating remote model..."
print_warning "This step must be done in BigQuery Console"
print_info "Please run this SQL in BigQuery Console:"
echo ""
echo "CREATE OR REPLACE MODEL \`$DATASET_NAME.gemini_flash\`"
echo "REMOTE WITH CONNECTION \`$REGION.vertex_ai_connection\`"
echo "OPTIONS (endpoint = 'gemini-1.5-flash');"
echo ""
read -p "Press Enter after creating the model..."


print_header "Step 8: Create BigQuery Tables"

print_info "Running SQL scripts to create tables..."

bq query --use_legacy_sql=false --project_id=$PROJECT_ID <<EOF
CREATE TABLE IF NOT EXISTS \`$DATASET_NAME.prompt_versions\` (
  prompt_version STRING NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
  description STRING,
  system_instruction STRING,
  temperature FLOAT64 DEFAULT 0.1,
  max_output_tokens INT64 DEFAULT 1024,
  is_active BOOL DEFAULT FALSE,
  notes STRING
);
EOF

print_success "prompt_versions table created"

bq query --use_legacy_sql=false --project_id=$PROJECT_ID <<EOF
CREATE TABLE IF NOT EXISTS \`$DATASET_NAME.submissions\` (
  submission_url STRING,
  project_title STRING,
  tagline STRING,
  challenge_title STRING,
  built_with STRING,
  about_the_project STRING,
  video_url STRING,
  website_url STRING,
  file_url STRING,
  try_it_out_url STRING,
  submission_gallery_url STRING,
  submitted_at TIMESTAMP,
  updated_at TIMESTAMP,
  like_count INT64,
  comment_count INT64,
  winner BOOL,
  content_hash STRING,
  loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
);
EOF

print_success "submissions table created"

bq query --use_legacy_sql=false --project_id=$PROJECT_ID <<EOF
CREATE TABLE IF NOT EXISTS \`$DATASET_NAME.ai_extractions_raw\` (
  extraction_id STRING DEFAULT GENERATE_UUID(),
  submission_url STRING,
  project_title STRING,
  challenge_title STRING,
  content_hash STRING,
  prompt_version STRING,
  model_name STRING DEFAULT 'gemini-1.5-flash',
  raw_json STRING,
  processing_status STRING DEFAULT 'pending',
  error_message STRING,
  processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
);
EOF

print_success "ai_extractions_raw table created"

bq query --use_legacy_sql=false --project_id=$PROJECT_ID <<EOF
CREATE TABLE IF NOT EXISTS \`$DATASET_NAME.ai_extractions\` (
  extraction_id STRING,
  submission_url STRING,
  project_title STRING,
  challenge_title STRING,
  content_hash STRING,
  themes ARRAY<STRING>,
  theme_confidence FLOAT64,
  project_type STRING,
  use_cases ARRAY<STRING>,
  target_audience ARRAY<STRING>,
  technologies_mentioned ARRAY<STRING>,
  sentiment_score FLOAT64,
  enthusiasm_level STRING,
  summary_200 STRING,
  key_innovation STRING,
  problem_addressed STRING,
  solution_approach STRING,
  narrative_length INT64,
  has_clear_problem BOOL,
  has_clear_solution BOOL,
  has_impact_metrics BOOL,
  contains_pii BOOL,
  prompt_version STRING,
  model_name STRING,
  processed_at TIMESTAMP
);
EOF

print_success "ai_extractions table created"

bq query --use_legacy_sql=false --project_id=$PROJECT_ID <<EOF
CREATE TABLE IF NOT EXISTS \`$DATASET_NAME.ai_extractions_failed\` (
  extraction_id STRING,
  submission_url STRING,
  project_title STRING,
  content_hash STRING,
  raw_json STRING,
  error_message STRING,
  failed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
  retry_count INT64 DEFAULT 0
);
EOF

print_success "ai_extractions_failed table created"


print_header "Step 9: Load Submission Data"

print_info "Looking for Parquet files to upload..."

if [ ! -d "data/submissions" ]; then
    mkdir -p data/submissions
    print_warning "data/submissions directory created"
fi

PARQUET_FILES=$(find data/submissions -name "*.parquet" 2>/dev/null | head -1)

if [ -z "$PARQUET_FILES" ]; then
    print_warning "No Parquet files found in data/submissions/"
    print_info "Please export data from Streamlit app:"
    echo "  1. Run: streamlit run streamlit_app.py"
    echo "  2. Go to Export page"
    echo "  3. Under 'Raw Data Exports', select Parquet format"
    echo "  4. Save to data/submissions/"
    echo ""
    read -p "Enter path to Parquet file (or press Enter to skip): " PARQUET_PATH
    
    if [ -z "$PARQUET_PATH" ]; then
        print_warning "Skipping data load. You can load data later with:"
        echo "  gsutil cp your_file.parquet gs://$BUCKET_NAME/raw/submissions/"
        echo "  bq load --source_format=PARQUET $DATASET_NAME.submissions gs://$BUCKET_NAME/raw/submissions/*.parquet"
    else
        PARQUET_FILES=$PARQUET_PATH
    fi
fi

if [ ! -z "$PARQUET_FILES" ]; then
    print_info "Uploading $PARQUET_FILES to Cloud Storage..."
    gsutil cp $PARQUET_FILES gs://$BUCKET_NAME/raw/submissions/
    
    print_info "Loading data into BigQuery..."
    bq load --source_format=PARQUET --replace \
        $DATASET_NAME.submissions \
        gs://$BUCKET_NAME/raw/submissions/*.parquet
    
    print_success "Data loaded successfully"
    
    print_info "Adding content hash for deduplication..."
    bq query --use_legacy_sql=false --project_id=$PROJECT_ID <<EOF
UPDATE \`$DATASET_NAME.submissions\`
SET content_hash = TO_HEX(SHA256(CAST(about_the_project AS BYTES)))
WHERE content_hash IS NULL AND about_the_project IS NOT NULL;
EOF
    
    print_success "Content hash added"
fi


print_header "Step 10: Create Analysis Views"

print_info "Creating submissions_to_process view..."
bq query --use_legacy_sql=false --project_id=$PROJECT_ID <<EOF
CREATE OR REPLACE VIEW \`$DATASET_NAME.submissions_to_process\` AS
SELECT
  submission_url,
  project_title,
  challenge_title,
  built_with,
  about_the_project,
  content_hash,
  CHAR_LENGTH(about_the_project) AS narrative_length,
  submitted_at
FROM \`$DATASET_NAME.submissions\`
WHERE about_the_project IS NOT NULL
  AND CHAR_LENGTH(TRIM(about_the_project)) >= 10
  AND content_hash NOT IN (
    SELECT DISTINCT content_hash
    FROM \`$DATASET_NAME.ai_extractions_raw\`
    WHERE content_hash IS NOT NULL
  );
EOF

print_success "submissions_to_process view created"


print_header "Deployment Complete!"

print_success "Infrastructure setup complete"
echo ""
print_info "Summary:"
echo "  • Project: $PROJECT_ID"
echo "  • Region: $REGION"
echo "  • Dataset: $DATASET_NAME"
echo "  • Bucket: gs://$BUCKET_NAME"
echo ""
print_info "Next Steps:"
echo "  1. Review the setup in BigQuery Console"
echo "  2. Test extraction with a small batch (see sql/03_extract_narratives.sql)"
echo "  3. Scale to full dataset"
echo "  4. Create analysis views (see sql/04_analyze_results.sql)"
echo ""
print_info "Documentation:"
echo "  • Full guide: VERTEX_AI_DEPLOYMENT.md"
echo "  • SQL scripts: sql/*.sql"
echo ""
print_success "Ready to process narratives!"
