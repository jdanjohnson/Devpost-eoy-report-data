# Google Cloud Run Deployment Guide

## Overview for Internal Review

### What We're Doing

We're deploying the Hackathon Data Aggregation Tool as a private, single-user web application to analyze 72 Excel files containing hackathon participation data (~73,000 total records). The tool processes submission and registrant data to generate aggregated statistics, interactive visualizations, and exportable reports for annual data analysis.

**Key Capabilities:**
- Process 36 submission files + 36 registrant files
- Automatic data cleaning, deduplication, and normalization
- Generate 8+ interactive analytics dashboards (technologies, skills, demographics, trends)
- Export comprehensive Excel reports with multiple sheets
- Track processing jobs and history

### How It Works

**Data Processing Flow:**

1. **Upload** → User uploads Excel files via web interface or places files in mounted storage
2. **Ingestion** → System reads Excel files, normalizes malformed headers, validates schema
3. **Deduplication** → Computes unique keys (Submission URL for submissions, Hackathon Name + User ID for registrants)
4. **Normalization** → Applies 230+ technology/skills synonym mappings (js→javascript, react.js→react)
5. **Storage** → Writes to Parquet columnar format for fast querying
6. **Analysis** → Runs SQL aggregations via DuckDB, generates Plotly visualizations
7. **Export** → Creates multi-sheet Excel workbooks with formatted results

**Processing Time:** ~5 minutes for all 72 files (~73,000 rows)

### Data Sharing & Privacy

**Who Has Access:**
- **Single User Only** - This is a private deployment for individual use
- **No External Sharing** - Data never leaves your Google Cloud environment
- **No Third-Party APIs** - Phase 1 uses only local processing (no AI/NLP APIs)

**Data Storage:**
- **Cloud Deployment:** Data stored in Google Cloud Storage buckets (private, encrypted at rest)
- **Database:** SQLite for job tracking (stored with application data)

**Data Retention:**
- Processed Parquet files persist until manually deleted
- Job history retained in SQLite database
- Exported Excel reports stored in designated output directory

## Technical Architecture

### Cloud Deployment Architecture

```
User Browser
    ↓ HTTPS
Google Cloud Run (Streamlit Container)
    ↓
Google Cloud Storage (Persistent Data)
    ├─ /data/submissions/*.parquet
    ├─ /data/registrants/*.parquet
    ├─ /data/processed/*.xlsx
    └─ jobs.db
```

**Components:**
- **Compute:** Cloud Run (serverless containers, auto-scaling)
- **Storage:** Cloud Storage bucket mounted via Cloud Storage FUSE
- **Database:** SQLite (stored in Cloud Storage bucket)
- **Container:** Docker image with Streamlit + Python dependencies
- **Networking:** Private Cloud Run service (requires authentication)

**Data Flow:**
1. User uploads Excel files through browser → Cloud Run instance
2. Cloud Run processes files → Writes Parquet to Cloud Storage
3. User requests dashboard → Cloud Run queries Parquet from Cloud Storage
4. User exports report → Cloud Run generates Excel → Stores in Cloud Storage → Downloads to browser

**Key Features:**
- ✅ Accessible from anywhere (not just local machine)
- ✅ Automatic backups via Cloud Storage versioning
- ✅ No local storage requirements
- ✅ Automatic container restarts on failure
- ⚠️ Requires Google Cloud account and billing
- ⚠️ Data stored in Google Cloud (not local filesystem)
- ⚠️ Cold start latency (~10-30 seconds if idle)

## Deployment Steps

### Prerequisites

1. **Google Cloud Account** with billing enabled
2. **gcloud CLI** installed and authenticated
3. **Docker** installed (for building container images)
4. **Project Setup:**
   ```bash
   # Set your project ID
   export PROJECT_ID="your-project-id"
   export REGION="us-central1"
   export SERVICE_NAME="hackathon-analysis"
   
   # Enable required APIs
   gcloud services enable run.googleapis.com
   gcloud services enable storage.googleapis.com
   gcloud services enable artifactregistry.googleapis.com
   ```

### Step 1: Create Cloud Storage Bucket for Persistent Data

