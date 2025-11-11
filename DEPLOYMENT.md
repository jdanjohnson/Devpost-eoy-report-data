# Deployment Guide

## Docker Deployment

The application has been containerized with Docker for easy deployment to any Docker-compatible hosting platform.

#### Docker Image

A Docker image has been built and is ready for deployment:
- **Image Name**: `hackathon-analysis:latest`
- **Base Image**: `python:3.10-slim`
- **Exposed Port**: 8501

#### Running with Docker Locally

```bash
# Build the Docker image
docker build -t hackathon-analysis:latest .

# Run the container
docker run -d -p 8501:8501 \
  --name hackathon-analysis \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/incoming:/app/incoming \
  hackathon-analysis:latest

# View logs
docker logs hackathon-analysis

# Stop the container
docker stop hackathon-analysis

# Remove the container
docker rm hackathon-analysis
```

#### Deploying to Cloud Platforms

The Docker image can be deployed to various cloud platforms:

##### Option 1: Render

1. Push your code to GitHub
2. Create a new Web Service on Render
3. Select "Docker" as the environment
4. Configure:
   - **Docker Command**: (leave default)
   - **Port**: 8501
   - **Environment Variables**: Set DATA_DIR, TEMP_DIR, DATABASE_PATH as needed
5. Add a persistent disk mounted to `/app/data`
6. Deploy

##### Option 2: Fly.io

1. Install Fly CLI: `curl -L https://fly.io/install.sh | sh`
2. Login: `fly auth login`
3. Create app: `fly launch`
4. Configure fly.toml:
   ```toml
   [env]
     PORT = "8501"
   
   [[services]]
     internal_port = 8501
     protocol = "tcp"
   
   [mounts]
     source = "data_volume"
     destination = "/app/data"
   ```
5. Create volume: `fly volumes create data_volume --size 10`
6. Deploy: `fly deploy`

##### Option 3: Railway

1. Push your code to GitHub
2. Create a new project on Railway
3. Connect your GitHub repository
4. Railway will auto-detect the Dockerfile
5. Configure environment variables if needed
6. Deploy

##### Option 4: Streamlit Community Cloud

1. Push your code to a public GitHub repository
2. Go to https://share.streamlit.io/
3. Sign in with GitHub
4. Click "New app"
5. Select your repository, branch, and main file (streamlit_app.py)
6. Deploy

**Note**: Streamlit Community Cloud has limitations on upload size and persistent storage. For production use with large files, consider Render, Fly.io, or Railway.

### Environment Variables

The application supports the following environment variables for configuration:

- `DATA_DIR`: Directory for storing processed data (default: `./data`)
- `INCOMING_DIR`: Directory for incoming Excel files (default: `./incoming`)
- `TEMP_DIR`: Directory for temporary files (default: `./temp`)
- `DATABASE_PATH`: Path to SQLite database (default: `./jobs.db`)
- `EXPORT_DIR`: Directory for Excel exports (default: `./data/processed`)
- `MAX_WORK_EXPERIENCE`: Maximum work experience in years (default: `50`)

### Persistent Storage

For production deployments, ensure that the following directories are mounted to persistent storage:

- `/app/data` - Stores processed Parquet files and exports
- `/app/incoming` - Stores incoming Excel files
- `/app/temp` - Temporary file storage
- `/app/data/jobs.db` - SQLite database (or wherever DATABASE_PATH points)

Without persistent storage, all data will be lost when the container restarts.

### Security Considerations

1. **Authentication**: The current deployment does not include user authentication. For production use, consider adding authentication using Streamlit's built-in authentication or a reverse proxy.

2. **File Upload Size**: The application is configured to accept uploads up to 1GB. Adjust `server.maxUploadSize` in `.streamlit/config.toml` if needed.

3. **CORS**: CORS is enabled by default for security. Adjust `.streamlit/config.toml` if you need to change this.

4. **Zip Extraction**: The application extracts ZIP files. Ensure uploaded files are from trusted sources.

### Monitoring

To monitor the deployed application:

```bash
# View application logs
docker logs -f hackathon-analysis

# Check container status
docker ps | grep hackathon-analysis

# Check resource usage
docker stats hackathon-analysis
```

### Troubleshooting

#### Application Not Starting

1. Check logs: `docker logs hackathon-analysis`
2. Verify port 8501 is not already in use: `lsof -i :8501`
3. Ensure all required directories exist and have proper permissions

#### Upload Failures

1. Check available disk space: `df -h`
2. Verify upload size limits in `.streamlit/config.toml`
3. Check logs for specific error messages

#### Performance Issues

1. Monitor resource usage: `docker stats`
2. Consider increasing container memory limits
3. Check database size and consider cleanup of old jobs

### Scaling Considerations

For high-traffic deployments:

1. **Database**: Consider migrating from SQLite to PostgreSQL for better concurrent access
2. **File Storage**: Use cloud storage (S3, GCS) instead of local filesystem
3. **Caching**: Implement caching for aggregation queries
4. **Load Balancing**: Deploy multiple instances behind a load balancer

### Backup and Recovery

To backup your data:

```bash
# Backup data directory
tar -czf backup-$(date +%Y%m%d).tar.gz data/

# Backup database
cp data/jobs.db data/jobs.db.backup
```

To restore:

```bash
# Restore data directory
tar -xzf backup-YYYYMMDD.tar.gz

# Restore database
cp data/jobs.db.backup data/jobs.db
```

### Updating the Application

To update the deployed application:

```bash
# Pull latest code
git pull

# Rebuild Docker image
docker build -t hackathon-analysis:latest .

# Stop and remove old container
docker stop hackathon-analysis
docker rm hackathon-analysis

# Start new container
docker run -d -p 8501:8501 \
  --name hackathon-analysis \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/incoming:/app/incoming \
  hackathon-analysis:latest
```

### Support

For issues or questions about deployment, refer to:
- Streamlit Documentation: https://docs.streamlit.io/
- Docker Documentation: https://docs.docker.com/
- Project README: README.md
