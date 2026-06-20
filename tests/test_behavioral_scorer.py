import pytest
from src.behavioral_scorer import BehavioralScorer

def test_score_behavior_active():
    scorer = BehavioralScorer(anchor_date_str="2026-06-19")
    signals = {
        "recruiter_response_rate": 0.90,
        "interview_completion_rate": 0.85,
        "github_activity_score": 75.0,
        "saved_by_recruiters_30d": 10,
        "search_appearance_30d": 120,
        "last_active_date": "2026-06-18" # active yesterday
    }
    res = scorer.score_behavior(signals)
    assert res["decay_multiplier"] > 0.95
    assert res["behavioral_raw_score"] > 50.0

def test_score_behavior_decayed():
    scorer = BehavioralScorer(anchor_date_str="2026-06-19")
    signals = {
        "recruiter_response_rate": 0.90,
        "interview_completion_rate": 0.85,
        "github_activity_score": 75.0,
        "saved_by_recruiters_30d": 10,
        "search_appearance_30d": 120,
        "last_active_date": "2025-06-19" # active 1 year ago -> should decay
    }
    res = scorer.score_behavior(signals)
    assert res["decay_multiplier"] < 0.30
    assert res["behavioral_raw_score"] < 30.0

def test_score_availability():
    scorer = BehavioralScorer()
    flags_verified = {
        "open_to_work_flag": True,
        "verified_email": True,
        "verified_phone": True,
        "linkedin_connected": True
    }
    res_verified = scorer.score_availability(flags_verified)
    assert res_verified["availability_raw_score"] == 100.0

    flags_unverified = {
        "open_to_work_flag": False,
        "verified_email": False,
        "verified_phone": False,
        "linkedin_connected": False
    }
    res_unverified = scorer.score_availability(flags_unverified)
    assert res_unverified["availability_raw_score"] == 10.0 # Base minimum open_to_work=False gives 0.1
