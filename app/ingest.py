import pandas as pd
import os
import zipfile
import traceback
from typing import Dict, Any, List, Optional, Tuple
import tempfile
import shutil
from pathlib import Path

from app.database import Database
from app.utils import (
    compute_file_hash, 
    validate_excel_file, 
    clean_string,
    parse_datetime
)


class DataIngestor:
    def __init__(self, db: Database):
        self.db = db
        self.data_dir = os.getenv('DATA_DIR', './data')
        self.temp_dir = os.getenv('TEMP_DIR', './temp')
        self.retry_dir = os.getenv('RETRY_DIR', './incoming/retry')
        self.max_work_experience = int(os.getenv('MAX_WORK_EXPERIENCE', '50'))
        
        os.makedirs(f"{self.data_dir}/submissions", exist_ok=True)
        os.makedirs(f"{self.data_dir}/registrants", exist_ok=True)
        os.makedirs(self.temp_dir, exist_ok=True)
        os.makedirs(f"{self.retry_dir}/submissions", exist_ok=True)
        os.makedirs(f"{self.retry_dir}/registrants", exist_ok=True)
    
    def process_zip_file(self, zip_path: str, progress_callback=None) -> Dict[str, Any]:
        results = {
            'total_files': 0,
            'processed_files': 0,
            'skipped_files': 0,
            'failed_files': 0,
            'errors': []
        }
        
        temp_extract_dir = tempfile.mkdtemp(dir=self.temp_dir)
        
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(temp_extract_dir)
            
            data_files = []
            for root, dirs, files in os.walk(temp_extract_dir):
                for file in files:
                    file_lower = file.lower()
                    if (file_lower.endswith('.xlsx') or file_lower.endswith('.csv')) and not file.startswith('~') and '__MACOSX' not in root:
                        data_files.append(os.path.join(root, file))
            
            results['total_files'] = len(data_files)
            
            for idx, file_path in enumerate(data_files):
                try:
                    if progress_callback:
                        progress_callback(idx + 1, len(data_files), os.path.basename(file_path))
                    
                    file_result = self.process_single_file(file_path)
                    
                    if file_result['status'] == 'processed':
                        results['processed_files'] += 1
                    elif file_result['status'] == 'skipped':
                        results['skipped_files'] += 1
                    else:
                        results['failed_files'] += 1
                        results['errors'].append({
                            'file': os.path.basename(file_path),
                            'error': file_result.get('error', 'Unknown error')
                        })
                
                except Exception as e:
                    results['failed_files'] += 1
                    error_details = f"{str(e)}\n{traceback.format_exc()}"
                    results['errors'].append({
                        'file': os.path.basename(file_path),
                        'error': error_details
                    })
        
        finally:
            shutil.rmtree(temp_extract_dir, ignore_errors=True)
        
        return results
    
    def process_folder(self, folder_path: str, file_type: str, progress_callback=None) -> Dict[str, Any]:
        results = {
            'total_files': 0,
            'processed_files': 0,
            'skipped_files': 0,
            'failed_files': 0,
            'errors': []
        }
        
        if not os.path.exists(folder_path):
            results['errors'].append({
                'file': folder_path,
                'error': 'Folder does not exist'
            })
            return results
        
        data_files = [
            os.path.join(folder_path, f) 
            for f in os.listdir(folder_path) 
            if (f.lower().endswith('.xlsx') or f.lower().endswith('.csv')) and not f.startswith('~')
        ]
        
        results['total_files'] = len(data_files)
        
        for idx, file_path in enumerate(data_files):
            try:
                if progress_callback:
                    progress_callback(idx + 1, len(data_files), os.path.basename(file_path))
                
                file_result = self.process_single_file(file_path)
                
                if file_result['status'] == 'processed':
                    results['processed_files'] += 1
                elif file_result['status'] == 'skipped':
                    results['skipped_files'] += 1
                else:
                    results['failed_files'] += 1
                    results['errors'].append({
                        'file': os.path.basename(file_path),
                        'error': file_result.get('error', 'Unknown error')
                    })
            
            except Exception as e:
                results['failed_files'] += 1
                error_details = f"{str(e)}\n{traceback.format_exc()}"
                results['errors'].append({
                    'file': os.path.basename(file_path),
                    'error': error_details
                })
        
        return results
    
    def process_single_file(self, file_path: str, retry_path: str = None) -> Dict[str, Any]:
        file_ext = os.path.splitext(file_path)[1].lower()
        if file_ext not in ['.xlsx', '.csv']:
            return {'status': 'failed', 'error': 'Invalid file type (must be .xlsx or .csv)'}
        
        if file_ext == '.xlsx' and not validate_excel_file(file_path):
            return {'status': 'failed', 'error': 'Invalid Excel file'}
        
        file_hash = compute_file_hash(file_path)
        
        if self.db.is_file_processed(file_hash):
            return {'status': 'skipped', 'reason': 'Already processed'}
        
        try:
            df = self.load_file(file_path)
            
            if df is None or df.empty:
                return {'status': 'failed', 'error': 'Empty or unreadable file'}
            
            df = self.normalize_headers(df)
            
            file_name = os.path.basename(file_path)
            file_type = self.detect_file_type(df, file_name)
            
            if file_type == 'unknown':
                columns_found = ', '.join(df.columns.tolist())
                return {'status': 'failed', 'error': f'Unknown file type. Columns found: {columns_found}'}
            
            if retry_path is None:
                retry_path = self._persist_file_for_retry(file_path, file_hash, file_type)
            
            job_id = self.db.log_job_start(file_hash, file_name, file_type, retry_path)
            
            try:
                df = self.clean_data(df, file_type)
                
                df = self.add_dedup_key(df, file_type)
                
                self.write_to_parquet(df, file_type)
                
                self.db.log_job_complete(job_id, len(df))
                
                if retry_path and os.path.exists(retry_path):
                    os.remove(retry_path)
                
                return {
                    'status': 'processed',
                    'file_type': file_type,
                    'row_count': len(df)
                }
            
            except Exception as e:
                self.db.log_job_error(job_id, str(e))
                return {'status': 'failed', 'error': str(e)}
        
        except Exception as e:
            return {'status': 'failed', 'error': str(e)}
    
    def load_file(self, file_path: str) -> Optional[pd.DataFrame]:
        """Load file (Excel or CSV) and return DataFrame."""
        try:
            file_ext = os.path.splitext(file_path)[1].lower()
            
            if file_ext == '.xlsx':
                df = pd.read_excel(file_path, engine='openpyxl')
            elif file_ext == '.csv':
                try:
                    df = pd.read_csv(
                        file_path,
                        encoding='utf-8-sig',
                        engine='python',
                        sep=None
                    )
                except Exception:
                    df = pd.read_csv(
                        file_path,
                        encoding='latin-1',
                        engine='python',
                        sep=None
                    )
            else:
                return None
            
            return df
        except Exception as e:
            return None
    
    def read_excel_file(self, file_path: str) -> Optional[pd.DataFrame]:
        """Deprecated: Use load_file() instead. Kept for backward compatibility."""
        return self.load_file(file_path)
    
    def normalize_headers(self, df: pd.DataFrame) -> pd.DataFrame:
        has_malformed_headers = False
        
        for col in df.columns:
            if pd.isna(col) or str(col).startswith('Unnamed') or isinstance(col, (int, float)):
                has_malformed_headers = True
                break
        
        if has_malformed_headers and len(df) > 0:
            new_headers = df.iloc[0].tolist()
            df = df[1:].reset_index(drop=True)
            df.columns = new_headers
        
        cleaned_columns = []
        for col in df.columns:
            col_str = str(col).lstrip('\ufeff')
            cleaned_columns.append(clean_string(col_str))
        
        seen = {}
        unique_columns = []
        for col in cleaned_columns:
            if col in seen:
                seen[col] += 1
                unique_columns.append(f"{col}.{seen[col]}")
            else:
                seen[col] = 0
                unique_columns.append(col)
        
        df.columns = unique_columns
        
        return df
    
    def detect_file_type(self, df: pd.DataFrame, file_name: str = '') -> str:
        columns = [clean_string(str(col)).lower() for col in df.columns]
        
        submission_indicators = [
            'organization name',
            'challenge title',
            'project title',
            'submission url',
            'built with'
        ]
        
        registrant_indicators = [
            'hackathon name',
            'user id',
            'country',
            'work experience',
            'skills',
            'occupation',
            'specialty'
        ]
        
        submission_indicators_normalized = [clean_string(s).lower() for s in submission_indicators]
        registrant_indicators_normalized = [clean_string(s).lower() for s in registrant_indicators]
        
        submission_score = sum(1 for indicator in submission_indicators_normalized if indicator in columns)
        registrant_score = sum(1 for indicator in registrant_indicators_normalized if indicator in columns)
        
        if submission_score >= 3 and submission_score >= registrant_score:
            return 'submission'
        elif registrant_score >= 3:
            return 'registrant'
        
        if 'submission url' in columns:
            return 'submission'
        elif 'user id' in columns:
            return 'registrant'
        
        if file_name:
            file_name_lower = file_name.lower()
            if 'registrant' in file_name_lower:
                return 'registrant'
            elif 'submission' in file_name_lower:
                return 'submission'
        
        return 'unknown'
    
    def clean_data(self, df: pd.DataFrame, file_type: str) -> pd.DataFrame:
        object_cols = df.select_dtypes(include=['object']).columns
        for col in object_cols:
            df[col] = df[col].apply(clean_string)
        
        if file_type == 'submission':
            date_columns = ['Project Created At', 'Challenge Published At', 'Created At']
            
            for base_col in date_columns:
                df = self._merge_duplicate_columns(df, base_col)
            
            df = self._coerce_date_columns(df, date_columns)
            
            if 'Additional Team Member Count' in df.columns:
                df['Additional Team Member Count'] = pd.to_numeric(df['Additional Team Member Count'], errors='coerce')
        
        elif file_type == 'registrant':
            if 'Work Experience' in df.columns:
                df['Work Experience'] = pd.to_numeric(df['Work Experience'], errors='coerce')
                df.loc[df['Work Experience'] > self.max_work_experience, 'Work Experience'] = None
            
            if 'Interests' in df.columns:
                df = df.drop(columns=['Interests'])
        
        return df
    
    def add_dedup_key(self, df: pd.DataFrame, file_type: str) -> pd.DataFrame:
        if file_type == 'submission':
            if 'Submission Url' in df.columns:
                df['_dedup_key'] = df['Submission Url'].astype(str)
            else:
                df['_dedup_key'] = df.index.astype(str)
        
        elif file_type == 'registrant':
            if 'Hackathon Name' in df.columns and 'User ID' in df.columns:
                df['_dedup_key'] = (
                    df['Hackathon Name'].astype(str) + '|' + 
                    df['User ID'].astype(str)
                )
            else:
                df['_dedup_key'] = df.index.astype(str)
        
        return df
    
    def write_to_parquet(self, df: pd.DataFrame, file_type: str) -> None:
        output_dir = f"{self.data_dir}/{file_type}s"
        os.makedirs(output_dir, exist_ok=True)
        
        output_file = f"{output_dir}/data.parquet"
        
        if file_type == 'submission':
            date_columns = ['Project Created At', 'Challenge Published At', 'Created At']
            df = self._coerce_date_columns(df, date_columns)
        
        if os.path.exists(output_file):
            existing_df = pd.read_parquet(output_file)
            
            if file_type == 'submission':
                date_columns = ['Project Created At', 'Challenge Published At', 'Created At']
                existing_df = self._coerce_date_columns(existing_df, date_columns)
            
            combined_df = pd.concat([existing_df, df], ignore_index=True)
            
            if file_type == 'submission':
                combined_df = self._coerce_date_columns(combined_df, date_columns)
            
            if '_dedup_key' in combined_df.columns:
                combined_df = combined_df.drop_duplicates(subset=['_dedup_key'], keep='first')
            
            combined_df.to_parquet(output_file, index=False, engine='pyarrow')
        else:
            df.to_parquet(output_file, index=False, engine='pyarrow')
    
    def get_data_summary(self) -> Dict[str, Any]:
        summary = {
            'submissions': {'exists': False, 'row_count': 0},
            'registrants': {'exists': False, 'row_count': 0}
        }
        
        submission_file = f"{self.data_dir}/submissions/data.parquet"
        if os.path.exists(submission_file):
            df = pd.read_parquet(submission_file)
            summary['submissions'] = {
                'exists': True,
                'row_count': len(df),
                'columns': list(df.columns)
            }
        
        registrant_file = f"{self.data_dir}/registrants/data.parquet"
        if os.path.exists(registrant_file):
            df = pd.read_parquet(registrant_file)
            summary['registrants'] = {
                'exists': True,
                'row_count': len(df),
                'columns': list(df.columns)
            }
        
        return summary
    
    def _merge_duplicate_columns(self, df: pd.DataFrame, base_col: str) -> pd.DataFrame:
        """Merge duplicate columns (e.g., 'Skills', 'Skills.1', 'Skills.2') into base column."""
        duplicate_cols = [col for col in df.columns if col == base_col or col.startswith(f"{base_col}.")]
        
        if len(duplicate_cols) <= 1:
            return df
        
        if base_col not in df.columns:
            return df
        
        for dup_col in duplicate_cols:
            if dup_col == base_col:
                continue
            
            mask = df[base_col].isna() | (df[base_col] == '') | (df[base_col] == 'None')
            df.loc[mask, base_col] = df.loc[mask, dup_col]
            
            df = df.drop(columns=[dup_col])
        
        return df
    
    def _coerce_date_columns(self, df: pd.DataFrame, date_columns: List[str]) -> pd.DataFrame:
        """Coerce date columns to datetime64[ns] with proper handling."""
        for col in date_columns:
            if col not in df.columns:
                continue
            
            df[col] = pd.to_datetime(df[col], errors='coerce')
            
            if pd.api.types.is_datetime64_any_dtype(df[col]):
                if hasattr(df[col].dtype, 'tz') and df[col].dtype.tz is not None:
                    df[col] = df[col].dt.tz_localize(None)
        
        return df
    
    def _persist_file_for_retry(self, file_path: str, file_hash: str, file_type: str) -> str:
        """Copy file to retry directory for future retry attempts."""
        file_name = os.path.basename(file_path)
        file_ext = os.path.splitext(file_name)[1]
        retry_file_name = f"{file_hash}_{file_name}"
        retry_path = os.path.join(self.retry_dir, f"{file_type}s", retry_file_name)
        
        os.makedirs(os.path.dirname(retry_path), exist_ok=True)
        shutil.copy2(file_path, retry_path)
        
        return retry_path
    
    def retry_failed_files(self, file_hashes: List[str] = None, progress_callback=None) -> Dict[str, Any]:
        """Retry processing of failed files.
        
        Args:
            file_hashes: List of file hashes to retry. If None, retry all failed files.
            progress_callback: Optional callback function(current, total, file_name)
        
        Returns:
            Dictionary with retry results
        """
        results = {
            'total_files': 0,
            'processed_files': 0,
            'failed_files': 0,
            'skipped_files': 0,
            'errors': []
        }
        
        failed_jobs = self.db.get_failed_jobs()
        
        if file_hashes:
            failed_jobs = [job for job in failed_jobs if job['file_hash'] in file_hashes]
        
        results['total_files'] = len(failed_jobs)
        
        for idx, job in enumerate(failed_jobs):
            try:
                if progress_callback:
                    progress_callback(idx + 1, len(failed_jobs), job['file_name'])
                
                retry_path = job.get('retry_path')
                
                if not retry_path or not os.path.exists(retry_path):
                    results['failed_files'] += 1
                    results['errors'].append({
                        'file': job['file_name'],
                        'error': 'Retry file not found. Please re-upload the file.'
                    })
                    continue
                
                file_result = self.process_single_file(retry_path, retry_path)
                
                if file_result['status'] == 'processed':
                    results['processed_files'] += 1
                elif file_result['status'] == 'skipped':
                    results['skipped_files'] += 1
                elif file_result['status'] == 'failed':
                    results['failed_files'] += 1
                    results['errors'].append({
                        'file': job['file_name'],
                        'error': file_result.get('error', 'Unknown error')
                    })
            
            except Exception as e:
                results['failed_files'] += 1
                error_details = f"{str(e)}\n{traceback.format_exc()}"
                results['errors'].append({
                    'file': job['file_name'],
                    'error': error_details
                })
        
        return results
    
    def retry_files_from_errors(self, error_list: List[Dict[str, str]], progress_callback=None) -> Dict[str, Any]:
        """Retry processing of files from current session error list.
        
        Args:
            error_list: List of error dictionaries with 'file' key
            progress_callback: Optional callback function(current, total, file_name)
        
        Returns:
            Dictionary with retry results
        """
        results = {
            'total_files': 0,
            'processed_files': 0,
            'failed_files': 0,
            'skipped_files': 0,
            'errors': []
        }
        
        file_names = [error['file'] for error in error_list]
        
        failed_jobs = self.db.get_failed_jobs()
        jobs_to_retry = [job for job in failed_jobs if job['file_name'] in file_names]
        
        results['total_files'] = len(jobs_to_retry)
        
        for idx, job in enumerate(jobs_to_retry):
            try:
                if progress_callback:
                    progress_callback(idx + 1, len(jobs_to_retry), job['file_name'])
                
                retry_path = job.get('retry_path')
                
                if not retry_path or not os.path.exists(retry_path):
                    results['failed_files'] += 1
                    results['errors'].append({
                        'file': job['file_name'],
                        'error': 'Retry file not found. Please re-upload the file.'
                    })
                    continue
                
                file_result = self.process_single_file(retry_path, retry_path)
                
                if file_result['status'] == 'processed':
                    results['processed_files'] += 1
                elif file_result['status'] == 'skipped':
                    results['skipped_files'] += 1
                elif file_result['status'] == 'failed':
                    results['failed_files'] += 1
                    results['errors'].append({
                        'file': job['file_name'],
                        'error': file_result.get('error', 'Unknown error')
                    })
            
            except Exception as e:
                results['failed_files'] += 1
                error_details = f"{str(e)}\n{traceback.format_exc()}"
                results['errors'].append({
                    'file': job['file_name'],
                    'error': error_details
                })
        
        return results
