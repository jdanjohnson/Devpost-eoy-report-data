--
--


CREATE OR REPLACE VIEW `devpost_ai.theme_summary` AS
WITH theme_exploded AS (
  SELECT
    theme,
    submission_url,
    project_title,
    challenge_title,
    theme_confidence,
    sentiment_score,
    has_clear_problem,
    has_clear_solution
  FROM `devpost_ai.ai_extractions`,
  UNNEST(themes) AS theme
  WHERE theme_confidence >= 0.6  -- Apply confidence threshold
)
SELECT
  theme,
  COUNT(*) AS project_count,
  ROUND(AVG(theme_confidence), 3) AS avg_confidence,
  ROUND(AVG(sentiment_score), 3) AS avg_sentiment,
  ROUND(AVG(CASE WHEN has_clear_problem THEN 1 ELSE 0 END), 3) AS pct_clear_problem,
  ROUND(AVG(CASE WHEN has_clear_solution THEN 1 ELSE 0 END), 3) AS pct_clear_solution,
  COUNT(DISTINCT challenge_title) AS hackathons_count
FROM theme_exploded
GROUP BY theme
ORDER BY project_count DESC;

WITH theme_pairs AS (
  SELECT
    t1.theme AS theme1,
    t2.theme AS theme2,
    COUNT(*) AS co_occurrence_count
  FROM `devpost_ai.ai_extractions` e,
  UNNEST(e.themes) AS t1,
  UNNEST(e.themes) AS t2
  WHERE t1.theme < t2.theme  -- Avoid duplicates
    AND e.theme_confidence >= 0.6
  GROUP BY theme1, theme2
)
SELECT *
FROM theme_pairs
WHERE co_occurrence_count >= 5
ORDER BY co_occurrence_count DESC
LIMIT 50;

SELECT
  DATE_TRUNC(s.submitted_at, MONTH) AS month,
  theme,
  COUNT(*) AS project_count
FROM `devpost_ai.ai_extractions` e
JOIN `devpost_ai.submissions` s USING (submission_url),
UNNEST(e.themes) AS theme
WHERE e.theme_confidence >= 0.6
GROUP BY month, theme
ORDER BY month DESC, project_count DESC;


CREATE OR REPLACE VIEW `devpost_ai.project_type_summary` AS
SELECT
  project_type,
  COUNT(*) AS project_count,
  ROUND(AVG(sentiment_score), 3) AS avg_sentiment,
  ROUND(AVG(theme_confidence), 3) AS avg_confidence,
  ARRAY_AGG(DISTINCT theme IGNORE NULLS LIMIT 5) AS top_themes
FROM `devpost_ai.ai_extractions`,
UNNEST(themes) AS theme
WHERE project_type IS NOT NULL
GROUP BY project_type
ORDER BY project_count DESC;


WITH tech_exploded AS (
  SELECT
    tech,
    submission_url,
    project_title
  FROM `devpost_ai.ai_extractions`,
  UNNEST(technologies_mentioned) AS tech
)
SELECT
  tech,
  COUNT(*) AS mention_count,
  COUNT(DISTINCT submission_url) AS project_count
FROM tech_exploded
GROUP BY tech
ORDER BY mention_count DESC
LIMIT 100;

SELECT
  ARRAY_TO_STRING(technologies_mentioned, ', ') AS tech_stack,
  COUNT(*) AS project_count,
  AVG(sentiment_score) AS avg_sentiment
FROM `devpost_ai.ai_extractions`
WHERE ARRAY_LENGTH(technologies_mentioned) BETWEEN 2 AND 5
GROUP BY tech_stack
HAVING project_count >= 3
ORDER BY project_count DESC
LIMIT 50;

WITH theme_tech AS (
  SELECT
    theme,
    tech,
    COUNT(*) AS count
  FROM `devpost_ai.ai_extractions`,
  UNNEST(themes) AS theme,
  UNNEST(technologies_mentioned) AS tech
  WHERE theme_confidence >= 0.6
  GROUP BY theme, tech
)
SELECT
  theme,
  ARRAY_AGG(STRUCT(tech, count) ORDER BY count DESC LIMIT 10) AS top_technologies
FROM theme_tech
GROUP BY theme
ORDER BY theme;


