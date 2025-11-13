--
--


WITH test_narrative AS (
  SELECT
    submission_url,
    project_title,
    challenge_title,
    built_with,
    about_the_project,
    content_hash
  FROM `devpost_ai.submissions_to_process`
  LIMIT 1
),
test_prompt AS (
  SELECT
    t.*,
    CONCAT(
      'Project: ', project_title, '\n',
      'Hackathon: ', challenge_title, '\n',
      'Technologies: ', COALESCE(built_with, 'Not specified'), '\n',
      'Narrative: ', about_the_project
    ) AS prompt
  FROM test_narrative t
)
SELECT
  submission_url,
  project_title,
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


DECLARE prompt_version STRING;
DECLARE system_instruction STRING;
DECLARE temperature FLOAT64;
DECLARE max_tokens INT64;

SET (prompt_version, system_instruction, temperature, max_tokens) = (
  SELECT AS STRUCT
    prompt_version,
    system_instruction,
    temperature,
    max_output_tokens
  FROM `devpost_ai.prompt_versions`
  WHERE is_active = TRUE
  LIMIT 1
);

INSERT INTO `devpost_ai.ai_extractions_raw` (
  submission_url,
  project_title,
  challenge_title,
  content_hash,
  prompt_version,
  model_name,
  raw_json,
  processing_status,
  error_message
)
WITH batch_to_process AS (
  SELECT
    submission_url,
    project_title,
    challenge_title,
    built_with,
    about_the_project,
    content_hash
  FROM `devpost_ai.submissions_to_process`
  LIMIT 25
),
prompts AS (
  SELECT
    submission_url,
    project_title,
    challenge_title,
    content_hash,
    CONCAT(
      'Project: ', project_title, '\n',
      'Hackathon: ', challenge_title, '\n',
      'Technologies: ', COALESCE(built_with, 'Not specified'), '\n',
      'Narrative: ', about_the_project
    ) AS prompt
  FROM batch_to_process
),
responses AS (
  SELECT
    p.submission_url,
    p.project_title,
    p.challenge_title,
    p.content_hash,
    r.ml_generate_text_llm_result AS raw_json,
    r.ml_generate_text_status AS status
  FROM prompts p
  CROSS JOIN
    ML.GENERATE_TEXT(
      MODEL `devpost_ai.gemini_flash`,
      (SELECT prompt FROM prompts WHERE submission_url = p.submission_url),
      STRUCT(
        0.1 AS temperature,
        1024 AS max_output_tokens,
        TRUE AS flatten_json_output
      )
    ) r
)
SELECT
  submission_url,
  project_title,
  challenge_title,
  content_hash,
  prompt_version AS prompt_version,
  'gemini-1.5-flash' AS model_name,
  raw_json,
  CASE
    WHEN status = 'success' THEN 'completed'
    ELSE 'failed'
  END AS processing_status,
  CASE
    WHEN status != 'success' THEN status
    ELSE NULL
  END AS error_message
FROM responses;


