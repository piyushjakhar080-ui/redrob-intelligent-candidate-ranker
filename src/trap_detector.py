import re
from typing import Dict, Any, List, Set, Tuple
from src.utils import generate_fingerprint, clean_and_split_skills, calculate_duration_months

ACADEMIC_BUZZWORDS = {
    "thesis", "dissertation", "academic paper", "simulation model", "theoretic framework",
    "pure science", "classroom assignment", "proof of concept", "professor sandbox", "syllabus"
}

class TrapDetector:
    def __init__(self):
        # Store fingerprints to detect Behavioral Twins O(1) in subsequent streaming steps
        self.seen_experience_fingerprints: Set[str] = set()
        
    def detect_keyword_stuffer(self, skills: List[str], experiences: List[Dict[str, Any]]) -> Tuple[bool, str]:
        """
        Keyword Stuffers Warning (-45 points):
        Triggers if candidate showcases an excessive list of skills (> 30 skills) OR if more than 60% 
        of listed skills find absolutely zero substring match across their work history descriptions.
        """
        all_skills = clean_and_split_skills(skills)
        if len(all_skills) > 30:
            return True, f"Excessive total skill count ({len(all_skills)}) exceeds threshold of 30."
            
        if not all_skills:
            return False, ""
            
        # Combine experiences texts
        history_text = " ".join([
            f"{job.get('title', '')} {job.get('description', '')}" 
            for job in experiences
        ]).lower()
        
        unsupported_count = 0
        for skill in all_skills:
            # Check if skill or standard variation is found in job history
            if skill not in history_text:
                unsupported_count += 1
                
        unsupported_pct = unsupported_count / len(all_skills)
        if len(all_skills) >= 10 and unsupported_pct > 0.65:
            return True, f"Unsupported skills density: {unsupported_pct:.1%} of listed skills have no backing in work history."
            
        return False, ""
        
    def detect_honeypot(self, skills: List[str], experiences: List[Dict[str, Any]], signals: Dict[str, Any], flags: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Honeypot Warning (-80 points):
        Bypasses standard matching via high profile buzzwords without verified identity details,
        having low portal activities (github < 15), representing non-genuine profiles.
        """
        all_skills = set(clean_and_split_skills(skills))
        
        # Combine resume content
        resume_text = " ".join([
            f"{job.get('title', '')} {job.get('description', '')}" 
            for job in experiences
        ]).lower() + " " + " ".join(all_skills)
        
        # Count academic/theoretical words
        academic_hits = sum(1 for word in ACADEMIC_BUZZWORDS if word in resume_text)
        
        # Verify identity factors
        identity_verified = bool(flags.get("verified_email", False)) or bool(flags.get("verified_phone", False))
        github_score = float(signals.get("github_activity_score", 0))
        interview_rate = float(signals.get("interview_completion_rate", 0))
        
        # Criteria match
        if academic_hits >= 2 and not identity_verified and github_score < 15.0 and interview_rate < 0.2:
            return True, f"Honeypot signature: {academic_hits} academic buzzwords, zero identity verification, low activity."
            
        return False, ""
        
    def check_behavioral_twin(self, candidate_id: str, experiences: List[Dict[str, Any]]) -> Tuple[bool, str]:
        """
        Behavioral Twins Warning (-30 points):
        Identifies bots or duplicate templates by hashing the sequence of past roles, companies, and content.
        """
        if not experiences:
            return False, ""
            
        # Compile unique structural details of candidate experiences
        signature_items = []
        for job in experiences:
            company = str(job.get("company", "")).strip().lower()
            title = str(job.get("title", "")).strip().lower()
            desc = str(job.get("description", "")).strip().lower()
            signature_items.append(f"{company}:{title}:{desc[:100]}")
            
        signature_text = "||".join(signature_items)
        if not signature_text:
            return False, ""
            
        fingerprint = generate_fingerprint(signature_text)
        
        if fingerprint in self.seen_experience_fingerprints:
            return True, "Duplicate profile footprint: exact job sequence match found in records."
            
        self.seen_experience_fingerprints.add(fingerprint)
        return False, ""
        
    def detect_title_contradiction(self, experiences: List[Dict[str, Any]]) -> Tuple[bool, str]:
        """
        Title Contradictions Warning (-35 points):
        1. Senior/Lead role with less than 2.5 years of experience total.
        2. First-ever held job in career history starts with a 'Lead' or 'VP' title.
        """
        if not experiences:
            return False, ""
            
        # Calculate total experience
        total_months = sum(calculate_duration_months(j.get("start_date"), j.get("end_date")) for j in experiences)
        total_years = total_months / 12.0
        
        # Check titles
        junior_experience_limit = 2.5
        senior_titles_found = []
        for job in experiences:
            title = str(job.get("title", "")).lower()
            if any(t in title for t in ["senior", "lead", "principal", "manager", "director", "vp", "chief", "cto"]):
                senior_titles_found.append(job.get("title"))
                
        if total_years < junior_experience_limit and len(senior_titles_found) > 0:
            return True, f"Title Contradiction: Senior title(s) {senior_titles_found} held with only {total_years:.1f} years total experience."
            
        # Chronological sort to check the starting job
        parsed_jobs = []
        for job in experiences:
            # Parse start date safely to sort
            from src.utils import parse_date
            parsed_jobs.append({
                "title": str(job.get("title", "")).strip(),
                "start": parse_date(job.get("start_date"))
            })
            
        parsed_jobs.sort(key=lambda x: x["start"])
        if parsed_jobs:
            first_title = parsed_jobs[0]["title"].lower()
            # If the first job is Lead or higher
            if any(t in first_title for t in ["lead", "principal", "director", "vp", "chief", "cto"]):
                # Allow founder or co-founder exceptions
                if "founder" not in first_title:
                    return True, f"First-ever role title contradiction: Started career directly as a '{parsed_jobs[0]['title']}'."
                    
        return False, ""
        
    def evaluate_all_traps(self, candidate_id: str, skills: List[str], experiences: List[Dict[str, Any]], signals: Dict[str, Any], flags: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processes candidate against all four anti-trap systems.
        """
        kw_stuffer, kw_reason = self.detect_keyword_stuffer(skills, experiences)
        honeypot, hp_reason = self.detect_honeypot(skills, experiences, signals, flags)
        twin, twin_reason = self.check_behavioral_twin(candidate_id, experiences)
        contradiction, contra_reason = self.detect_title_contradiction(experiences)
        
        penalties = 0.0
        applied_traps = []
        
        if kw_stuffer:
            penalties += 45.0
            applied_traps.append({"trap": "Keyword Stuffer", "penalty": -45.0, "reason": kw_reason})
        if honeypot:
            penalties += 80.0
            applied_traps.append({"trap": "Honeypot", "penalty": -80.0, "reason": hp_reason})
        if twin:
            penalties += 30.0
            applied_traps.append({"trap": "Behavioral Twin", "penalty": -30.0, "reason": twin_reason})
        if contradiction:
            penalties += 35.0
            applied_traps.append({"trap": "Title Contradiction", "penalty": -35.0, "reason": contra_reason})
            
        return {
            "has_traps": len(applied_traps) > 0,
            "total_trap_penalty": penalties,
            "applied_traps": applied_traps
        }
