import sqlite3
import pandas as pd
from datetime import datetime
from typing import List, Dict, Any, Optional
import os


class Database:
    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = os.getenv('DATABASE_PATH', './jobs.db')
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path) if os.path.dirname(self.db_path) else '.', exist_ok=True)
        self.init_database()
    
    def get_connection(self):
        return sqlite3.connect(self.db_path)
    
    def init_database(self) -> None:
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_hash TEXT UNIQUE NOT NULL,
                file_name TEXT NOT NULL,
                file_type TEXT NOT NULL,
                status TEXT NOT NULL,
                row_count INTEGER DEFAULT 0,
                error_message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                retry_path TEXT,
                attempts INTEGER DEFAULT 1
            )
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_file_hash ON jobs(file_hash)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_status ON jobs(status)
        """)
        
        try:
            cursor.execute("ALTER TABLE jobs ADD COLUMN retry_path TEXT")
        except sqlite3.OperationalError:
            pass
        
        try:
            cursor.execute("ALTER TABLE jobs ADD COLUMN attempts INTEGER DEFAULT 1")
        except sqlite3.OperationalError:
            pass
        
        conn.commit()
        conn.close()
    
    def get_processed_files(self) -> List[str]:
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT file_hash FROM jobs 
            WHERE status = 'completed'
        """)
        
        result = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        return result
    
    def is_file_processed(self, file_hash: str) -> bool:
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT COUNT(*) FROM jobs 
            WHERE file_hash = ? AND status = 'completed'
        """, (file_hash,))
        
        count = cursor.fetchone()[0]
        conn.close()
        
        return count > 0
    
    def log_job_start(self, file_hash: str, file_name: str, file_type: str, retry_path: str = None) -> int:
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO jobs (file_hash, file_name, file_type, status, retry_path, attempts)
                VALUES (?, ?, ?, 'processing', ?, 1)
            """, (file_hash, file_name, file_type, retry_path))
            
            job_id = cursor.lastrowid
            conn.commit()
        except sqlite3.IntegrityError:
            cursor.execute("""
                SELECT attempts FROM jobs WHERE file_hash = ?
            """, (file_hash,))
            
            result = cursor.fetchone()
            attempts = (result[0] if result else 0) + 1
            
            cursor.execute("""
                UPDATE jobs 
                SET status = 'processing', error_message = NULL, attempts = ?, retry_path = ?
                WHERE file_hash = ?
            """, (attempts, retry_path, file_hash))
            
            cursor.execute("""
                SELECT id FROM jobs WHERE file_hash = ?
            """, (file_hash,))
            
            job_id = cursor.fetchone()[0]
            conn.commit()
        
        conn.close()
        return job_id
    
    def log_job_complete(self, job_id: int, row_count: int) -> None:
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE jobs 
            SET status = 'completed', 
                row_count = ?,
                completed_at = ?
            WHERE id = ?
        """, (row_count, datetime.now(), job_id))
        
        conn.commit()
        conn.close()
    
    def log_job_error(self, job_id: int, error: str) -> None:
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE jobs 
            SET status = 'failed', 
                error_message = ?,
                completed_at = ?
            WHERE id = ?
        """, (error, datetime.now(), job_id))
        
        conn.commit()
        conn.close()
    
    def get_job_history(self) -> pd.DataFrame:
        conn = self.get_connection()
        
        df = pd.read_sql_query("""
            SELECT 
                id,
                file_name,
                file_type,
                status,
                row_count,
                error_message,
                created_at,
                completed_at,
                retry_path,
                attempts
            FROM jobs
            ORDER BY created_at DESC
        """, conn)
        
        conn.close()
        return df
    
    def delete_job(self, job_id: int) -> None:
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM jobs WHERE id = ?", (job_id,))
        
        conn.commit()
        conn.close()
    
    def get_job_by_id(self, job_id: int) -> Optional[Dict[str, Any]]:
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                id, file_hash, file_name, file_type, status, 
                row_count, error_message, created_at, completed_at, retry_path, attempts
            FROM jobs
            WHERE id = ?
        """, (job_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'id': row[0],
                'file_hash': row[1],
                'file_name': row[2],
                'file_type': row[3],
                'status': row[4],
                'row_count': row[5],
                'error_message': row[6],
                'created_at': row[7],
                'completed_at': row[8],
                'retry_path': row[9],
                'attempts': row[10]
            }
        return None
    
    def get_summary_stats(self) -> Dict[str, Any]:
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                COUNT(*) as total_jobs,
                SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed_jobs,
                SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed_jobs,
                SUM(CASE WHEN status = 'processing' THEN 1 ELSE 0 END) as processing_jobs,
                SUM(row_count) as total_rows
            FROM jobs
        """)
        
        row = cursor.fetchone()
        conn.close()
        
        return {
            'total_jobs': row[0] or 0,
            'completed_jobs': row[1] or 0,
            'failed_jobs': row[2] or 0,
            'processing_jobs': row[3] or 0,
            'total_rows': row[4] or 0
        }
    
    def get_failed_jobs(self) -> List[Dict[str, Any]]:
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                id, file_hash, file_name, file_type, status, 
                row_count, error_message, created_at, completed_at, retry_path, attempts
            FROM jobs
            WHERE status = 'failed'
            ORDER BY created_at DESC
        """)
        
        rows = cursor.fetchall()
        conn.close()
        
        return [{
            'id': row[0],
            'file_hash': row[1],
            'file_name': row[2],
            'file_type': row[3],
            'status': row[4],
            'row_count': row[5],
            'error_message': row[6],
            'created_at': row[7],
            'completed_at': row[8],
            'retry_path': row[9],
            'attempts': row[10]
        } for row in rows]
