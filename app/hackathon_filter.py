import pandas as pd
import os
from typing import Dict, List, Optional
from app.hackathon_source import HackathonSource
from app.aggregate import DataAggregator


class HackathonFilter:
    """
    Filters submission and registrant data by hackathon or organizer.
    Shows data attribution clearly.
    """
    
    def __init__(self, aggregator: DataAggregator = None, source: HackathonSource = None):
        self.aggregator = aggregator if aggregator else DataAggregator()
        self.source = source if source else HackathonSource()
        
        self.submissions_df = self.aggregator._get_submissions_df()
        self.registrants_df = self.aggregator._get_registrants_df()
    
    def filter_by_hackathon(self, hackathon_name: str) -> Dict:
        """
        Filter all data for a specific hackathon.
        Returns submissions, registrants, and source validation.
        """
        result = {
            'hackathon_name': hackathon_name,
            'source_data': None,
            'validation': None,
            'submissions': pd.DataFrame(),
            'registrants': pd.DataFrame(),
            'stats': {}
        }
        
        source_data = self.source.get_hackathon_by_name(hackathon_name)
        result['source_data'] = source_data
        
        if self.submissions_df is not None and 'Challenge Title' in self.submissions_df.columns:
            submissions = self.submissions_df[
                self.submissions_df['Challenge Title'] == hackathon_name
            ]
            
            if submissions.empty:
                submissions = self.submissions_df[
                    self.submissions_df['Challenge Title'].str.lower() == hackathon_name.lower()
                ]
            
            result['submissions'] = submissions
            result['stats']['submission_count'] = len(submissions)
        
        if self.registrants_df is not None and 'Hackathon Name' in self.registrants_df.columns:
            registrants = self.registrants_df[
                self.registrants_df['Hackathon Name'] == hackathon_name
            ]
            
            if registrants.empty:
                registrants = self.registrants_df[
                    self.registrants_df['Hackathon Name'].str.lower() == hackathon_name.lower()
                ]
            
            result['registrants'] = registrants
            result['stats']['registrant_count'] = len(registrants)
        
        if source_data:
            validation = self.source.validate_hackathon_data(
                hackathon_name,
                submission_count=result['stats'].get('submission_count'),
                registrant_count=result['stats'].get('registrant_count')
            )
            result['validation'] = validation
        
        return result
    
    def filter_by_organizer(self, organizer_name: str) -> Dict:
        """
        Filter all data for a specific organizer.
        Handles case-insensitive matching and name variations.
        Returns data for all hackathons by this organizer.
        """
        result = {
            'organizer_name': organizer_name,
            'canonical_name': self.source.normalize_organizer_name(organizer_name),
            'name_variations': self.source.get_organizer_variations(organizer_name),
            'hackathons': [],
            'total_submissions': 0,
            'total_registrants': 0
        }
        
        organizer_hackathons = self.source.get_hackathons_by_organizer(organizer_name)
        
        if organizer_hackathons.empty:
            return result
        
        for _, row in organizer_hackathons.iterrows():
            hackathon_name = row['Hackathon name']
            hackathon_data = self.filter_by_hackathon(hackathon_name)
            
            hackathon_info = {
                'hackathon_name': hackathon_name,
                'source_data': hackathon_data['source_data'],
                'submission_count': hackathon_data['stats'].get('submission_count', 0),
                'registrant_count': hackathon_data['stats'].get('registrant_count', 0),
                'validation': hackathon_data['validation']
            }
            
            result['hackathons'].append(hackathon_info)
            result['total_submissions'] += hackathon_info['submission_count']
            result['total_registrants'] += hackathon_info['registrant_count']
        
        return result
    
    def get_hackathon_summary(self, hackathon_name: str) -> Dict:
        """
        Get a summary of hackathon data with attribution.
        Shows where each piece of data comes from.
        """
        filtered = self.filter_by_hackathon(hackathon_name)
        
        summary = {
            'hackathon_name': hackathon_name,
            'data_sources': {
                'source_of_truth': 'Hackathons List for Report.xlsx',
                'submissions': 'Processed submission files',
                'registrants': 'Processed registrant files'
            },
            'source_data': filtered['source_data'],
            'processed_data': {
                'submissions': filtered['stats'].get('submission_count', 0),
                'registrants': filtered['stats'].get('registrant_count', 0)
            },
            'validation': filtered['validation'],
            'data_attribution': []
        }
        
        if filtered['source_data']:
            summary['data_attribution'].append({
                'field': 'Organization Name',
                'value': filtered['source_data']['organization_name'],
                'source': 'Source of Truth'
            })
            summary['data_attribution'].append({
                'field': 'Hackathon URL',
                'value': filtered['source_data']['hackathon_url'],
                'source': 'Source of Truth'
            })
            summary['data_attribution'].append({
                'field': 'Published Date',
                'value': filtered['source_data']['published_date'],
                'source': 'Source of Truth'
            })
            summary['data_attribution'].append({
                'field': 'Total Participants (Source)',
                'value': filtered['source_data']['participant_count'],
                'source': 'Source of Truth'
            })
            summary['data_attribution'].append({
                'field': 'Valid Submissions (Source)',
                'value': filtered['source_data']['valid_submissions'],
                'source': 'Source of Truth'
            })
        
        summary['data_attribution'].append({
            'field': 'Processed Submissions',
            'value': filtered['stats'].get('submission_count', 0),
            'source': 'Processed Data Files'
        })
        summary['data_attribution'].append({
            'field': 'Processed Registrants',
            'value': filtered['stats'].get('registrant_count', 0),
            'source': 'Processed Data Files'
        })
        
        return summary
    
    def get_organizer_summary(self, organizer_name: str) -> Dict:
        """
        Get a summary of organizer data with attribution.
        Shows all hackathons and data sources.
        """
        filtered = self.filter_by_organizer(organizer_name)
        
        summary = {
            'organizer_name': organizer_name,
            'canonical_name': filtered['canonical_name'],
            'name_variations': filtered['name_variations'],
            'data_sources': {
                'source_of_truth': 'Hackathons List for Report.xlsx',
                'submissions': 'Processed submission files',
                'registrants': 'Processed registrant files'
            },
            'hackathon_count': len(filtered['hackathons']),
            'total_submissions': filtered['total_submissions'],
            'total_registrants': filtered['total_registrants'],
            'hackathons': filtered['hackathons']
        }
        
        return summary
    
    def export_hackathon_data(self, hackathon_name: str, output_path: str) -> bool:
        """
        Export all data for a specific hackathon to Excel.
        """
        filtered = self.filter_by_hackathon(hackathon_name)
        
        try:
            with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                if filtered['source_data']:
                    source_df = pd.DataFrame([filtered['source_data']])
                    source_df.to_excel(writer, sheet_name='Source Data', index=False)
                
                if not filtered['submissions'].empty:
                    filtered['submissions'].to_excel(writer, sheet_name='Submissions', index=False)
                
                if not filtered['registrants'].empty:
                    filtered['registrants'].to_excel(writer, sheet_name='Registrants', index=False)
                
                summary = self.get_hackathon_summary(hackathon_name)
                summary_df = pd.DataFrame(summary['data_attribution'])
                summary_df.to_excel(writer, sheet_name='Data Attribution', index=False)
            
            return True
        except Exception as e:
            print(f"Error exporting hackathon data: {e}")
            return False
    
    def export_organizer_data(self, organizer_name: str, output_path: str) -> bool:
        """
        Export all data for a specific organizer to Excel.
        """
        filtered = self.filter_by_organizer(organizer_name)
        
        try:
            with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                summary_data = {
                    'Canonical Name': [filtered['canonical_name']],
                    'Name Variations': [', '.join(filtered['name_variations'])],
                    'Hackathon Count': [len(filtered['hackathons'])],
                    'Total Submissions': [filtered['total_submissions']],
                    'Total Registrants': [filtered['total_registrants']]
                }
                summary_df = pd.DataFrame(summary_data)
                summary_df.to_excel(writer, sheet_name='Organizer Summary', index=False)
                
                hackathons_data = []
                for h in filtered['hackathons']:
                    hackathons_data.append({
                        'Hackathon Name': h['hackathon_name'],
                        'Submissions': h['submission_count'],
                        'Registrants': h['registrant_count'],
                        'Source Submissions': h['source_data']['valid_submissions'] if h['source_data'] else 'N/A',
                        'Source Participants': h['source_data']['participant_count'] if h['source_data'] else 'N/A'
                    })
                hackathons_df = pd.DataFrame(hackathons_data)
                hackathons_df.to_excel(writer, sheet_name='Hackathons', index=False)
            
            return True
        except Exception as e:
            print(f"Error exporting organizer data: {e}")
            return False
