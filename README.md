# Hackathon Data Aggregation Tool

**Version:** 1.0  
**Phase:** 1 of 3  
**Date:** November 11, 2025

A web-based tool that ingests Excel files containing hackathon participation data and generates aggregated analytics reports with interactive visualizations.

## Deployment Options

This tool can be deployed in two ways:

- **[Local Deployment](#installation)** - Run on your local machine (instructions below)
- **[Google Cloud Run Deployment](CLOUD_DEPLOYMENT.md)** - Deploy to Google Cloud for remote access

For cloud deployment with Google Cloud Run, see the [Cloud Deployment Guide](CLOUD_DEPLOYMENT.md).

## Features

- **Data Ingestion**: Upload ZIP files or process local folders containing Excel files
- **Automatic Processing**: Header normalization, deduplication, and data cleaning
- **Interactive Dashboard**: View aggregated data with 8+ interactive charts
- **Hackathon Source of Truth**: Load hackathon metadata from Excel as authoritative source
- **Per-Hackathon Filtering**: Filter submissions and registrants by specific hackathon with validation
- **Per-Organizer Filtering**: Filter data by organizer with case-insensitive name matching
- **Timeline Analysis**: View time trends, year-over-year comparisons, and seasonal patterns
- **Data Validation**: Compare processed data against source participant/submission counts
- **Job History**: Track processing jobs and view detailed logs
- **Excel Export**: Generate comprehensive reports (submission, registrant, or combined)
- **Technology & Skills Normalization**: Automatic mapping of synonyms (js → javascript, etc.)

## System Requirements

### Minimum
- Python 3.10 or higher
- 8GB RAM
- 10GB free disk space
- Modern web browser (Chrome, Firefox, Safari, Edge)

### Recommended
- Python 3.10+
- 16GB RAM
- 20GB free disk space
- SSD storage

## Installation

### 1. Clone or Download the Project

```bash
cd hackathon-analysis
```

### 2. Create Virtual Environment

```bash
python3 -m venv venv
```

### 3. Activate Virtual Environment

**Linux/Mac:**
```bash
source venv/bin/activate
```

**Windows:**
```bash
venv\Scripts\activate
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Verify Installation

```bash
streamlit --version
```

## Quick Start

### 1. Start the Application

```bash
streamlit run streamlit_app.py
```

The application will open in your default web browser at `http://localhost:8501`

### 2. Upload Files

Navigate to the **Upload** page and either:
- Upload a ZIP file containing Excel files, or
- Place Excel files in `./incoming/submissions/` or `./incoming/registrants/` and process them

### 3. View Dashboard

Once processing is complete, navigate to the **Dashboard** page to view:
- Summary statistics
- Top technologies and skills
- Submissions by hackathon
- Team size distribution
- Country and occupation breakdowns
- Time trends

### 4. Filter by Hackathon or Organizer

Navigate to the **Hackathon Filter** page to:
- Filter data by specific hackathon with validation against source data
- Filter data by organizer (handles case-insensitive matching like "MHacks" and "mhacks")
- View data attribution showing where each piece of data comes from
- Export filtered data to Excel

### 5. Analyze Timeline Trends

Navigate to the **Timeline Analysis** page to:
- View hackathon activity over time (monthly, quarterly, yearly)
- Compare year-over-year metrics with growth percentages
- Identify seasonal patterns (which months are most popular)
- Track organizer evolution over time
- Filter hackathons by custom date ranges

### 6. Export Reports

Navigate to the **Export** page to generate and download Excel workbooks:
- **Submission Report**: Technologies, hackathons, team sizes, time trends
- **Registrant Report**: Skills, countries, occupations, work experience
- **Combined Report**: All data together

## Project Structure

```
hackathon-analysis/
├── app/
│   ├── __init__.py
│   ├── database.py          # SQLite job tracking
│   ├── utils.py             # Utility functions
│   ├── ingest.py            # Data ingestion and processing
│   ├── aggregate.py         # Aggregation queries
│   ├── visualize.py         # Chart generation
│   ├── export.py            # Excel export
│   ├── hackathon_source.py  # Hackathon source of truth management
│   ├── hackathon_filter.py  # Per-hackathon/organizer filtering
│   └── ui.py                # UI utilities and CSS injection
├── data/
│   ├── submissions/         # Processed submission data (Parquet)
│   ├── registrants/         # Processed registrant data (Parquet)
│   └── processed/           # Excel exports
├── incoming/
│   ├── submissions/         # Drop folder for submission files
│   └── registrants/         # Drop folder for registrant files
├── temp/                    # Temporary files
├── pages/
│   ├── 1_Upload.py          # Upload page
│   ├── 2_Dashboard.py       # Dashboard page
│   ├── 3_History.py         # History page
│   ├── 4_Export.py          # Export page
│   ├── 5_Hackathon_Filter.py # Hackathon/Organizer filtering
│   └── 6_Timeline_Analysis.py # Timeline & trend analysis
├── streamlit_app.py         # Main application (home page)
├── requirements.txt         # Python dependencies
├── synonyms.json            # Technology/skills normalization
├── .env.example             # Environment variables template
├── jobs.db                  # SQLite database (auto-created)
└── README.md                # This file
```

## Hackathon Source of Truth

The tool uses a hackathon source of truth Excel file (`hackathons_source.xlsx`) that contains authoritative metadata for all hackathons. This file should be placed in the `./data/` directory.

**Required Sheet:** `challenge_report_2022_10-2025-1`

**Required Columns:**
- Organization name
- Hackathon name
- Hackathon url
- Hackathon published date
- Total participant count
- Total valid submissions (excluding spam)
- In person vs virtual

**Features:**
- Validates processed data against source participant/submission counts
- Handles organizer name variations (case-insensitive matching)
- Provides date-based filtering and trend analysis
- Shows clear data attribution

**Note:** The source file is not included in the repository due to .gitignore. You must provide your own `hackathons_source.xlsx` file in the `./data/` directory for the filtering and timeline features to work.

## Data Specifications

### Submission Files

Expected columns:
- Organization Name
- Challenge Title
- Challenge Published At
- Project Title
- Submission Url (used for deduplication)
- Project Created At
- About The Project
- Built With (comma-separated technologies)
- Additional Team Member Count

### Registrant Files

Expected columns:
- Hackathon Name (used for deduplication)
- User ID (used for deduplication)
- Country
- Work Experience
- Skills (semicolon-separated)
- Occupation
- Specialty (Student / Professional / Post Grad)

**Note:** Headers may be in the first data row. The tool automatically normalizes them.

## Usage Guide

### Uploading Files

#### Method 1: ZIP File Upload
1. Navigate to the **Upload** page
2. Select "ZIP File Upload"
3. Click "Choose a ZIP file" and select your file
4. Click "Start Processing"
5. Monitor the progress bar

#### Method 2: Local Folder Processing
1. Place Excel files in `./incoming/submissions/` or `./incoming/registrants/`
2. Navigate to the **Upload** page
3. Select "Local Folder Processing"
4. Choose the folder type (Submissions or Registrants)
5. Click "Start Processing"

### Viewing Analytics

1. Navigate to the **Dashboard** page
2. View summary statistics at the top
3. Explore different tabs:
   - **Technologies & Skills**: Top technologies and skills used
   - **Hackathons & Teams**: Submissions by hackathon and team sizes
   - **Demographics**: Country, occupation, and specialty distributions
   - **Time Trends**: Submissions over time

### Filtering by Hackathon

1. Navigate to the **Hackathon Filter** page
2. Select the "Filter by Hackathon" tab
3. Choose a hackathon from the dropdown
4. View source data, validation results, and data attribution
5. (Optional) Export filtered data to Excel

### Filtering by Organizer

1. Navigate to the **Hackathon Filter** page
2. Select the "Filter by Organizer" tab
3. Choose an organizer from the dropdown
4. View all hackathons by that organizer with aggregated metrics
5. See name variations (e.g., "MHacks" and "mhacks" grouped together)
6. (Optional) Export filtered data to Excel

### Analyzing Timeline Trends

1. Navigate to the **Timeline Analysis** page
2. Explore different tabs:
   - **Time Trends**: View activity by month, quarter, or year
   - **Year-over-Year**: Compare metrics across years with growth rates
   - **Seasonal Patterns**: Identify peak months for hackathons
   - **Organizer Timeline**: Track specific organizer evolution
   - **Date Range Filter**: Filter by custom date range

### Exporting Data

1. Navigate to the **Export** page
2. Choose report type:
   - **Submission Report**: Submission-related data only
   - **Registrant Report**: Registrant-related data only
   - **Combined Report**: All data together
3. (Optional) Enter a custom filename
4. Click the appropriate "Generate Report" button
5. Click "Download" to download the report

### Viewing History

1. Navigate to the **History** page
2. View all processing jobs with their status
3. Filter by status, file type, or search by filename
4. Expand jobs to view details
5. Delete failed or old jobs as needed

## Configuration

### Environment Variables

Copy `.env.example` to `.env` and customize:

```bash
cp .env.example .env
```

Available settings:
- `DATA_DIR`: Directory for processed data (default: ./data)
- `INCOMING_DIR`: Directory for incoming files (default: ./incoming)
- `TEMP_DIR`: Directory for temporary files (default: ./temp)
- `DATABASE_PATH`: Path to SQLite database (default: ./jobs.db)
- `MAX_WORK_EXPERIENCE`: Maximum valid work experience years (default: 50)
- `BATCH_SIZE`: Processing batch size (default: 1000)
- `EXPORT_DIR`: Directory for exports (default: ./data/processed)

### Technology/Skills Normalization

Edit `synonyms.json` to add or modify technology and skills mappings:

```json
{
  "technologies": {
    "js": "javascript",
    "reactjs": "react",
    ...
  },
  "skills": {
    "ml": "machine learning",
    "ai": "artificial intelligence",
    ...
  }
}
```

## Performance

### Expected Processing Times

- **72 Excel files** (~576k rows): Under 10 minutes
- **Dashboard loading**: Under 3 seconds
- **Chart rendering**: Under 3 seconds
- **Excel export**: Under 30 seconds

### Optimization Tips

1. Use SSD storage for better I/O performance
2. Increase RAM for processing large files
3. Process files in batches if memory is limited
4. Close other applications during processing

## Troubleshooting

### Issue: "No module named 'streamlit'"

**Solution:** Ensure virtual environment is activated and dependencies are installed:
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### Issue: "Port 8501 is already in use"

**Solution:** Stop other Streamlit instances or use a different port:
```bash
streamlit run streamlit_app.py --server.port 8502
```

### Issue: "File processing failed"

**Possible causes:**
- Invalid Excel file format
- Corrupted file
- Missing required columns
- Malformed data

**Solution:** Check the error message in the History page and verify file format.

### Issue: "Out of memory"

**Solution:** 
- Process files in smaller batches
- Increase system RAM
- Close other applications

### Issue: "Charts not displaying"

**Solution:**
- Ensure data has been processed successfully
- Check browser console for JavaScript errors
- Try refreshing the page
- Clear browser cache

## Data Privacy & Security

- All data is processed and stored locally
- No data is sent to external servers
- SQLite database stores only metadata (file hashes, job status)
- Processed data is stored in Parquet format
- No authentication required (single-user application)

## Known Limitations

### Phase 1 Limitations

- No NLP analysis of project narratives (planned for Phase 2)
- No conversational querying interface (planned for Phase 3)
- No user authentication or multi-user support
- No cloud deployment (local only)
- No real-time data updates
- No API endpoints

### Data Limitations

- Work experience values > 50 years are filtered as outliers
- "Interests" field is skipped (99.6% empty in sample data)
- Duplicate detection based on file hash (exact matches only)

## Future Enhancements

### Phase 2 (Planned)
- NLP analysis of "About The Project" narratives
- Sentiment analysis
- Topic modeling
- Keyword extraction

### Phase 3 (Planned)
- Conversational querying interface
- Natural language questions
- AI-powered insights
- Recommendations

### Optional Enhancements
- Cloud deployment (AWS, GCP, Azure)
- User authentication
- Multi-user support
- Real-time data updates
- REST API
- Scheduled processing
- Email notifications

## Support

For issues, questions, or feature requests, please refer to the project documentation or contact the development team.

## License

This project is proprietary software. All rights reserved.

## Changelog

### Version 1.1 (November 11, 2025)
- Added hackathon source of truth management
- Added per-hackathon filtering with validation
- Added per-organizer filtering with name normalization
- Added timeline analysis with time trends, YoY comparison, seasonal patterns
- Added date-based filtering and trend analysis
- Added separate submission and registrant report generation
- Enhanced data validation against source participant/submission counts
- Added clear data attribution showing data sources

### Version 1.0 (November 10, 2025)
- Initial release
- Data ingestion and processing
- Interactive dashboard with 8+ charts
- Excel export functionality
- Job history tracking
- Technology and skills normalization

## Credits

**Developed by:** AI Development Team  
**Project Phase:** 1 of 3  
**Technology Stack:** Python, Streamlit, Pandas, DuckDB, Plotly, OpenPyXL
