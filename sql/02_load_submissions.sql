--
--

DECLARE PROJECT_ID STRING DEFAULT 'your-project-id';
DECLARE BUCKET_NAME STRING DEFAULT 'your-bucket-name';


CREATE OR REPLACE TABLE `devpost_ai.submissions` (
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


LOAD DATA OVERWRITE `devpost_ai.submissions`
FROM FILES (
  format = 'PARQUET',
  uris = ['gs://YOUR_BUCKET/raw/submissions_*.parquet']
);



UPDATE `devpost_ai.submissions`
SET content_hash = TO_HEX(SHA256(CAST(about_the_project AS BYTES)))
WHERE content_hash IS NULL
  AND about_the_project IS NOT NULL;


CREATE OR REPLACE VIEW `devpost_ai.submissions_to_process` AS
SELECT
  submission_url,
  project_title,
  challenge_title,
  built_with,
  about_the_project,
  content_hash,
  CHAR_LENGTH(about_the_project) AS narrative_length,
  submitted_at
FROM `devpost_ai.submissions`
WHERE about_the_project IS NOT NULL
  AND CHAR_LENGTH(TRIM(about_the_project)) >= 10
  AND content_hash NOT IN (
    SELECT DISTINCT content_hash
    FROM `devpost_ai.ai_extractions_raw`
    WHERE content_hash IS NOT NULL
  );


CREATE OR REPLACE TABLE `devpost_ai.ai_extractions_raw` (
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
  processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
  PRIMARY KEY (extraction_id) NOT ENFORCED
);

CREATE OR REPLACE TABLE `devpost_ai.ai_extractions` (
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
  processed_at TIMESTAMP,
  
  PRIMARY KEY (extraction_id) NOT ENFORCED
);

CREATE OR REPLACE TABLE `devpost_ai.ai_extractions_failed` (
  extraction_id STRING,
  submission_url STRING,
  project_title STRING,
  content_hash STRING,
  raw_json STRING,
  error_message STRING,
  failed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
  retry_count INT64 DEFAULT 0
);


SELECT
  COUNT(*) AS total_submissions,
  COUNT(DISTINCT challenge_title) AS unique_hackathons,
  COUNT(DISTINCT content_hash) AS unique_narratives,
  MIN(submitted_at) AS earliest_submission,
  MAX(submitted_at) AS latest_submission
FROM `devpost_ai.submissions`;

SELECT
  COUNT(*) AS narratives_to_process,
  AVG(narrative_length) AS avg_length,
  MIN(narrative_length) AS min_length,
  MAX(narrative_length) AS max_length
FROM `devpost_ai.submissions_to_process`;

SELECT
  table_name,
  ddl
FROM `devpost_ai.INFORMATION_SCHEMA.TABLES`
WHERE table_name IN ('submissions', 'ai_extractions_raw', 'ai_extractions', 'ai_extractions_failed');
