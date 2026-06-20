import pytest
from src.ranker import CandidateRanker

def test_ranker_heap_top_k():
    ranker = CandidateRanker(job_description_text="Elasticsearch Search relevance engineer")
    
    # 5 dummy candidates
    candidates = [
        {
            "candidate_id": f"c_{i}",
            "skills": ["Elasticsearch", "search relevance"],
            "experiences": [
                {"company": "Google", "title": "RE Engineer", "start_date": "2020-01", "end_date": "Present", "description": "search engineer"}
            ],
            "recruiter_response_rate": 0.8 + (i * 0.03),
            "interview_completion_rate": 0.8 + (i * 0.03),
            "github_activity_score": 50.0 + (i * 5.0),
            "saved_by_recruiters_30d": 10 + i,
            "search_appearance_30d": 100 + (i * 20),
            "last_active_date": "2026-06-18",
            "open_to_work_flag": True, "verified_email": True, "verified_phone": True, "linkedin_connected": True
        }
        for i in range(5)
    ]
    
    # Process with top_k = 2
    top_2 = ranker.process_and_rank(candidates, top_k=2)
    assert len(top_2) == 2
    # Ensure sorted order descending
    assert top_2[0]["final_score"] >= top_2[1]["final_score"]
    # Best candidate should be c_4
    assert top_2[0]["candidate_id"] == "c_4"