```bash
# Create bucket for data storage
gsutil mb -p $PROJECT_ID -l $REGION gs://${PROJECT_ID}-hackathon-data

# Create directory structure
gsutil -m cp /dev/null gs://${PROJECT_ID}-hackathon-data/data/submissions/.keep
gsutil -m cp /dev/null gs://${PROJECT_ID}-hackathon-data/data/registrants/.keep
gsutil -m cp /dev/null gs://${PROJECT_ID}-hackathon-data/data/processed/.keep
gsutil -m cp /dev/null gs://${PROJECT_ID}-hackathon-data/incoming/submissions/.keep
gsutil -m cp /dev/null gs://${PROJECT_ID}-hackathon-data/incoming/registrants/.keep
gsutil -m cp /dev/null gs://${PROJECT_ID}-hackathon-data/temp/.keep

# Set lifecycle policy to auto-delete temp files after 7 days
cat > lifecycle.json <<EOF
{
  "lifecycle": {
    "rule": [
      {
        "action": {"type": "Delete"},
        "condition": {
          "age": 7,
          "matchesPrefix": ["temp/"]
        }
      }
    ]
  }
}
EOF
gsutil lifecycle set lifecycle.json gs://${PROJECT_ID}-hackathon-data
```

### Step 2: Build and Push Docker Image

```bash
# Create Artifact Registry repository
gcloud artifacts repositories create hackathon-analysis \
    --repository-format=docker \
    --location=$REGION \
    --description="Hackathon Analysis Tool"

# Configure Docker authentication
gcloud auth configure-docker ${REGION}-docker.pkg.dev

# Build and push image
docker build -t ${REGION}-docker.pkg.dev/${PROJECT_ID}/hackathon-analysis/app:latest .
docker push ${REGION}-docker.pkg.dev/${PROJECT_ID}/hackathon-analysis/app:latest
```

### Step 3: Deploy to Cloud Run with Cloud Storage Mount

```bash
# Deploy Cloud Run service with Cloud Storage bucket mounted
gcloud run deploy $SERVICE_NAME \
    --image ${REGION}-docker.pkg.dev/${PROJECT_ID}/hackathon-analysis/app:latest \
    --platform managed \
    --region $REGION \
    --memory 2Gi \
    --cpu 2 \
    --timeout 3600 \
    --max-instances 1 \
    --min-instances 0 \
    --execution-environment gen2 \
    --add-volume name=data,type=cloud-storage,bucket=${PROJECT_ID}-hackathon-data \
    --add-volume-mount volume=data,mount-path=/app/data \
    --set-env-vars DATA_DIR=/app/data/data \
    --set-env-vars INCOMING_DIR=/app/data/incoming \
    --set-env-vars TEMP_DIR=/app/data/temp \
    --set-env-vars DATABASE_PATH=/app/data/jobs.db \
    --set-env-vars EXPORT_DIR=/app/data/data/processed \
    --no-allow-unauthenticated

# Get service URL
gcloud run services describe $SERVICE_NAME --region $REGION --format 'value(status.url)'
```

### Step 4: Configure Authentication

Since this is a private, single-user deployment, we'll use IAM authentication:

```bash
# Get your email
export USER_EMAIL=$(gcloud config get-value account)

# Grant yourself access to invoke the service
gcloud run services add-iam-policy-binding $SERVICE_NAME \
    --region=$REGION \
    --member="user:${USER_EMAIL}" \
    --role="roles/run.invoker"
```

### Step 5: Access the Application

**Option A: Using gcloud proxy (Recommended)**
```bash
# Start proxy on localhost:8080
gcloud run services proxy $SERVICE_NAME --region=$REGION --port=8080

# Open browser to http://localhost:8080
```

**Option B: Direct access with authentication**
```bash
# Get service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region $REGION --format 'value(status.url)')

# Generate auth token
AUTH_TOKEN=$(gcloud auth print-identity-token)

# Access with curl (for testing)
curl -H "Authorization: Bearer $AUTH_TOKEN" $SERVICE_URL
```

## Data Processing Workflow

### Upload Process
1. User uploads Excel files via Streamlit web interface
2. Files temporarily stored in Cloud Run container memory
3. Streamlit processes files:
   - Reads Excel with pandas/openpyxl
   - Normalizes headers and validates schema
   - Computes deduplication keys
   - Writes Parquet files to Cloud Storage bucket (via mounted volume)
   - Logs job status to SQLite database (in Cloud Storage)
4. Temporary files cleaned up from container memory

### Analysis Process
1. User navigates to Dashboard page
2. Streamlit queries Parquet files from Cloud Storage
3. DuckDB runs SQL aggregations in-memory
4. Plotly generates interactive visualizations
5. Results rendered in browser

### Export Process
1. User clicks "Generate Export" button
2. Streamlit runs all aggregation queries
3. Creates multi-sheet Excel workbook in memory
4. Writes to Cloud Storage bucket (/data/processed/)
5. Provides download link to user
6. File downloaded directly from Cloud Storage to user's browser

## Cost Estimation

### Cloud Run Costs (us-central1 pricing)
- **CPU:** $0.00002400 per vCPU-second
- **Memory:** $0.00000250 per GiB-second
- **Requests:** $0.40 per million requests

### Example Usage (Monthly)
- 20 processing sessions per month
- 5 minutes per session = 100 minutes total
- 2 vCPU, 2 GiB memory

