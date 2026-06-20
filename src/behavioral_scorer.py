from datetime import datetime
from typing import Dict, Any, Optional
from src.utils import parse_date, compute_exponential_decay, normalize_score

class BehavioralScorer:
    def __init__(self, anchor_date_str: str = "2026-06-19"):
        self.anchor_date = parse_date(anchor_date_str)
        
    def score_behavior(self, signals: Dict[str, Any]) -> Dict[str, Any]:
        """
        Scores candidate portal interactions and behavioral engagement (20% weight):
        - recruiter_response_rate (0-1) => weight: 25%
        - interview_completion_rate (0-1) => weight: 25%
        - github_activity_score (0-100) => weight: 20%
        - saved_by_recruiters_30d => weight: 15% (norm-capped at 40)
        - search_appearance_30d => weight: 15% (norm-capped at 300)
        
        Applies an exponential half-life decay multiplier based on the last active date.
        """
        # Extract signals with friendly default values
        rec_rate = float(signals.get("recruiter_response_rate", 0.5))
        int_rate = float(signals.get("interview_completion_rate", 0.5))
        github_score = float(signals.get("github_activity_score", 0.0))
        saved_30d = float(signals.get("saved_by_recruiters_30d", 0))
        search_30d = float(signals.get("search_appearance_30d", 0))
        
        last_active_str = signals.get("last_active_date")
        last_active_dt = parse_date(last_active_str)
        
        # Calculate days inactive relative to the timeline anchor
        delta_days = (self.anchor_date - last_active_dt).days
        days_inactive = max(0.0, float(delta_days))
        
        # Activity Decay (180 days half-life ensures gentle decay)
        decay_multiplier = compute_exponential_decay(days_inactive, half_life_days=180.0)
        
        # Base scores normalization
        norm_github = normalize_score(github_score, 0.0, 100.0)
        norm_saved = normalize_score(saved_30d, 0.0, 40.0)
        norm_search = normalize_score(search_30d, 0.0, 300.0)
        
        # Integrate weights
        weighted_score = (
            rec_rate * 0.25 +
            int_rate * 0.25 +
            norm_github * 0.20 +
            norm_saved * 0.15 +
            norm_search * 0.15
        ) * 100.0
        
        # Apply inactivity decay
        final_behavioral_score = weighted_score * decay_multiplier
        
        return {
            "recruiter_response_rate_score": rec_rate * 100.0,
            "interview_completion_rate_score": int_rate * 100.0,
            "github_score_normalized": norm_github * 100.0,
            "saved_by_recruiters_normalized": norm_saved * 100.0,
            "search_appearance_normalized": norm_search * 100.0,
            "days_inactive": days_inactive,
            "decay_multiplier": decay_multiplier,
            "behavioral_raw_score": final_behavioral_score
        }
        
    def score_availability(self, flags: Dict[str, Any]) -> Dict[str, Any]:
        """
        Scores availability signals (5% overall score weight):
        - open_to_work_flag (Boolean) => weight: 40%
        - verified_email (Boolean) => weight: 20%
        - verified_phone (Boolean) => weight: 20%
        - linkedin_connected (Boolean) => weight: 20%
        """
        open_to_work = bool(flags.get("open_to_work_flag", False))
        v_email = bool(flags.get("verified_email", False))
        v_phone = bool(flags.get("verified_phone", False))
        li_conn = bool(flags.get("linkedin_connected", False))
        
        weighted_score = (
            (0.4 if open_to_work else 0.1) +
            (0.2 if v_email else 0.0) +
            (0.2 if v_phone else 0.0) +
            (0.2 if li_conn else 0.0)
        ) * 100.0
        
        return {
            "open_to_work_flag": open_to_work,
            "verified_email": v_email,
            "verified_phone": v_phone,
            "linkedin_connected": li_conn,
            "availability_raw_score": weighted_score
        }