INSERT INTO `devpost_ai.ai_extractions` (
  extraction_id,
  submission_url,
  project_title,
  challenge_title,
  content_hash,
  themes,
  theme_confidence,
  project_type,
  use_cases,
  target_audience,
  technologies_mentioned,
  sentiment_score,
  enthusiasm_level,
  summary_200,
  key_innovation,
  problem_addressed,
  solution_approach,
  narrative_length,
  has_clear_problem,
  has_clear_solution,
  has_impact_metrics,
  contains_pii,
  prompt_version,
  model_name,
  processed_at
)
SELECT
  extraction_id,
  submission_url,
  project_title,
  challenge_title,
  content_hash,
  
  JSON_QUERY_ARRAY(raw_json, '$.themes') AS themes,
  SAFE_CAST(JSON_VALUE(raw_json, '$.theme_confidence') AS FLOAT64) AS theme_confidence,
  JSON_VALUE(raw_json, '$.project_type') AS project_type,
  JSON_QUERY_ARRAY(raw_json, '$.use_cases') AS use_cases,
  JSON_QUERY_ARRAY(raw_json, '$.target_audience') AS target_audience,
  JSON_QUERY_ARRAY(raw_json, '$.technologies_mentioned') AS technologies_mentioned,
  SAFE_CAST(JSON_VALUE(raw_json, '$.sentiment_score') AS FLOAT64) AS sentiment_score,
  JSON_VALUE(raw_json, '$.enthusiasm_level') AS enthusiasm_level,
  JSON_VALUE(raw_json, '$.summary_200') AS summary_200,
  JSON_VALUE(raw_json, '$.key_innovation') AS key_innovation,
  JSON_VALUE(raw_json, '$.problem_addressed') AS problem_addressed,
  JSON_VALUE(raw_json, '$.solution_approach') AS solution_approach,
  CHAR_LENGTH(s.about_the_project) AS narrative_length,
  SAFE_CAST(JSON_VALUE(raw_json, '$.has_clear_problem') AS BOOL) AS has_clear_problem,
  SAFE_CAST(JSON_VALUE(raw_json, '$.has_clear_solution') AS BOOL) AS has_clear_solution,
  SAFE_CAST(JSON_VALUE(raw_json, '$.has_impact_metrics') AS BOOL) AS has_impact_metrics,
  SAFE_CAST(JSON_VALUE(raw_json, '$.contains_pii') AS BOOL) AS contains_pii,
  prompt_version,
  model_name,
  processed_at
FROM `devpost_ai.ai_extractions_raw` r
JOIN `devpost_ai.submissions` s USING (submission_url)
WHERE processing_status = 'completed'
  AND extraction_id NOT IN (SELECT extraction_id FROM `devpost_ai.ai_extractions`);


INSERT INTO `devpost_ai.ai_extractions_failed` (
  extraction_id,
  submission_url,
  project_title,
  content_hash,
  raw_json,
  error_message
)
SELECT
  extraction_id,
  submission_url,
  project_title,
  content_hash,
  raw_json,
  error_message
FROM `devpost_ai.ai_extractions_raw`
WHERE processing_status = 'failed'
  AND extraction_id NOT IN (SELECT extraction_id FROM `devpost_ai.ai_extractions_failed`);


/*
INSERT INTO `devpost_ai.ai_extractions_raw` (...)
WITH batch_to_process AS (
  SELECT * FROM `devpost_ai.submissions_to_process`
  LIMIT 1000  -- Adjust batch size based on quota and budget
)
*/


SELECT
  processing_status,
  COUNT(*) AS count,
  AVG(TIMESTAMP_DIFF(CURRENT_TIMESTAMP(), processed_at, SECOND)) AS avg_age_seconds
FROM `devpost_ai.ai_extractions_raw`
GROUP BY processing_status;

SELECT
  COUNT(*) AS total_extractions,
  COUNT(DISTINCT content_hash) AS unique_narratives,
  AVG(theme_confidence) AS avg_confidence,
  AVG(sentiment_score) AS avg_sentiment,
  AVG(ARRAY_LENGTH(themes)) AS avg_themes_per_project
FROM `devpost_ai.ai_extractions`;

SELECT
  error_message,
  COUNT(*) AS count
FROM `devpost_ai.ai_extractions_failed`
GROUP BY error_message
ORDER BY count DESC;

SELECT
  CASE
    WHEN theme_confidence >= 0.8 THEN 'High (0.8+)'
    WHEN theme_confidence >= 0.6 THEN 'Medium (0.6-0.8)'
    WHEN theme_confidence >= 0.4 THEN 'Low (0.4-0.6)'
    ELSE 'Very Low (<0.4)'
  END AS confidence_bucket,
  COUNT(*) AS count,
  ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) AS percentage
FROM `devpost_ai.ai_extractions`
GROUP BY confidence_bucket
ORDER BY MIN(theme_confidence) DESC;


WITH remaining AS (
  SELECT COUNT(*) AS narratives_remaining
  FROM `devpost_ai.submissions_to_process`
)
SELECT
  narratives_remaining,
  narratives_remaining * 0.0001 AS estimated_cost_usd,
  narratives_remaining * 1.5 AS estimated_seconds,
  ROUND(narratives_remaining * 1.5 / 60, 1) AS estimated_minutes
FROM remaining;