CREATE OR REPLACE VIEW `devpost_ai.sentiment_summary` AS
SELECT
  CASE
    WHEN sentiment_score >= 0.5 THEN 'Very Positive (0.5+)'
    WHEN sentiment_score >= 0.2 THEN 'Positive (0.2-0.5)'
    WHEN sentiment_score >= -0.2 THEN 'Neutral (-0.2 to 0.2)'
    WHEN sentiment_score >= -0.5 THEN 'Negative (-0.5 to -0.2)'
    ELSE 'Very Negative (<-0.5)'
  END AS sentiment_category,
  enthusiasm_level,
  COUNT(*) AS project_count,
  ROUND(AVG(sentiment_score), 3) AS avg_score,
  ROUND(AVG(theme_confidence), 3) AS avg_confidence
FROM `devpost_ai.ai_extractions`
GROUP BY sentiment_category, enthusiasm_level
ORDER BY MIN(sentiment_score) DESC, enthusiasm_level;

SELECT
  theme,
  ROUND(AVG(sentiment_score), 3) AS avg_sentiment,
  ROUND(STDDEV(sentiment_score), 3) AS sentiment_stddev,
  COUNT(*) AS project_count
FROM `devpost_ai.ai_extractions`,
UNNEST(themes) AS theme
WHERE theme_confidence >= 0.6
GROUP BY theme
ORDER BY avg_sentiment DESC;


CREATE OR REPLACE VIEW `devpost_ai.quality_metrics` AS
SELECT
  ROUND(AVG(CASE WHEN has_clear_problem THEN 1 ELSE 0 END), 3) AS pct_clear_problem,
  ROUND(AVG(CASE WHEN has_clear_solution THEN 1 ELSE 0 END), 3) AS pct_clear_solution,
  ROUND(AVG(CASE WHEN has_impact_metrics THEN 1 ELSE 0 END), 3) AS pct_impact_metrics,
  ROUND(AVG(CASE WHEN contains_pii THEN 1 ELSE 0 END), 3) AS pct_contains_pii,
  ROUND(AVG(narrative_length), 0) AS avg_narrative_length,
  ROUND(AVG(theme_confidence), 3) AS avg_theme_confidence,
  COUNT(*) AS total_projects
FROM `devpost_ai.ai_extractions`;

SELECT
  challenge_title,
  COUNT(*) AS project_count,
  ROUND(AVG(CASE WHEN has_clear_problem THEN 1 ELSE 0 END), 3) AS pct_clear_problem,
  ROUND(AVG(CASE WHEN has_clear_solution THEN 1 ELSE 0 END), 3) AS pct_clear_solution,
  ROUND(AVG(CASE WHEN has_impact_metrics THEN 1 ELSE 0 END), 3) AS pct_impact_metrics,
  ROUND(AVG(narrative_length), 0) AS avg_narrative_length,
  ROUND(AVG(theme_confidence), 3) AS avg_confidence
FROM `devpost_ai.ai_extractions`
GROUP BY challenge_title
HAVING project_count >= 10
ORDER BY project_count DESC;


WITH use_case_exploded AS (
  SELECT
    use_case,
    submission_url
  FROM `devpost_ai.ai_extractions`,
  UNNEST(use_cases) AS use_case
)
SELECT
  use_case,
  COUNT(*) AS project_count
FROM use_case_exploded
GROUP BY use_case
ORDER BY project_count DESC
LIMIT 100;

WITH theme_use_cases AS (
  SELECT
    theme,
    use_case,
    COUNT(*) AS count
  FROM `devpost_ai.ai_extractions`,
  UNNEST(themes) AS theme,
  UNNEST(use_cases) AS use_case
  WHERE theme_confidence >= 0.6
  GROUP BY theme, use_case
)
SELECT
  theme,
  ARRAY_AGG(STRUCT(use_case, count) ORDER BY count DESC LIMIT 10) AS top_use_cases
FROM theme_use_cases
GROUP BY theme
ORDER BY theme;


WITH audience_exploded AS (
  SELECT
    audience,
    submission_url
  FROM `devpost_ai.ai_extractions`,
  UNNEST(target_audience) AS audience
)
SELECT
  audience,
  COUNT(*) AS project_count
FROM audience_exploded
GROUP BY audience
ORDER BY project_count DESC
LIMIT 50;


SELECT
  project_title,
  submission_url,
  summary_200,
  sentiment_score,
  theme_confidence
FROM `devpost_ai.ai_extractions`
WHERE 'healthcare_medical' IN UNNEST(themes)
  AND theme_confidence >= 0.6
