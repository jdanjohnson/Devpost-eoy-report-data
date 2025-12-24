#!/usr/bin/env python3
"""
AI-Powered Narrative Analysis Script

This script processes hackathon submission narratives using Google Gemini AI to extract
structured, quantitative data from qualitative text. It converts personal narratives and
pitches into structured themes, categories, sentiment, and use cases.

Usage:
    python scripts/analyze_narratives.py --input data/submissions/data.parquet --output data/ai_extractions/
    
Environment Variables:
    GEMINI_API_KEY: Google Gemini API key (required)
"""

import os
import sys
import json
import time
import argparse
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import pandas as pd
from pydantic import BaseModel, Field, ValidationError
import google.generativeai as genai
from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).parent.parent))


class ProjectExtraction(BaseModel):
    """Structured extraction from project narrative"""
    submission_url: str
    project_title: str
    hackathon: str
    
    themes: List[str] = Field(default_factory=list, description="List of themes from taxonomy")
    theme_confidence: float = Field(0.0, description="Overall confidence in theme extraction (0-1)")
    
    project_type: Optional[str] = Field(None, description="Type of project (mobile_app, web_app, etc)")
    use_cases: List[str] = Field(default_factory=list, description="Short use case phrases")
    target_audience: List[str] = Field(default_factory=list, description="Target audiences")
    
    technologies_mentioned: List[str] = Field(default_factory=list, description="Technologies mentioned in narrative")
    
    sentiment_score: float = Field(0.0, description="Sentiment score from -1 (negative) to 1 (positive)")
    enthusiasm_level: str = Field("neutral", description="Level of enthusiasm: low, neutral, high")
    
    summary_200: str = Field("", description="Short summary (max 200 chars)")
    key_innovation: str = Field("", description="Main innovation or unique aspect")
    
    problem_addressed: str = Field("", description="Problem the project addresses")
    solution_approach: str = Field("", description="How the project solves it")
    
    narrative_length: int = Field(0, description="Length of original narrative")
    has_clear_problem: bool = Field(False, description="Whether narrative clearly states a problem")
    has_clear_solution: bool = Field(False, description="Whether narrative clearly states a solution")
    has_impact_metrics: bool = Field(False, description="Whether narrative mentions impact or metrics")
    
    contains_pii: bool = Field(False, description="Whether narrative contains PII")
    
    processed_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    model_version: str = Field("gemini-1.5-flash", description="AI model used")
    prompt_version: str = Field("v2", description="Prompt version used for extraction")


class NarrativeAnalyzer:
    """Analyzes project narratives using Google Gemini AI"""
    
    def __init__(self, api_key: str, taxonomy_path: str = "taxonomy.json", cache_dir: str = ".cache", 
                 temperature: float = 0.1, confidence_threshold: float = 0.6):
        """Initialize analyzer with API key and taxonomy"""
        self.api_key = api_key
        genai.configure(api_key=api_key)
        
        system_instruction = self._build_system_instruction()
        
        self.model = genai.GenerativeModel(
            'gemini-1.5-flash',
            system_instruction=system_instruction,
            generation_config=genai.GenerationConfig(
                temperature=temperature,
                top_p=1.0,
                top_k=1,
                max_output_tokens=1024,
                response_mime_type="application/json"
            )
        )
        
        with open(taxonomy_path, 'r') as f:
            self.taxonomy = json.load(f)
        
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        
        self.confidence_threshold = confidence_threshold
        self.last_request_time = 0
        self.min_request_interval = 1.0
        
        self.stats = {
            'processed': 0,
            'cached': 0,
            'failed': 0,
            'validation_errors': 0,
            'low_confidence': 0
        }
    
    def _get_cache_key(self, narrative: str) -> str:
        """Generate cache key from narrative hash"""
        return hashlib.sha256(narrative.encode()).hexdigest()
    
    def _get_cached_result(self, cache_key: str) -> Optional[Dict]:
        """Retrieve cached result if exists"""
        cache_file = self.cache_dir / f"{cache_key}.json"
        if cache_file.exists():
            with open(cache_file, 'r') as f:
                return json.load(f)
        return None
    
    def _save_to_cache(self, cache_key: str, result: Dict):
        """Save result to cache"""
        cache_file = self.cache_dir / f"{cache_key}.json"
        with open(cache_file, 'w') as f:
            json.dump(result, f)
    
    def _rate_limit(self):
        """Enforce rate limiting between API calls"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_request_interval:
            time.sleep(self.min_request_interval - elapsed)
        self.last_request_time = time.time()
    
    def _build_prompt(self, row: pd.Series) -> str:
        """Build prompt for Gemini API"""
        
        prompt = f"""You are analyzing a hackathon project submission to extract structured data from the narrative.

**Project Information:**
- Title: {row.get('Project Title', 'N/A')}
- Hackathon: {row.get('Challenge Title', 'N/A')}
- Technologies Used: {row.get('Built With', 'N/A')}
- Narrative: {row.get('About The Project', 'N/A')}

**Your Task:**
Extract structured information from this project narrative and return ONLY valid JSON matching this schema:

{{
  "themes": [list of applicable themes from the taxonomy below],
  "project_type": "one of: mobile_app, web_app, api_backend, game, dashboard_visualization, browser_extension, desktop_app, cli_tool, hardware_device, chatbot, platform_marketplace",
  "use_cases": [short phrases describing what the project does],
  "target_audience": [who this project is for],
  "technologies_mentioned": [technologies mentioned in the narrative, normalized],
  "sentiment_score": float from -1.0 to 1.0,
  "enthusiasm_level": "low, neutral, or high",
  "summary_200": "concise summary in 200 chars or less",
  "key_innovation": "main innovation or unique aspect",
  "problem_addressed": "what problem does this solve",
  "solution_approach": "how does it solve the problem",
  "has_clear_problem": true/false,
  "has_clear_solution": true/false,
  "has_impact_metrics": true/false,
  "contains_pii": true/false (check for emails, phone numbers, addresses)
}}

