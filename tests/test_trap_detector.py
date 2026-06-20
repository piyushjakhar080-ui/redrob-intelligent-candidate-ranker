import pytest
from src.trap_detector import TrapDetector

def test_detect_keyword_stuffer():
    detector = TrapDetector()
    # Case range: excess skills (> 30)
    huge_skills = [f"skill_{i}" for i in range(35)]
    is_trap, reason = detector.detect_keyword_stuffer(huge_skills, [])
    assert is_trap == True
    assert "Excessive" in reason

    # Case range: unsupported skills density
    skills = ["kubernetes", "docker", "recommender", "elasticsearch", "pytorch", "solr", "neural networks"]
    experiences = [
        {"title": "Clerk", "description": "Checked books in catalog and helped customers move shelves."}
    ]
    is_trap, reason = detector.detect_keyword_stuffer(skills, experiences)
    # 0 match of skills inside experiences
    assert is_trap == True
    assert "Unsupported" in reason

def test_detect_title_contradiction():
    detector = TrapDetector()
    # Case: senior title with < 2.5 years of experience
    experiences = [
        {"title": "Principal Staff Engineer", "start_date": "2025-01", "end_date": "2025-06"}
    ]
    is_trap, reason = detector.detect_title_contradiction(experiences)
    assert is_trap == True
    assert " contradictions" in reason or "Title Contradiction" in reason
