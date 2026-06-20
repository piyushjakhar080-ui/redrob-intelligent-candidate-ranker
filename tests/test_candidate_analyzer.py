import pytest
from src.candidate_analyzer import CandidateAnalyzer

def test_get_role_level():
    analyzer = CandidateAnalyzer()
    assert analyzer.get_role_level("VP Engineering") == 4.0
    assert analyzer.get_role_level("Lead Machine Learning Developer") == 3.5
    assert analyzer.get_role_level("Senior Software Engineer") == 3.0
    assert analyzer.get_role_level("Software Engineer") == 2.0
    assert analyzer.get_role_level("Junior Developer") == 1.0
    assert analyzer.get_role_level("Unmapped Role Title") == 2.0 # default

def test_analyze_empty_career_path():
    analyzer = CandidateAnalyzer()
    res = analyzer.analyze_career_path([])
    assert res["career_raw_score"] == 0.0
    assert res["total_experience_years"] == 0.0

def test_analyze_career_path():
    analyzer = CandidateAnalyzer()
    experiences = [
        {"company": "Google", "title": "Software Engineer", "start_date": "2020-01", "end_date": "2022-01"},
        {"company": "Meta", "title": "Senior Machine Learning Engineer", "start_date": "2022-01", "end_date": "Present"}
    ]
    res = analyzer.analyze_career_path(experiences)
    assert res["total_experience_years"] > 5.0
    # Career progression from Engineer to Senior
    assert res["progression_score"] > 0.5
    # High tier company authority
    assert res["company_authority_score"] == 1.0

def test_detect_hidden_star():
    analyzer = CandidateAnalyzer()
    # Hidden Star: Mention target without traps
    skills = ["Elasticsearch", "Python"]
    experiences = [{"title": "Search Engineer", "description": "Worked on ranking and retrieval relevance models."}]
    assert analyzer.detect_hidden_star(skills, experiences) == True

    # Includes traps: Negates Hidden Star
    skills_with_trap = ["Elasticsearch", "Pinecone", "RAG"]
    assert analyzer.detect_hidden_star(skills_with_trap, experiences) == False
