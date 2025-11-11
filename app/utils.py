import json
import hashlib
import re
from typing import Dict, List, Optional
import os


def load_synonyms(synonyms_path: str = "./synonyms.json") -> Dict[str, Dict[str, str]]:
    if not os.path.exists(synonyms_path):
        return {"technologies": {}, "skills": {}}
    
    with open(synonyms_path, 'r') as f:
        return json.load(f)


def normalize_token(token: str, synonyms: Dict[str, str]) -> str:
    if not token:
        return ""
    
    token = token.strip().lower()
    
    token = re.sub(r'^[^\w\s]+|[^\w\s]+$', '', token)
    
    if token in synonyms:
        return synonyms[token]
    
    return token


def tokenize_field(value: str, delimiter: str = ',') -> List[str]:
    if not value or pd.isna(value):
        return []
    
    if not isinstance(value, str):
        value = str(value)
    
    tokens = value.split(delimiter)
    
    cleaned_tokens = []
    for token in tokens:
        token = token.strip()
        if token:
            cleaned_tokens.append(token)
    
    return cleaned_tokens


def compute_file_hash(file_path: str) -> str:
    sha256_hash = hashlib.sha256()
    
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    
    return sha256_hash.hexdigest()


def validate_excel_file(file_path: str) -> bool:
    if not os.path.exists(file_path):
        return False
    
    if not file_path.endswith('.xlsx'):
        return False
    
    file_size = os.path.getsize(file_path)
    if file_size == 0:
        return False
    
    return True


def clean_string(value: str) -> str:
    if not value or pd.isna(value):
        return ""
    
    if not isinstance(value, str):
        value = str(value)
    
    value = value.strip()
    
    value = re.sub(r'\s+', ' ', value)
    
    return value


def parse_datetime(value: str) -> Optional[str]:
    if not value or pd.isna(value):
        return None
    
    try:
        import pandas as pd
        dt = pd.to_datetime(value)
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    except:
        return None


import pandas as pd
