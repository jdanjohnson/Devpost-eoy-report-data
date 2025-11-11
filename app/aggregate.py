import pandas as pd
import duckdb
import os
from typing import Dict, Any, List, Optional
from collections import Counter

from app.utils import load_synonyms, normalize_token, tokenize_field


class DataAggregator:
    def __init__(self, data_dir: str = None):
        if data_dir is None:
            data_dir = os.getenv('DATA_DIR', './data')
        self.data_dir = data_dir
        self.submissions_file = f"{data_dir}/submissions/data.parquet"
        self.registrants_file = f"{data_dir}/registrants/data.parquet"
        self.synonyms = load_synonyms()
    
    def _get_submissions_df(self) -> Optional[pd.DataFrame]:
        if os.path.exists(self.submissions_file):
            return pd.read_parquet(self.submissions_file)
        return None
    
    def _get_registrants_df(self) -> Optional[pd.DataFrame]:
        if os.path.exists(self.registrants_file):
            return pd.read_parquet(self.registrants_file)
        return None
    
    def get_top_technologies(self, limit: Optional[int] = 50) -> pd.DataFrame:
        df = self._get_submissions_df()
        
        if df is None or 'Built With' not in df.columns:
            return pd.DataFrame(columns=['Technology', 'Count', 'Percentage'])
        
        tech_counter = Counter()
        tech_synonyms = self.synonyms.get('technologies', {})
        
        for value in df['Built With'].dropna():
            tokens = tokenize_field(str(value), ',')
            for token in tokens:
                normalized = normalize_token(token, tech_synonyms)
                if normalized:
                    tech_counter[normalized] += 1
        
        total_count = sum(tech_counter.values())
        
        top_techs = tech_counter.most_common() if limit is None else tech_counter.most_common(limit)
        
        result_df = pd.DataFrame([
            {
                'Rank': idx + 1,
                'Technology': tech,
                'Count': count,
                'Percentage': round((count / total_count * 100), 2) if total_count > 0 else 0
            }
            for idx, (tech, count) in enumerate(top_techs)
        ])
        
        return result_df
    
    def get_top_skills(self, limit: Optional[int] = 50) -> pd.DataFrame:
        df = self._get_registrants_df()
        
        if df is None or 'Skills' not in df.columns:
            return pd.DataFrame(columns=['Skill', 'Count', 'Percentage'])
        
        skill_counter = Counter()
        skill_synonyms = self.synonyms.get('skills', {})
        
        for value in df['Skills'].dropna():
            tokens = tokenize_field(str(value), ';')
            for token in tokens:
                normalized = normalize_token(token, skill_synonyms)
                if normalized:
                    skill_counter[normalized] += 1
        
        total_count = sum(skill_counter.values())
        
        top_skills = skill_counter.most_common() if limit is None else skill_counter.most_common(limit)
        
        result_df = pd.DataFrame([
            {
                'Rank': idx + 1,
                'Skill': skill,
                'Count': count,
                'Percentage': round((count / total_count * 100), 2) if total_count > 0 else 0
            }
            for idx, (skill, count) in enumerate(top_skills)
        ])
        
        return result_df
    
    def get_submissions_by_hackathon(self) -> pd.DataFrame:
        df = self._get_submissions_df()
        
        if df is None or 'Challenge Title' not in df.columns:
            return pd.DataFrame(columns=['Hackathon', 'Submissions', 'Organizations'])
        
        hackathon_groups = df.groupby('Challenge Title').agg({
            'Project Title': 'count',
            'Organization Name': 'nunique'
        }).reset_index()
        
        hackathon_groups.columns = ['Hackathon', 'Submissions', 'Organizations']
        
        hackathon_groups = hackathon_groups.sort_values('Submissions', ascending=False)
        
        return hackathon_groups
    
    def get_team_size_distribution(self) -> pd.DataFrame:
        df = self._get_submissions_df()
        
        if df is None or 'Additional Team Member Count' not in df.columns:
            return pd.DataFrame(columns=['Team Size', 'Count', 'Percentage'])
        
        df['Team Size'] = df['Additional Team Member Count'].fillna(0).astype(int) + 1
        
        team_size_counts = df['Team Size'].value_counts().sort_index()
        
        total = team_size_counts.sum()
        
        result_df = pd.DataFrame({
            'Team Size': team_size_counts.index,
            'Count': team_size_counts.values,
            'Percentage': ((team_size_counts / total * 100).round(2).to_numpy()) if total > 0 else 0
        })
        
        return result_df
    
    def get_country_distribution(self, limit: Optional[int] = 50) -> pd.DataFrame:
        df = self._get_registrants_df()
        
        if df is None or 'Country' not in df.columns:
            return pd.DataFrame(columns=['Country', 'Count', 'Percentage'])
        
        country_counts = df['Country'].value_counts() if limit is None else df['Country'].value_counts().head(limit)
        
        total = df['Country'].count()
        
        result_df = pd.DataFrame({
            'Country': country_counts.index,
            'Count': country_counts.values,
            'Percentage': ((country_counts / total * 100).round(2).to_numpy()) if total > 0 else 0
        })
        
        return result_df
    
    def get_occupation_breakdown(self, limit: Optional[int] = 50) -> pd.DataFrame:
        df = self._get_registrants_df()
        
        if df is None or 'Occupation' not in df.columns:
            return pd.DataFrame(columns=['Occupation', 'Count', 'Percentage'])
        
        occupation_counts = df['Occupation'].value_counts() if limit is None else df['Occupation'].value_counts().head(limit)
        
        total = df['Occupation'].count()
        
        result_df = pd.DataFrame({
            'Occupation': occupation_counts.index,
            'Count': occupation_counts.values,
            'Percentage': ((occupation_counts / total * 100).round(2).to_numpy()) if total > 0 else 0
        })
        
        return result_df
    
    def get_specialty_distribution(self) -> pd.DataFrame:
        df = self._get_registrants_df()
        
        if df is None or 'Specialty' not in df.columns:
            return pd.DataFrame(columns=['Specialty', 'Count', 'Percentage'])
        
        specialty_counts = df['Specialty'].value_counts()
        
        total = df['Specialty'].count()
        
        result_df = pd.DataFrame({
            'Specialty': specialty_counts.index,
            'Count': specialty_counts.values,
            'Percentage': ((specialty_counts / total * 100).round(2).to_numpy()) if total > 0 else 0
        })
        
        return result_df
    
    def get_work_experience_distribution(self) -> pd.DataFrame:
        df = self._get_registrants_df()
        
        if df is None or 'Work Experience' not in df.columns:
            return pd.DataFrame(columns=['Experience Range', 'Count', 'Percentage'])
        
        df['Work Experience'] = pd.to_numeric(df['Work Experience'], errors='coerce')
        
        df = df[df['Work Experience'].notna()]
        
        bins = [0, 2, 5, 10, 50]
        labels = ['0-2 years', '3-5 years', '6-10 years', '10+ years']
        
        df['Experience Range'] = pd.cut(df['Work Experience'], bins=bins, labels=labels, right=True)
        
        exp_counts = df['Experience Range'].value_counts().sort_index()
        
        total = exp_counts.sum()
        
        result_df = pd.DataFrame({
            'Experience Range': exp_counts.index,
            'Count': exp_counts.values,
            'Percentage': ((exp_counts / total * 100).round(2).to_numpy()) if total > 0 else 0
        })
        
        return result_df
    
    def get_time_trends(self, period: str = 'daily') -> pd.DataFrame:
        df = self._get_submissions_df()
        
        if df is None or 'Project Created At' not in df.columns:
            return pd.DataFrame(columns=['Date', 'Submissions', 'Cumulative'])
        
        df['Date'] = pd.to_datetime(df['Project Created At'], errors='coerce')
        
        df = df[df['Date'].notna()]
        
        if period == 'daily':
            df['Period'] = df['Date'].dt.date
        elif period == 'weekly':
            df['Period'] = df['Date'].dt.to_period('W').dt.start_time.dt.date
        elif period == 'monthly':
            df['Period'] = df['Date'].dt.to_period('M').dt.start_time.dt.date
        else:
            df['Period'] = df['Date'].dt.date
        
        time_counts = df.groupby('Period').size().reset_index(name='Submissions')
        
        time_counts = time_counts.sort_values('Period')
        
        time_counts['Cumulative'] = time_counts['Submissions'].cumsum()
        
        time_counts.columns = ['Date', 'Submissions', 'Cumulative']
        
        return time_counts
    
    def get_summary_statistics(self) -> Dict[str, Any]:
        submissions_df = self._get_submissions_df()
        registrants_df = self._get_registrants_df()
        
        summary = {
            'total_submissions': 0,
            'total_registrants': 0,
            'unique_hackathons': 0,
            'unique_organizations': 0,
            'date_range': {'start': None, 'end': None},
            'most_popular_technology': None,
            'most_popular_skill': None,
            'top_country': None,
            'avg_team_size': 0
        }
        
        if submissions_df is not None:
            summary['total_submissions'] = len(submissions_df)
            
            if 'Challenge Title' in submissions_df.columns:
                summary['unique_hackathons'] = submissions_df['Challenge Title'].nunique()
            
            if 'Organization Name' in submissions_df.columns:
                summary['unique_organizations'] = submissions_df['Organization Name'].nunique()
            
            if 'Project Created At' in submissions_df.columns:
                dates = pd.to_datetime(submissions_df['Project Created At'], errors='coerce')
                dates = dates.dropna()
                if len(dates) > 0:
                    summary['date_range'] = {
                        'start': dates.min().strftime('%Y-%m-%d'),
                        'end': dates.max().strftime('%Y-%m-%d')
                    }
            
            if 'Additional Team Member Count' in submissions_df.columns:
                team_sizes = submissions_df['Additional Team Member Count'].fillna(0).astype(int) + 1
                summary['avg_team_size'] = round(team_sizes.mean(), 2)
        
        if registrants_df is not None:
            summary['total_registrants'] = len(registrants_df)
        
        top_techs = self.get_top_technologies(limit=1)
        if not top_techs.empty:
            summary['most_popular_technology'] = top_techs.iloc[0]['Technology']
        
        top_skills = self.get_top_skills(limit=1)
        if not top_skills.empty:
            summary['most_popular_skill'] = top_skills.iloc[0]['Skill']
        
        countries = self.get_country_distribution(limit=1)
        if not countries.empty:
            summary['top_country'] = countries.iloc[0]['Country']
        
        return summary
    
    def data_exists(self) -> bool:
        return (
            os.path.exists(self.submissions_file) or 
            os.path.exists(self.registrants_file)
        )
