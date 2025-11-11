# Hackathon Data Aggregation Tool

**Version:** 1.0  
**Phase:** 1 of 3  
**Date:** November 10, 2025

A web-based tool that ingests Excel files containing hackathon participation data and generates aggregated analytics reports with interactive visualizations.

## Features

- **Data Ingestion**: Upload ZIP files or process local folders containing Excel files
- **Automatic Processing**: Header normalization, deduplication, and data cleaning
- **Interactive Dashboard**: View aggregated data with 8+ interactive charts
- **Job History**: Track processing jobs and view detailed logs
- **Excel Export**: Generate comprehensive reports with multiple sheets
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

### 4. Export Reports

Navigate to the **Export** page to generate and download Excel workbooks with all aggregations.

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
│   └── export.py            # Excel export
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
│   └── 4_Export.py          # Export page
├── streamlit_app.py         # Main application (home page)
├── requirements.txt         # Python dependencies
├── synonyms.json            # Technology/skills normalization
├── .env.example             # Environment variables template
├── jobs.db                  # SQLite database (auto-created)
└── README.md                # This file
```

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

### Exporting Data

1. Navigate to the **Export** page
2. (Optional) Enter a custom filename
3. Click "Generate Export"
4. Click "Download Excel File" to download the report
5. View export history and download previous exports

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
