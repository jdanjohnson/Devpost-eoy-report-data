--
--

DECLARE PROJECT_ID STRING DEFAULT 'your-project-id';
DECLARE REGION STRING DEFAULT 'us-central1';


CREATE OR REPLACE CONNECTION `us-central1.vertex_ai_connection`
LOCATION 'us-central1'
OPTIONS (
  connection_type = 'CLOUD_RESOURCE'
);

--
--
--


CREATE SCHEMA IF NOT EXISTS `devpost_ai`
OPTIONS (
  location = 'us-central1',
  description = 'AI-powered analysis of hackathon narratives using Vertex AI'
);


CREATE OR REPLACE MODEL `devpost_ai.gemini_flash`
REMOTE WITH CONNECTION `us-central1.vertex_ai_connection`
OPTIONS (
  endpoint = 'gemini-1.5-flash'
);


CREATE OR REPLACE TABLE `devpost_ai.prompt_versions` (
  prompt_version STRING NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
  description STRING,
  system_instruction STRING,
  temperature FLOAT64 DEFAULT 0.1,
  max_output_tokens INT64 DEFAULT 1024,
  is_active BOOL DEFAULT FALSE,
  notes STRING
);

INSERT INTO `devpost_ai.prompt_versions` (
  prompt_version,
  description,
  system_instruction,
  temperature,
  max_output_tokens,
  is_active
) VALUES (
  'v1',
  'Initial extraction prompt with 20 themes',
  '''You are analyzing hackathon project submissions to extract structured data.

Extract the following information and return ONLY valid JSON:
{
  "themes": [array of applicable themes],
  "theme_confidence": float 0-1,
  "project_type": "mobile_app|web_app|api_backend|game|dashboard_visualization|browser_extension|desktop_app|cli_tool|hardware_device|chatbot|platform_marketplace",
  "use_cases": [short phrases],
  "target_audience": [who this is for],
  "technologies_mentioned": [normalized tech names],
  "sentiment_score": float -1.0 to 1.0,
  "enthusiasm_level": "low|neutral|high",
  "summary_200": "max 200 chars",
  "key_innovation": "main innovation",
  "problem_addressed": "what problem",
  "solution_approach": "how it solves",
  "has_clear_problem": bool,
  "has_clear_solution": bool,
  "has_impact_metrics": bool,
  "contains_pii": bool
}

Themes (choose all that apply):
- artificial_intelligence_ml: AI, machine learning, neural networks, LLMs
- healthcare_medical: Health, medical, wellness, fitness, mental health
- education_learning: Education, e-learning, tutoring, skill development
- climate_sustainability: Climate, environment, sustainability, green tech
- finance_fintech: Finance, banking, payments, investing, budgeting
- social_impact: Social good, community, accessibility, inclusion
- productivity_tools: Productivity, workflow, automation, organization
- gaming_entertainment: Games, entertainment, media, content creation
- communication_collaboration: Chat, messaging, collaboration, social networking
- data_analytics: Data analysis, visualization, business intelligence
- cybersecurity_privacy: Security, privacy, encryption, authentication
- iot_hardware: IoT, hardware, embedded systems, robotics
- blockchain_web3: Blockchain, crypto, NFT, decentralized apps
- ar_vr: AR, VR, mixed reality, spatial computing
- developer_tools: Dev tools, APIs, SDKs, infrastructure
- ecommerce_retail: E-commerce, shopping, retail, marketplace
- transportation_mobility: Transportation, logistics, travel, navigation
- food_agriculture: Food, agriculture, farming, nutrition
- real_estate_housing: Real estate, housing, property management
- other: Projects that don't fit other categories

Guidelines:
1. Be conservative with themes - only include if clearly relevant
2. Normalize technology names (e.g., "react.js" → "React")
3. Extract actual use cases mentioned, not generic descriptions
4. Sentiment reflects tone and enthusiasm in the narrative
5. Flag PII if you see emails, phone numbers, or addresses
6. Use empty strings/arrays if information not available
7. Return ONLY JSON, no markdown or additional text''',
  0.1,
  1024,
  TRUE
);


SELECT * FROM `us-central1.INFORMATION_SCHEMA.CONNECTIONS`
WHERE connection_name = 'vertex_ai_connection';

SELECT * FROM `devpost_ai.INFORMATION_SCHEMA.MODELS`
WHERE model_name = 'gemini_flash';

SELECT * FROM `devpost_ai.prompt_versions`
WHERE is_active = TRUE;
