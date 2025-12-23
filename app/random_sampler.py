import pandas as pd
import os
import re
from typing import Dict, List, Optional, Tuple, Callable, Generator
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
    
    def load_hackathon_list(
        self, 
        file_path: str,
        filter_column: Optional[str] = None,
        filter_value: Optional[str] = None
    ) -> Tuple[pd.DataFrame, str]:
        """
        Load a hackathon list from an Excel file.
        
        Args:
            file_path: Path to the Excel file containing hackathon URLs
            filter_column: Optional column name to filter by (e.g., 'Include_in_Sample')
            filter_value: Optional value to filter for (e.g., 'YES')
        
        Returns:
            Tuple of (DataFrame with hackathon list, URL column name)
        """
        try:
            df = pd.read_excel(file_path)
            
            # Apply filter if specified
            if filter_column and filter_value:
                if filter_column in df.columns:
                    df = df[df[filter_column] == filter_value]
                else:
                    raise ValueError(f"Filter column '{filter_column}' not found in file")
            
            # Find the URL column
            url_columns = [c for c in df.columns if 'url' in c.lower()]
            if not url_columns:
                # Try to find a column with devpost URLs
                for col in df.columns:
                    if df[col].astype(str).str.contains('devpost.com', na=False).any():
                        url_columns = [col]
                        break
            
            if not url_columns:
                raise ValueError("No URL column found in the hackathon list file")
            
            url_column = url_columns[0]
            return df, url_column
        except Exception as e:
            raise ValueError(f"Error loading hackathon list: {e}")
    
    def batch_sample(
        self,
        hackathon_urls: List[str],
        sample_size: int = 30,
        random_state: Optional[int] = None,
        progress_callback: Optional[Callable[[int, int, str, str], None]] = None
    ) -> Generator[Dict, None, None]:
        """
        Process multiple hackathons and yield results for each.
        
        Args:
            hackathon_urls: List of hackathon URLs to process
            sample_size: Number of submissions to sample per hackathon
            random_state: Base random seed (incremented for each hackathon)
            progress_callback: Optional callback(current, total, url, status)
        
        Yields:
            Dict with keys: url, slug, hackathon_name, organization, 
                           total_submissions, sample_size, sample_df, status, error
        """
        total = len(hackathon_urls)
        
        for idx, url in enumerate(hackathon_urls):
            if not url or pd.isna(url):
                continue
            
            url = str(url).strip()
            if not url:
                continue
            
            # Calculate random state for this hackathon
            current_random_state = None
            if random_state is not None:
                current_random_state = random_state + idx
            
            # Get sample
            sample_df, info = self.get_random_sample(
                url, 
                sample_size=sample_size,
                random_state=current_random_state
            )
            
            result = {
                'url': url,
                'slug': self.extract_hackathon_slug(url),
                'hackathon_name': info.get('challenge_title', ''),
                'organization': info.get('organization', ''),
                'total_submissions': info.get('total_submissions', 0),
                'sample_size': info.get('sample_size', 0),
                'sample_df': sample_df,
                'status': 'success' if not sample_df.empty else 'not_found',
                'error': info.get('error', None)
            }
            
            if progress_callback:
                status = 'success' if result['status'] == 'success' else 'not found'
                progress_callback(idx + 1, total, url, status)
            
            yield result
    
    def batch_sample_from_file(
        self,
        file_path: str,
        sample_size: int = 30,
        random_state: Optional[int] = None,
        progress_callback: Optional[Callable[[int, int, str, str], None]] = None,
        filter_column: Optional[str] = None,
        filter_value: Optional[str] = None
    ) -> Generator[Dict, None, None]:
        """
        Process hackathons from an Excel file and yield results.
        
        Args:
            file_path: Path to Excel file with hackathon URLs
            sample_size: Number of submissions to sample per hackathon
            random_state: Base random seed
            progress_callback: Optional callback(current, total, url, status)
            filter_column: Optional column name to filter by (e.g., 'Include_in_Sample')
            filter_value: Optional value to filter for (e.g., 'YES')
        
        Yields:
            Dict with sample results for each hackathon
        """
        df, url_column = self.load_hackathon_list(
            file_path, 
            filter_column=filter_column, 
            filter_value=filter_value
        )
        urls = df[url_column].dropna().tolist()
        
        yield from self.batch_sample(
            urls,
            sample_size=sample_size,
            random_state=random_state,
            progress_callback=progress_callback
        )
    
    def export_batch_samples(
        self,
        results: List[Dict],
        output_path: str,
        include_summary: bool = True
    ) -> bool:
        """
        Export batch sample results to a single Excel file.
        
        Args:
            results: List of result dicts from batch_sample
            output_path: Path to save the Excel file
            include_summary: Whether to include a summary sheet
        
        Returns:
            True if export successful, False otherwise
        """
        try:
            # Combine all samples into one DataFrame
            all_samples = []
            summary_data = []
            
            for result in results:
                if result['status'] == 'success' and not result['sample_df'].empty:
                    sample_df = result['sample_df'].copy()
                    # Add hackathon identifier columns
                    sample_df.insert(0, 'Hackathon URL', result['url'])
                    sample_df.insert(1, 'Hackathon Slug', result['slug'])
                    all_samples.append(sample_df)
                
                summary_data.append({
                    'Hackathon URL': result['url'],
                    'Hackathon Slug': result['slug'],
                    'Hackathon Name': result['hackathon_name'],
                    'Organization': result['organization'],
                    'Total Submissions': result['total_submissions'],
                    'Sample Size': result['sample_size'],
                    'Status': result['status'],
                    'Error': result['error'] or ''
                })
            
            with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                # Write combined samples
                if all_samples:
                    combined_df = pd.concat(all_samples, ignore_index=True)
                    combined_df.to_excel(writer, sheet_name='All Samples', index=False)
                
                # Write summary
                if include_summary:
                    summary_df = pd.DataFrame(summary_data)
                    summary_df.to_excel(writer, sheet_name='Summary', index=False)
                    
                    # Write statistics
                    stats = {
                        'Total Hackathons Processed': len(results),
                        'Hackathons Found': sum(1 for r in results if r['status'] == 'success'),
                        'Hackathons Not Found': sum(1 for r in results if r['status'] == 'not_found'),
                        'Total Samples Collected': sum(r['sample_size'] for r in results),
                    }
                    stats_df = pd.DataFrame([stats])
                    stats_df.to_excel(writer, sheet_name='Statistics', index=False)
            
            return True
        except Exception as e:
            print(f"Error exporting batch samples: {e}")
            return False
    
    def get_batch_preview(
        self,
        file_path: str,
        limit: int = 10,
        filter_column: Optional[str] = None,
        filter_value: Optional[str] = None
    ) -> Tuple[List[Dict], int]:
        """
        Preview hackathons from a list file and check which ones have data.
        
        Args:
            file_path: Path to Excel file with hackathon URLs
            limit: Number of hackathons to preview
            filter_column: Optional column name to filter by (e.g., 'Include_in_Sample')
            filter_value: Optional value to filter for (e.g., 'YES')
        
        Returns:
            Tuple of (list of preview dicts, total count)
        """
        df, url_column = self.load_hackathon_list(
            file_path,
            filter_column=filter_column,
            filter_value=filter_value
        )
        urls = df[url_column].dropna().tolist()
        total = len(urls)
        
        preview = []
        for url in urls[:limit]:
            url = str(url).strip()
            if not url:
                continue
            
            slug = self.extract_hackathon_slug(url)
            hackathon_info = self.find_hackathon(url)
            
            preview.append({
                'url': url,
                'slug': slug,
                'found': hackathon_info is not None,
                'hackathon_name': hackathon_info['challenge_title'] if hackathon_info else None,
                'submission_count': hackathon_info['submission_count'] if hackathon_info else 0
            })
        
        return preview, total
