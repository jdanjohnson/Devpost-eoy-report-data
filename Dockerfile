FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/data/submissions /app/data/registrants /app/data/processed \
    /app/incoming/submissions /app/incoming/registrants /app/temp

ENV DATA_DIR=/app/data
ENV INCOMING_DIR=/app/incoming
ENV TEMP_DIR=/app/temp
ENV DATABASE_PATH=/app/data/jobs.db
ENV EXPORT_DIR=/app/data/processed

EXPOSE 8501

HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

CMD ["streamlit", "run", "streamlit_app.py", "--server.address=0.0.0.0", "--server.port=8501", "--server.headless=true"]
