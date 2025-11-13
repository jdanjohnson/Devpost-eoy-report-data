import pandas as pd
import os
from typing import Dict, List, Optional, Tuple
from datetime import datetime


class HackathonSource:
    """
    Manages the hackathon source of truth data from the Excel file.
    Provides filtering by hackathon and organizer with name normalization.
    """
    
    def __init__(self, source_file: str = None):
        if source_file is None:
            source_file = os.path.join(os.getenv('DATA_DIR', './data'), 'hackathons_source.xlsx')
        
        self.source_file = source_file
        self.df = None
        self.organizer_mapping = {}  # Maps normalized names to canonical names
        
        if os.path.exists(source_file):
            self.load_source_data()
    
    def load_source_data(self) -> bool:
        """Load the hackathon source data from Excel file."""
        try:
            self.df = pd.read_excel(
                self.source_file, 
                sheet_name='challenge_report_2022_10-2025-1'
            )
            
            self.df.columns = self.df.columns.str.strip()
            
            mask = self.df['Hackathon name'].apply(lambda x: not isinstance(x, str) or (isinstance(x, str) and not x.strip()))
            if mask.any():
                dropped_count = mask.sum()
                print(f"Dropping {dropped_count} rows with non-string or empty hackathon names")
                self.df = self.df[~mask]
            
            text_columns = ['Hackathon name', 'Organization name', 'Hackathon url', 'In person vs virtual']
            for col in text_columns:
                if col in self.df.columns:
                    self.df[col] = self.df[col].astype('string').str.strip()
            
            self.df['Hackathon published date'] = pd.to_datetime(
                self.df['Hackathon published date'], 
                errors='coerce',
                utc=True
            )
            
            self.df['Hackathon published date'] = self.df['Hackathon published date'].dt.tz_localize(None)
            
            self.df['Year'] = self.df['Hackathon published date'].dt.year
            self.df['Month'] = self.df['Hackathon published date'].dt.month
            self.df['Quarter'] = self.df['Hackathon published date'].dt.quarter
            
            self._build_organizer_mapping()
            
            return True
        except Exception as e:
            print(f"Error loading hackathon source data: {e}")
            return False
    
    def _build_organizer_mapping(self):
        """Build a mapping of normalized organizer names to canonical names."""
        if self.df is None:
            return
        
        org_groups = self.df.groupby(
            self.df['Organization name'].str.lower().str.strip()
        )['Organization name'].apply(list)
        
        for normalized_name, variations in org_groups.items():
            canonical = max(set(variations), key=variations.count)
            self.organizer_mapping[normalized_name] = {
                'canonical': canonical,
                'variations': list(set(variations)),
                'count': len(variations)
            }
    
    def normalize_organizer_name(self, name: str) -> str:
        """Normalize an organizer name to its canonical form."""
        if not name:
            return name
        
        normalized = name.lower().strip()
        if normalized in self.organizer_mapping:
            return self.organizer_mapping[normalized]['canonical']
        return name
    
    def get_organizer_variations(self, name: str) -> List[str]:
        """Get all variations of an organizer name."""
        normalized = name.lower().strip()
        if normalized in self.organizer_mapping:
            return self.organizer_mapping[normalized]['variations']
        return [name]
    
    def get_all_hackathons(self) -> pd.DataFrame:
        """Get all hackathons from the source."""
        if self.df is None:
            return pd.DataFrame()
        return self.df.copy()
    
    def get_hackathon_by_name(self, hackathon_name: str) -> Optional[Dict]:
        """Get hackathon details by name."""
        if self.df is None:
            return None
        
        matches = self.df[self.df['Hackathon name'] == hackathon_name]
        
        if matches.empty:
            matches = self.df[
                self.df['Hackathon name'].str.lower() == hackathon_name.lower()
            ]
        
        if matches.empty:
            return None
        
        row = matches.iloc[0]
        return {
            'organization_name': row['Organization name'],
            'hackathon_name': row['Hackathon name'],
            'hackathon_url': row['Hackathon url'],
            'published_date': row['Hackathon published date'],
            'participant_count': row['Total participant count'],
            'valid_submissions': row['Total valid submissions (excluding spam)'],
            'event_type': row['In person vs virtual']
        }
    
    def get_hackathons_by_organizer(self, organizer_name: str) -> pd.DataFrame:
        """Get all hackathons for a specific organizer (case-insensitive)."""
        if self.df is None:
            return pd.DataFrame()
        
        variations = self.get_organizer_variations(organizer_name)
        
        mask = self.df['Organization name'].isin(variations)
        return self.df[mask].copy()
    
    def get_all_organizers(self) -> List[Dict]:
        """Get list of all unique organizers with their canonical names."""
        if self.df is None:
            return []
        
        organizers = []
        for normalized_name, info in self.organizer_mapping.items():
            hackathon_count = len(
                self.df[self.df['Organization name'].isin(info['variations'])]
            )
            organizers.append({
                'canonical_name': info['canonical'],
                'variations': info['variations'],
                'variation_count': len(info['variations']),
                'hackathon_count': hackathon_count
            })
        
        organizers.sort(key=lambda x: x['hackathon_count'], reverse=True)
        return organizers
    
    def get_hackathon_list(self) -> List[str]:
        """Get list of all hackathon names."""
        if self.df is None:
            return []
        
        names = self.df['Hackathon name'].dropna()
        names = names[names.apply(lambda x: isinstance(x, str))]
        names = [n.strip() for n in names if n.strip()]
        return sorted(set(names), key=str.casefold)
    
    def validate_hackathon_data(self, hackathon_name: str, 
                                submission_count: int = None,
                                registrant_count: int = None) -> Dict:
        """
        Validate submission/registrant data against source of truth.
        Returns validation results with warnings/errors.
        """
        source_data = self.get_hackathon_by_name(hackathon_name)
        
        if source_data is None:
            return {
                'valid': False,
                'error': f"Hackathon '{hackathon_name}' not found in source data",
                'warnings': []
            }
        
        warnings = []
        
        if submission_count is not None:
            source_submissions = source_data['valid_submissions']
            if submission_count > source_submissions:
                warnings.append(
                    f"Submission count ({submission_count}) exceeds source data "
                    f"({source_submissions}). This may be due to spam filtering."
                )
            elif submission_count < source_submissions * 0.8:
                warnings.append(
                    f"Submission count ({submission_count}) is significantly lower "
                    f"than source data ({source_submissions}). Data may be incomplete."
                )
        
        if registrant_count is not None:
            source_participants = source_data['participant_count']
            if registrant_count > source_participants:
                warnings.append(
                    f"Registrant count ({registrant_count}) exceeds source participant "
                    f"count ({source_participants}). This is unusual."
                )
        
        return {
            'valid': True,
            'source_data': source_data,
            'warnings': warnings
        }
    
    def is_loaded(self) -> bool:
        """Check if source data is loaded."""
        return self.df is not None and not self.df.empty
    
    def get_hackathons_by_date_range(self, start_date: str = None, end_date: str = None) -> pd.DataFrame:
        """Get hackathons within a date range."""
        if self.df is None:
            return pd.DataFrame()
        
        df = self.df.copy()
        
        if start_date:
            start = pd.to_datetime(start_date)
            df = df[df['Hackathon published date'] >= start]
        
        if end_date:
            end = pd.to_datetime(end_date)
            df = df[df['Hackathon published date'] <= end]
        
        return df
    
    def get_hackathons_by_year(self, year: int) -> pd.DataFrame:
        """Get all hackathons for a specific year."""
        if self.df is None:
            return pd.DataFrame()
        
        return self.df[self.df['Year'] == year].copy()
    
    def get_time_trends(self, period: str = 'monthly') -> pd.DataFrame:
        """
        Get time-based trends of hackathons.
        
        Args:
            period: 'monthly', 'quarterly', or 'yearly'
        
        Returns:
            DataFrame with time periods and aggregated stats
        """
        if self.df is None:
            return pd.DataFrame()
        
        df = self.df.copy()
        
        if period == 'monthly':
            df['Period'] = df['Hackathon published date'].dt.to_period('M')
        elif period == 'quarterly':
            df['Period'] = df['Hackathon published date'].dt.to_period('Q')
        elif period == 'yearly':
            df['Period'] = df['Hackathon published date'].dt.to_period('Y')
        else:
            raise ValueError(f"Invalid period: {period}. Must be 'monthly', 'quarterly', or 'yearly'")
        
        trends = df.groupby('Period').agg({
            'Hackathon name': 'count',
            'Total participant count': 'sum',
            'Total valid submissions (excluding spam)': 'sum',
            'Organization name': 'nunique'
        }).reset_index()
        
        trends.columns = [
            'Period',
            'Hackathon Count',
            'Total Participants',
            'Total Submissions',
            'Unique Organizers'
        ]
        
        trends['Period'] = trends['Period'].astype(str)
        
        return trends
    
    def get_seasonal_patterns(self) -> pd.DataFrame:
        """Get hackathon activity by month of year (seasonal patterns)."""
        if self.df is None:
            return pd.DataFrame()
        
        df = self.df.copy()
        
        seasonal = df.groupby('Month').agg({
            'Hackathon name': 'count',
            'Total participant count': 'mean',
            'Total valid submissions (excluding spam)': 'mean'
        }).reset_index()
        
        seasonal.columns = [
            'Month',
            'Hackathon Count',
            'Avg Participants',
            'Avg Submissions'
        ]
        
        month_names = {
            1: 'January', 2: 'February', 3: 'March', 4: 'April',
            5: 'May', 6: 'June', 7: 'July', 8: 'August',
            9: 'September', 10: 'October', 11: 'November', 12: 'December'
        }
        seasonal['Month Name'] = seasonal['Month'].map(month_names)
        
        return seasonal
    
    def get_year_over_year_comparison(self) -> pd.DataFrame:
        """Get year-over-year comparison of hackathon metrics."""
        if self.df is None:
            return pd.DataFrame()
        
        df = self.df.copy()
        
        yoy = df.groupby('Year').agg({
            'Hackathon name': 'count',
            'Total participant count': ['sum', 'mean'],
            'Total valid submissions (excluding spam)': ['sum', 'mean'],
            'Organization name': 'nunique'
        }).reset_index()
        
        yoy.columns = [
            'Year',
            'Hackathon Count',
            'Total Participants',
            'Avg Participants per Hackathon',
            'Total Submissions',
            'Avg Submissions per Hackathon',
            'Unique Organizers'
        ]
        
        yoy['Hackathon Growth %'] = yoy['Hackathon Count'].pct_change() * 100
        yoy['Participant Growth %'] = yoy['Total Participants'].pct_change() * 100
        yoy['Submission Growth %'] = yoy['Total Submissions'].pct_change() * 100
        
        return yoy
    
    def get_organizer_timeline(self, organizer_name: str) -> pd.DataFrame:
        """Get timeline of hackathons for a specific organizer."""
        if self.df is None:
            return pd.DataFrame()
        
        variations = self.get_organizer_variations(organizer_name)
        df = self.df[self.df['Organization name'].isin(variations)].copy()
        
        df = df.sort_values('Hackathon published date')
        
        timeline = df[[
            'Hackathon published date',
            'Hackathon name',
            'Total participant count',
            'Total valid submissions (excluding spam)',
            'In person vs virtual'
        ]].copy()
        
        timeline.columns = [
            'Date',
            'Hackathon',
            'Participants',
            'Submissions',
            'Event Type'
        ]
        
        timeline['Hackathon'] = timeline['Hackathon'].astype('string')
        timeline['Event Type'] = timeline['Event Type'].astype('string')
        
        return timeline
    
    def get_date_range(self) -> Tuple[datetime, datetime]:
        """Get the date range of hackathons in the source data."""
        if self.df is None or self.df.empty:
            return None, None
        
        dates = self.df['Hackathon published date'].dropna()
        if dates.empty:
            return None, None
        
        return dates.min(), dates.max()