ORDER BY sentiment_score DESC, theme_confidence DESC
LIMIT 5;

SELECT
  COUNT(*) AS project_count,
  ROUND(AVG(sentiment_score), 3) AS avg_sentiment,
  ARRAY_AGG(project_title LIMIT 5) AS example_projects
FROM `devpost_ai.ai_extractions`
WHERE 'artificial_intelligence_ml' IN UNNEST(themes)
  AND 'education_learning' IN UNNEST(themes)
  AND theme_confidence >= 0.6;

WITH climate_projects AS (
  SELECT
    tech,
    COUNT(*) AS count
  FROM `devpost_ai.ai_extractions`,
  UNNEST(technologies_mentioned) AS tech
  WHERE 'climate_sustainability' IN UNNEST(themes)
    AND theme_confidence >= 0.6
  GROUP BY tech
)
SELECT *
FROM climate_projects
ORDER BY count DESC
LIMIT 20;

SELECT
  project_title,
  submission_url,
  summary_200,
  sentiment_score,
  enthusiasm_level,
  themes
FROM `devpost_ai.ai_extractions`
WHERE enthusiasm_level = 'high'
  AND sentiment_score < 0
ORDER BY sentiment_score ASC
LIMIT 10;

WITH recent_themes AS (
  SELECT
    theme,
    DATE_TRUNC(s.submitted_at, QUARTER) AS quarter,
    COUNT(*) AS count
  FROM `devpost_ai.ai_extractions` e
  JOIN `devpost_ai.submissions` s USING (submission_url),
  UNNEST(e.themes) AS theme
  WHERE e.theme_confidence >= 0.6
    AND s.submitted_at >= DATE_SUB(CURRENT_DATE(), INTERVAL 1 YEAR)
  GROUP BY theme, quarter
)
SELECT
  theme,
  quarter,
  count,
  LAG(count) OVER (PARTITION BY theme ORDER BY quarter) AS prev_quarter_count,
  ROUND((count - LAG(count) OVER (PARTITION BY theme ORDER BY quarter)) * 100.0 / 
    NULLIF(LAG(count) OVER (PARTITION BY theme ORDER BY quarter), 0), 1) AS growth_pct
FROM recent_themes
ORDER BY quarter DESC, count DESC;


CREATE OR REPLACE VIEW `devpost_ai.dashboard_export` AS
SELECT
  e.submission_url,
  e.project_title,
  e.challenge_title,
  s.submitted_at,
  e.themes,
  e.theme_confidence,
  e.project_type,
  e.sentiment_score,
  e.enthusiasm_level,
  e.summary_200,
  e.key_innovation,
  e.problem_addressed,
  e.solution_approach,
  e.technologies_mentioned,
  e.use_cases,
  e.target_audience,
  e.has_clear_problem,
  e.has_clear_solution,
  e.has_impact_metrics,
  e.narrative_length,
  s.like_count,
  s.comment_count,
  s.winner
FROM `devpost_ai.ai_extractions` e
JOIN `devpost_ai.submissions` s USING (submission_url)
WHERE e.theme_confidence >= 0.6;

/*

INSERT INTO `devpost_ai.ai_extractions_raw` (...)
WITH new_submissions AS (
  SELECT * FROM `devpost_ai.submissions_to_process`
  LIMIT 1000
)
*/


SELECT
  'Total Submissions' AS metric,
  COUNT(*) AS count
FROM `devpost_ai.submissions`
UNION ALL
SELECT
  'Submissions with Narratives' AS metric,
  COUNT(*) AS count
FROM `devpost_ai.submissions`
WHERE about_the_project IS NOT NULL
  AND CHAR_LENGTH(TRIM(about_the_project)) >= 10
UNION ALL
SELECT
  'Extractions Completed' AS metric,
  COUNT(*) AS count
FROM `devpost_ai.ai_extractions`
UNION ALL
SELECT
  'Extractions Failed' AS metric,
  COUNT(*) AS count
FROM `devpost_ai.ai_extractions_failed`
UNION ALL
SELECT
  'Coverage Percentage' AS metric,
  ROUND(
    (SELECT COUNT(*) FROM `devpost_ai.ai_extractions`) * 100.0 /
    NULLIF((SELECT COUNT(*) FROM `devpost_ai.submissions` 
            WHERE about_the_project IS NOT NULL 
            AND CHAR_LENGTH(TRIM(about_the_project)) >= 10), 0),
    2
  ) AS count;