### Calculation
- CPU: 100 min × 60 sec × 2 vCPU × $0.000024 = $0.29
- Memory: 100 min × 60 sec × 2 GiB × $0.0000025 = $0.03
- Requests: ~100 requests × $0.40/1M = $0.00
- **Total Cloud Run: ~$0.32/month**

### Cloud Storage Costs
- Storage: ~500 MB × $0.020/GB = $0.01/month
- Operations: Negligible for single-user use
- **Total Storage: ~$0.01/month**

### Total Estimated Cost
**~$0.33/month** (with minimal usage)

### Free Tier
- Cloud Run: 2 million requests, 360,000 GiB-seconds, 180,000 vCPU-seconds per month
- Cloud Storage: 5 GB storage, 5,000 Class A operations, 50,000 Class B operations per month
- **This deployment likely stays within free tier limits**

## Monitoring and Maintenance

### View Logs
```bash
# Stream logs
gcloud run services logs tail $SERVICE_NAME --region=$REGION

# View recent logs
gcloud run services logs read $SERVICE_NAME --region=$REGION --limit=50
```

### Check Service Status
```bash
gcloud run services describe $SERVICE_NAME --region=$REGION
```

### Update Deployment
```bash
# Rebuild and push new image
docker build -t ${REGION}-docker.pkg.dev/${PROJECT_ID}/hackathon-analysis/app:latest .
docker push ${REGION}-docker.pkg.dev/${PROJECT_ID}/hackathon-analysis/app:latest

# Deploy new version
gcloud run services update $SERVICE_NAME \
    --image ${REGION}-docker.pkg.dev/${PROJECT_ID}/hackathon-analysis/app:latest \
    --region $REGION
```

### Backup Data
```bash
# Download all processed data
gsutil -m cp -r gs://${PROJECT_ID}-hackathon-data/data ./backup-$(date +%Y%m%d)

# Download database
gsutil cp gs://${PROJECT_ID}-hackathon-data/jobs.db ./backup-$(date +%Y%m%d)/
```

## Security Considerations

### Authentication & Access Control
- ✅ **IAM Authentication:** Cloud Run service requires Google Cloud IAM authentication
- ✅ **No Public Access:** Service is not publicly accessible (--no-allow-unauthenticated)
- ✅ **Single User:** Only authorized Google account can access service
- ⚠️ **No Multi-User Support:** Not designed for team access (single instance, no user management)

### Data Security
- **Data at Rest:** Encrypted at rest in Cloud Storage (Google-managed encryption keys)
- **Data in Transit:** All traffic encrypted via HTTPS (Cloud Run enforces TLS)
- **Data Isolation:** Data stored in private Cloud Storage bucket (not shared with other projects)

### Input Validation
- ✅ **File Type Validation:** Only .xlsx files accepted
- ✅ **File Size Limits:** Max 1GB upload size (configurable)
- ✅ **Schema Validation:** Validates Excel column structure before processing
- ✅ **SQL Injection Protection:** Uses parameterized queries for all database operations

### Recommended Security Improvements
1. ⚠️ **Add Zip Slip Protection:** Sanitize ZIP member paths before extraction
2. ⚠️ **Add Rate Limiting:** Prevent abuse of upload endpoint
3. ⚠️ **Add Audit Logging:** Log all file uploads and exports for compliance
4. ⚠️ **Regular Dependency Updates:** Monitor and update Python packages

### For Production Use
1. Enable VPC Service Controls for Cloud Run
2. Implement Cloud Armor for DDoS protection
3. Add Cloud Logging and Monitoring alerts
4. Set up automated backups of Cloud Storage bucket
5. Implement data retention policies (auto-delete after X days)

## Troubleshooting

### Service Won't Start
```bash
# Check logs for errors
gcloud run services logs read $SERVICE_NAME --region=$REGION --limit=100

# Verify image exists
gcloud artifacts docker images list ${REGION}-docker.pkg.dev/${PROJECT_ID}/hackathon-analysis
```

### Can't Access Service
```bash
# Verify IAM permissions
gcloud run services get-iam-policy $SERVICE_NAME --region=$REGION

# Test with curl
AUTH_TOKEN=$(gcloud auth print-identity-token)
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region $REGION --format 'value(status.url)')
curl -H "Authorization: Bearer $AUTH_TOKEN" $SERVICE_URL
```

### Upload Fails
- Check Cloud Storage bucket permissions
- Verify bucket is mounted correctly in Cloud Run
- Check Cloud Run logs for specific errors

### Slow Performance
- Increase memory/CPU allocation in Cloud Run
- Check Cloud Storage bucket location (should match Cloud Run region)
- Monitor Cloud Run metrics in Google Cloud Console