**Theme Taxonomy (choose all that apply):**
{json.dumps(self.taxonomy['theme_descriptions'], indent=2)}

**Guidelines:**
1. Only use themes from the taxonomy above
2. Be conservative with theme selection - only include if clearly relevant
3. Extract actual use cases mentioned, not generic descriptions
4. Normalize technology names (e.g., "react.js" → "react")
5. Sentiment should reflect the tone and enthusiasm in the narrative
6. Summary should capture the essence in plain language
7. Flag PII if you see email addresses, phone numbers, or physical addresses
8. If information is not available, use empty strings or empty arrays

Return ONLY the JSON object, no additional text or markdown formatting.
"""
        return prompt
    
    def analyze_narrative(self, row: pd.Series) -> Optional[ProjectExtraction]:
        """Analyze a single project narrative"""
        
        narrative = row.get('About The Project', '')
        if not narrative or pd.isna(narrative) or len(str(narrative).strip()) < 10:
            return None
        
        cache_key = self._get_cache_key(str(narrative))
        cached = self._get_cached_result(cache_key)
        if cached:
            self.stats['cached'] += 1
            try:
                return ProjectExtraction(**cached)
            except ValidationError:
                pass  # Cache invalid, re-process
        
        self._rate_limit()
        
        try:
            prompt = self._build_prompt(row)
            
            response = self.model.generate_content(prompt)
            
            response_text = response.text.strip()
            
            if response_text.startswith('```'):
                response_text = response_text.split('```')[1]
                if response_text.startswith('json'):
                    response_text = response_text[4:]
                response_text = response_text.strip()
            
            extracted_data = json.loads(response_text)
            
            extracted_data['submission_url'] = row.get('Submission Url', '')
            extracted_data['project_title'] = row.get('Project Title', '')
            extracted_data['hackathon'] = row.get('Challenge Title', '')
            extracted_data['narrative_length'] = len(str(narrative))
            
            extraction = ProjectExtraction(**extracted_data)
            
            self._save_to_cache(cache_key, extraction.model_dump())
            
            self.stats['processed'] += 1
            return extraction
            
        except json.JSONDecodeError as e:
            self.stats['failed'] += 1
            print(f"JSON decode error for {row.get('Project Title', 'unknown')}: {e}")
            return None
        except ValidationError as e:
            self.stats['validation_errors'] += 1
            print(f"Validation error for {row.get('Project Title', 'unknown')}: {e}")
            return None
        except Exception as e:
            self.stats['failed'] += 1
            print(f"Error processing {row.get('Project Title', 'unknown')}: {e}")
            return None
    
    def analyze_batch(self, df: pd.DataFrame, limit: Optional[int] = None) -> pd.DataFrame:
        """Analyze a batch of narratives"""
        
        df_with_narratives = df[df['About The Project'].notna()].copy()
        
        if limit:
            df_with_narratives = df_with_narratives.head(limit)
        
        print(f"Processing {len(df_with_narratives)} narratives...")
        
        results = []
        for idx, row in tqdm(df_with_narratives.iterrows(), total=len(df_with_narratives)):
            extraction = self.analyze_narrative(row)
            if extraction:
                results.append(extraction.model_dump())
        
        print(f"\nProcessing complete!")
        print(f"  Processed: {self.stats['processed']}")
        print(f"  Cached: {self.stats['cached']}")
        print(f"  Failed: {self.stats['failed']}")
        print(f"  Validation errors: {self.stats['validation_errors']}")
        
        if results:
            return pd.DataFrame(results)
        else:
            return pd.DataFrame()


def main():
    parser = argparse.ArgumentParser(description='Analyze hackathon narratives with AI')
    parser.add_argument('--input', required=True, help='Input parquet file with submissions')
    parser.add_argument('--output', required=True, help='Output directory for extractions')
    parser.add_argument('--limit', type=int, help='Limit number of narratives to process (for testing)')
    parser.add_argument('--taxonomy', default='taxonomy.json', help='Path to taxonomy file')
    parser.add_argument('--cache-dir', default='.cache/narratives', help='Cache directory')
    
    args = parser.parse_args()
    
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("Error: GEMINI_API_KEY environment variable not set")
        sys.exit(1)
    
    print(f"Loading data from {args.input}...")
    df = pd.read_parquet(args.input)
    print(f"Loaded {len(df)} submissions")
    
    print("Initializing AI analyzer...")
    analyzer = NarrativeAnalyzer(
        api_key=api_key,
        taxonomy_path=args.taxonomy,
        cache_dir=args.cache_dir
    )
    
    extractions_df = analyzer.analyze_batch(df, limit=args.limit)
    
    if extractions_df.empty:
        print("No extractions generated")
        sys.exit(1)
    
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    parquet_path = output_dir / f"ai_extractions_{timestamp}.parquet"
    extractions_df.to_parquet(parquet_path, index=False)
    print(f"\nSaved extractions to {parquet_path}")
    
    ndjson_path = output_dir / f"ai_extractions_{timestamp}.ndjson"
    extractions_df.to_json(ndjson_path, orient='records', lines=True)
    print(f"Saved NDJSON to {ndjson_path}")
    
    stats_path = output_dir / f"stats_{timestamp}.json"
    with open(stats_path, 'w') as f:
        json.dump(analyzer.stats, f, indent=2)
    print(f"Saved statistics to {stats_path}")
    
    print("\n✅ Analysis complete!")


if __name__ == '__main__':
    main()
