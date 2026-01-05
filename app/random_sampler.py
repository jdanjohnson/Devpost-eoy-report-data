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
    
    # Submission bucket thresholds
    BUCKET_THRESHOLDS = [
        (300, 'Bucket E (Mega)'),      # 300+ submissions
        (100, 'Bucket D (Large)'),     # 100-299 submissions
        (25, 'Bucket C (Mid-Size)'),   # 25-99 submissions
        (10, 'Bucket B (Small)'),      # 10-24 submissions
        (1, 'Bucket A (Micro)'),       # 1-9 submissions
    ]
    
    # Columns to exclude from exports
    EXCLUDED_COLUMNS = [
        'Hackathon Description',
        '_dedup_key',  # Internal deduplication key
    ]
    
    # Path to AI hackathons list
    AI_HACKATHONS_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'ai_hackathons_list.xlsx')
    
    def __init__(self, aggregator: DataAggregator = None):
        self.aggregator = aggregator if aggregator else DataAggregator()
        self.submissions_df = self.aggregator._get_submissions_df()
        self._ai_hackathons_cache = None
    
    def get_ai_hackathons_list(self) -> List[str]:
        """
        Load the list of AI/ML hackathon URLs from the AI hackathons file.
        
        Returns:
            List of hackathon URLs
        """
        if self._ai_hackathons_cache is not None:
            return self._ai_hackathons_cache
        
        if not os.path.exists(self.AI_HACKATHONS_FILE):
            return []
        
        try:
            df = pd.read_excel(self.AI_HACKATHONS_FILE)
            if 'Hackathon url' in df.columns:
                urls = df['Hackathon url'].dropna().tolist()
                self._ai_hackathons_cache = urls
                return urls
        except Exception as e:
            print(f"Error loading AI hackathons list: {e}")
        
        return []
    
    def get_ai_hackathons_metadata(self) -> pd.DataFrame:
        """
        Load the AI hackathons metadata including Organization Type and Category.
        
        Returns:
            DataFrame with hackathon metadata
        """
        if not os.path.exists(self.AI_HACKATHONS_FILE):
            return pd.DataFrame()
        
        try:
            df = pd.read_excel(self.AI_HACKATHONS_FILE)
            # Keep relevant columns for merging
            keep_cols = ['Hackathon url', 'Year', 'Organization Type', 'Organization Category', 
                        'In person vs virtual', 'Hackathon Tags']
            available_cols = [c for c in keep_cols if c in df.columns]
            return df[available_cols]
        except Exception as e:
            print(f"Error loading AI hackathons metadata: {e}")
        
        return pd.DataFrame()
    
    @staticmethod
    def get_submission_bucket(submission_count: int) -> str:
        """
        Get the submission bucket classification based on number of submissions.
        
        Bucket E (Mega): 300+ submissions
        Bucket D (Large): 100-299 submissions
        Bucket C (Mid-Size): 25-99 submissions
        Bucket B (Small): 10-24 submissions
        Bucket A (Micro): 1-9 submissions
        """
        for threshold, bucket_name in RandomSampler.BUCKET_THRESHOLDS:
            if submission_count >= threshold:
                return bucket_name
        return 'Bucket A (Micro)'  # Default for 0 or negative (shouldn't happen)
    
    @staticmethod
    def extract_year_from_date(date_value) -> Optional[int]:
        """
        Extract year from a date value.
        
        Args:
            date_value: Date string or datetime object
        
        Returns:
            Year as integer, or None if parsing fails
        """
        if pd.isna(date_value):
            return None
        try:
            if isinstance(date_value, str):
                parsed_date = pd.to_datetime(date_value, errors='coerce')
                if pd.isna(parsed_date):
                    return None
                return parsed_date.year
            elif hasattr(date_value, 'year'):
                return date_value.year
            else:
                return None
        except Exception:
            return None
    
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
        random_state: Optional[int] = None,
        export_all: bool = False
    ) -> Tuple[pd.DataFrame, Dict]:
        """
        Get a random sample of submissions from a hackathon, or all submissions if export_all is True.
        
        Args:
            identifier: Hackathon URL or name
            sample_size: Number of submissions to sample (default: 30, ignored if export_all=True)
            random_state: Random seed for reproducibility (optional)
            export_all: If True, return all submissions instead of a random sample
        
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
        
        total_submissions = len(matching)
        
        # Determine actual sample size
        if export_all:
            actual_sample_size = total_submissions
            sampled = matching.copy()
        else:
            actual_sample_size = min(sample_size, total_submissions)
            sampled = matching.sample(n=actual_sample_size, random_state=random_state)
        
        # Calculate hackathon year from submission dates
        hackathon_year = None
        if 'Project Created At' in matching.columns:
            years = matching['Project Created At'].apply(self.extract_year_from_date).dropna()
            if len(years) > 0:
                hackathon_year = int(years.mode().iloc[0]) if len(years.mode()) > 0 else int(years.iloc[0])
        
        hackathon_info = {
            'slug': matching['hackathon_slug'].iloc[0] if pd.notna(matching['hackathon_slug'].iloc[0]) else slug,
            'challenge_title': matching['Challenge Title'].iloc[0],
            'organization': matching['Organization Name'].iloc[0],
            'total_submissions': total_submissions,
            'sample_size': actual_sample_size,
            'url': f"https://{matching['hackathon_slug'].iloc[0]}.devpost.com" if pd.notna(matching['hackathon_slug'].iloc[0]) else None,
            'submission_bucket': self.get_submission_bucket(total_submissions),
            'hackathon_year': hackathon_year
        }
        
        # Include all columns except excluded ones
        excluded_cols = self.EXCLUDED_COLUMNS + ['hackathon_slug']  # Also exclude internal slug column
        available_columns = [col for col in sampled.columns if col not in excluded_cols]
        sampled = sampled[available_columns].reset_index(drop=True)
        
        # Add Year column extracted from Project Created At
        if 'Project Created At' in sampled.columns:
            sampled['Year'] = sampled['Project Created At'].apply(self.extract_year_from_date)
        
        # Add Submission Bucket column
        sampled['Submission Bucket'] = hackathon_info['submission_bucket']
        
        # Add Hackathon Year column
        sampled['Hackathon Year'] = hackathon_info['hackathon_year']
        
        # Try to merge AI hackathon metadata if available
        hackathon_url = hackathon_info.get('url')
        if hackathon_url:
            ai_metadata = self.get_ai_hackathons_metadata()
            if not ai_metadata.empty and 'Hackathon url' in ai_metadata.columns:
                matching_meta = ai_metadata[ai_metadata['Hackathon url'] == hackathon_url]
                if not matching_meta.empty:
                    meta_row = matching_meta.iloc[0]
                    # Add metadata columns
                    if 'Organization Type' in meta_row.index:
                        sampled['Organization Type'] = meta_row['Organization Type']
                    if 'Organization Category' in meta_row.index:
                        sampled['Organization Category'] = meta_row['Organization Category']
                    if 'In person vs virtual' in meta_row.index:
                        sampled['In Person vs Virtual'] = meta_row['In person vs virtual']
        
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
        progress_callback: Optional[Callable[[int, int, str, str], None]] = None,
        export_all: bool = False
    ) -> Generator[Dict, None, None]:
        """
        Process multiple hackathons and yield results for each.
        
        Args:
            hackathon_urls: List of hackathon URLs to process
            sample_size: Number of submissions to sample per hackathon (ignored if export_all=True)
            random_state: Base random seed (incremented for each hackathon)
            progress_callback: Optional callback(current, total, url, status)
            export_all: If True, return all submissions instead of a random sample
        
        Yields:
            Dict with keys: url, slug, hackathon_name, organization, 
                           total_submissions, sample_size, sample_df, status, error,
                           submission_bucket, hackathon_year
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
                random_state=current_random_state,
                export_all=export_all
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
                'error': info.get('error', None),
                'submission_bucket': info.get('submission_bucket', ''),
                'hackathon_year': info.get('hackathon_year', None)
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
        filter_value: Optional[str] = None,
        export_all: bool = False
    ) -> Generator[Dict, None, None]:
        """
        Process hackathons from an Excel file and yield results.
        
        Args:
            file_path: Path to Excel file with hackathon URLs
            sample_size: Number of submissions to sample per hackathon (ignored if export_all=True)
            random_state: Base random seed
            progress_callback: Optional callback(current, total, url, status)
            filter_column: Optional column name to filter by (e.g., 'Include_in_Sample')
            filter_value: Optional value to filter for (e.g., 'YES')
            export_all: If True, return all submissions instead of a random sample
        
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
            progress_callback=progress_callback,
            export_all=export_all
        )
    
    def batch_sample_ai_hackathons(
        self,
        sample_size: int = 30,
        random_state: Optional[int] = None,
        progress_callback: Optional[Callable[[int, int, str, str], None]] = None,
        export_all: bool = False
    ) -> Generator[Dict, None, None]:
        """
        Process all AI/ML hackathons from the built-in list and yield results.
        
        Args:
            sample_size: Number of submissions to sample per hackathon (ignored if export_all=True)
            random_state: Base random seed
            progress_callback: Optional callback(current, total, url, status)
            export_all: If True, return all submissions instead of a random sample
        
        Yields:
            Dict with sample results for each hackathon
        """
        urls = self.get_ai_hackathons_list()
        
        yield from self.batch_sample(
            urls,
            sample_size=sample_size,
            random_state=random_state,
            progress_callback=progress_callback,
            export_all=export_all
        )
    
    def get_ai_hackathons_count(self) -> int:
        """
        Get the count of AI/ML hackathons in the built-in list.
        
        Returns:
            Number of AI hackathons
        """
        return len(self.get_ai_hackathons_list())
    
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
