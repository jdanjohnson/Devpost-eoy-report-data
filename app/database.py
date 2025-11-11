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
                completed_at TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_file_hash ON jobs(file_hash)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_status ON jobs(status)
        """)
        
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
    
    def log_job_start(self, file_hash: str, file_name: str, file_type: str) -> int:
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO jobs (file_hash, file_name, file_type, status)
                VALUES (?, ?, ?, 'processing')
            """, (file_hash, file_name, file_type))
            
            job_id = cursor.lastrowid
            conn.commit()
        except sqlite3.IntegrityError:
            cursor.execute("""
                UPDATE jobs 
                SET status = 'processing', error_message = NULL
                WHERE file_hash = ?
            """, (file_hash,))
            
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
                completed_at
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
                row_count, error_message, created_at, completed_at
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
                'completed_at': row[8]
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
