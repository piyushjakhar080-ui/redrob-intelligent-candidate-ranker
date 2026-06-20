import re
import hashlib
from datetime import datetime
from typing import Any, Dict, Optional, Union

def parse_date(date_str: Optional[str], default_year: int = 2026) -> datetime:
    """
    Parses a variety of date formats safely, supporting string styles like '2023-01-01', 
    'Present', '05/2018', or timestamps.
    """
    if not date_str:
        return datetime(default_year, 6, 19)
    
    date_str_clean = str(date_str).strip()
    if date_str_clean.lower() in ["present", "current", "now", "today", ""]:
        return datetime(2026, 6, 19) # Anchored to the current hackathon timeline
    
    # Try common formats
    for fmt in ("%Y-%m-%d", "%Y-%m", "%m/%Y", "%Y"):
        try:
            return datetime.strptime(date_str_clean, fmt)
        except ValueError:
            pass
            
    # Try extracting via regex digits
    digits = re.findall(r"\d+", date_str_clean)
    if len(digits) >= 2:
        # Check if four-digit year is first or second
        if len(digits[0]) == 4:
            year, month = int(digits[0]), int(digits[1])
        elif len(digits[1]) == 4:
            month, year = int(digits[0]), int(digits[1])
        else:
            year, month = 2000 + int(digits[1]), int(digits[0])
        month = max(1, min(12, month))
        return datetime(year, month, 1)
    elif len(digits) == 1 and len(digits[0]) == 4:
        return datetime(int(digits[0]), 1, 1)
        
    return datetime(default_year, 6, 19)

def calculate_duration_months(start_date_str: Optional[str], end_date_str: Optional[str]) -> float:
    """
    Calculates duration between two date strings in months.
    """
    start = parse_date(start_date_str)
    end = parse_date(end_date_str)
    
    if start > end:
        # Swap if reversed
        start, end = end, start
        
    delta_years = end.year - start.year
    delta_months = end.month - start.month
    total_months = delta_years * 12 + delta_months
    return max(0.0, float(total_months))

def compute_exponential_decay(days: float, half_life_days: float = 90.0) -> float:
    """
    Computes exponential decay for activity metrics.
    Formula: 2^(-days / half_life)
    """
    if days < 0:
        return 1.0
    return float(2.0 ** (-days / half_life_days))

def normalize_score(value: float, min_val: float, max_val: float) -> float:
    """
    Clamps and scales value between 0.0 and 1.0.
    """
    if max_val <= min_val:
        return 0.0
    clamped = max(min_val, min(max_val, value))
    return (clamped - min_val) / (max_val - min_val)

def generate_fingerprint(text: str) -> str:
    """
    Generates a normalized MD5 fingerprint of work experience text to detect behavioral twins.
    Cleans punctuation, whitespaces, and returns MD5 hash.
    """
    cleaned = re.sub(r"[^a-zA-Z0-9]", "", text).lower()
    return hashlib.md5(cleaned.encode("utf-8")).hexdigest()

def clean_and_split_skills(skills_data: Union[str, list]) -> list:
    """
    Safely converts skills raw field to a clean lowercased list of skills.
    """
    if isinstance(skills_data, list):
        return [str(s).strip().lower() for s in skills_data if s]
    if isinstance(skills_data, str):
        # Could be comma-separated or semicolon-separated
        delimiters = [",", ";", "|"]
        pattern = "|".join(map(re.escape, delimiters))
        split_skills = re.split(pattern, skills_data)
        return [s.strip().lower() for s in split_skills if s.strip()]
    return []
