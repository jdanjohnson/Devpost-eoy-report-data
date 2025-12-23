import pandas as pd
import os
import re
from typing import Dict, List, Optional, Tuple
from app.aggregate import DataAggregator


class RandomSampler:
    """
    Random sampling tool for hackathon submissions.
    Extracts random submissions from a hackathon based on name or URL.
    """
    
    def __init__(self, aggregator: DataAggregator = None):
        self.aggregator = aggregator if aggregator else DataAggregator()
        self.submissions_df = self.aggregator._get_submissions_df()
    
    @staticmethod
    def extract_hackathon_slug(url_or_name: str) -> str:
        """
        Extract hackathon slug from a URL or return the name as-is.
        
        Examples:
            - "https://hackonomics.devpost.com" -> "hackonomics"
            - "https://hackonomics.devpost.com/submissions/123" -> "hackonomics"
            - "hackonomics.devpost.com" -> "hackonomics"
            - "Hackonomics 2024" -> "hackonomics 2024" (lowercased)
        """
        url_or_name = url_or_name.strip()
        
        # Pattern to match devpost URLs
        devpost_pattern = r'(?:https?://)?([a-zA-Z0-9-]+)\.devpost\.com'
        match = re.match(devpost_pattern, url_or_name)
        
        if match:
            return match.group(1).lower()
        
        # If not a URL, return lowercased name
        return url_or_name.lower()
    
    def get_available_hackathons(self) -> List[Dict]:
        """
        Get list of all available hackathons in the dataset with submission counts.
        """
        if self.submissions_df is None or 'Submission Url' not in self.submissions_df.columns:
            return []
        
        # Extract hackathon slugs from submission URLs
        df = self.submissions_df.copy()
        df['hackathon_slug'] = df['Submission Url'].str.extract(r'https://([^.]+)\.devpost\.com')
        
        # Group by hackathon slug and count submissions
        hackathon_counts = df.groupby('hackathon_slug').agg({
            'Project Title': 'count',
            'Challenge Title': 'first',
            'Organization Name': 'first'
        }).reset_index()
        
        hackathon_counts.columns = ['slug', 'submission_count', 'challenge_title', 'organization']
        hackathon_counts = hackathon_counts.sort_values('submission_count', ascending=False)
        
        result = []
        for _, row in hackathon_counts.iterrows():
            result.append({
                'slug': row['slug'],
                'challenge_title': row['challenge_title'],
                'organization': row['organization'],
                'submission_count': row['submission_count'],
                'url': f"https://{row['slug']}.devpost.com"
            })
        
        return result
    
    def find_hackathon(self, identifier: str) -> Optional[Dict]:
        """
        Find a hackathon by URL or name.
        Returns hackathon info if found, None otherwise.
        """
        if self.submissions_df is None:
            return None
        
        slug = self.extract_hackathon_slug(identifier)
        
        # Extract slugs from submission URLs
        df = self.submissions_df.copy()
        df['hackathon_slug'] = df['Submission Url'].str.extract(r'https://([^.]+)\.devpost\.com')
        
        # Filter by slug
        matching = df[df['hackathon_slug'].str.lower() == slug]
        
        if matching.empty:
            # Try matching by Challenge Title (case-insensitive)
            matching = df[df['Challenge Title'].str.lower() == identifier.lower()]
        
        if matching.empty:
            # Try partial match on Challenge Title
            matching = df[df['Challenge Title'].str.lower().str.contains(slug, na=False)]
        
        if matching.empty:
            return None
        
        return {
            'slug': matching['hackathon_slug'].iloc[0] if 'hackathon_slug' in matching.columns else slug,
            'challenge_title': matching['Challenge Title'].iloc[0],
            'organization': matching['Organization Name'].iloc[0],
            'submission_count': len(matching),
            'url': f"https://{matching['hackathon_slug'].iloc[0]}.devpost.com" if pd.notna(matching['hackathon_slug'].iloc[0]) else None
        }
    
    def get_random_sample(
        self, 
        identifier: str, 
        sample_size: int = 30, 
        random_state: Optional[int] = None
    ) -> Tuple[pd.DataFrame, Dict]:
        """
        Get a random sample of submissions from a hackathon.
        
        Args:
            identifier: Hackathon URL or name
            sample_size: Number of submissions to sample (default: 30)
            random_state: Random seed for reproducibility (optional)
        
        Returns:
            Tuple of (sampled DataFrame, hackathon info dict)
        """
        if self.submissions_df is None:
            return pd.DataFrame(), {'error': 'No submission data available'}
        
        slug = self.extract_hackathon_slug(identifier)
        
        # Extract slugs from submission URLs
        df = self.submissions_df.copy()
        df['hackathon_slug'] = df['Submission Url'].str.extract(r'https://([^.]+)\.devpost\.com')
        
        # Filter by slug
        matching = df[df['hackathon_slug'].str.lower() == slug]
        
        if matching.empty:
            # Try matching by Challenge Title (case-insensitive)
            matching = df[df['Challenge Title'].str.lower() == identifier.lower()]
        
        if matching.empty:
            # Try partial match on Challenge Title
            matching = df[df['Challenge Title'].str.lower().str.contains(slug, na=False)]
        
        if matching.empty:
            return pd.DataFrame(), {
                'error': f'No submissions found for hackathon: {identifier}',
                'searched_slug': slug
            }
        
        hackathon_info = {
            'slug': matching['hackathon_slug'].iloc[0] if pd.notna(matching['hackathon_slug'].iloc[0]) else slug,
            'challenge_title': matching['Challenge Title'].iloc[0],
            'organization': matching['Organization Name'].iloc[0],
            'total_submissions': len(matching),
            'sample_size': min(sample_size, len(matching)),
            'url': f"https://{matching['hackathon_slug'].iloc[0]}.devpost.com" if pd.notna(matching['hackathon_slug'].iloc[0]) else None
        }
        
        # Sample submissions
        actual_sample_size = min(sample_size, len(matching))
        sampled = matching.sample(n=actual_sample_size, random_state=random_state)
        
        # Select relevant columns for output
        output_columns = [
            'Project Title',
            'Submission Url',
            'Organization Name',
            'Challenge Title',
            'Project Created At',
            'About The Project',
            'Built With',
            'Additional Team Member Count'
        ]
        
        # Only include columns that exist
        available_columns = [col for col in output_columns if col in sampled.columns]
        sampled = sampled[available_columns].reset_index(drop=True)
        
        return sampled, hackathon_info
    
    def export_sample(
        self, 
        identifier: str, 
        output_path: str, 
        sample_size: int = 30,
        random_state: Optional[int] = None
    ) -> bool:
        """
        Export a random sample to Excel.
        
        Args:
            identifier: Hackathon URL or name
            output_path: Path to save the Excel file
            sample_size: Number of submissions to sample
            random_state: Random seed for reproducibility
        
        Returns:
            True if export successful, False otherwise
        """
        sampled, info = self.get_random_sample(identifier, sample_size, random_state)
        
        if sampled.empty:
            return False
        
        try:
            with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                # Write sample data
                sampled.to_excel(writer, sheet_name='Random Sample', index=False)
                
                # Write metadata
                metadata = pd.DataFrame([{
                    'Hackathon': info.get('challenge_title', ''),
                    'Organization': info.get('organization', ''),
                    'URL': info.get('url', ''),
                    'Total Submissions': info.get('total_submissions', 0),
                    'Sample Size': info.get('sample_size', 0),
                    'Random Seed': random_state if random_state else 'Random'
                }])
                metadata.to_excel(writer, sheet_name='Metadata', index=False)
            
            return True
        except Exception as e:
            print(f"Error exporting sample: {e}")
            return False
    
    def search_hackathons(self, query: str, limit: int = 20) -> List[Dict]:
        """
        Search for hackathons by name or slug.
        
        Args:
            query: Search query
            limit: Maximum number of results
        
        Returns:
            List of matching hackathon info dicts
        """
        hackathons = self.get_available_hackathons()
        
        if not hackathons:
            return []
        
        query_lower = query.lower()
        
        # Score and filter hackathons
        scored = []
        for h in hackathons:
            score = 0
            slug = h['slug'] or ''
            title = h['challenge_title'] or ''
            
            # Exact slug match
            if slug.lower() == query_lower:
                score = 100
            # Slug starts with query
            elif slug.lower().startswith(query_lower):
                score = 80
            # Slug contains query
            elif query_lower in slug.lower():
                score = 60
            # Title contains query
            elif query_lower in title.lower():
                score = 40
            
            if score > 0:
                scored.append((score, h))
        
        # Sort by score descending, then by submission count
        scored.sort(key=lambda x: (-x[0], -x[1]['submission_count']))
        
        return [h for _, h in scored[:limit]]
