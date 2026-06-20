import heapq
from typing import Generator, Dict, Any, List, Tuple
from src.candidate_analyzer import CandidateAnalyzer
from src.behavioral_scorer import BehavioralScorer
from src.trap_detector import TrapDetector

class CandidateRanker:
    def __init__(self, job_description_text: str = "", anchor_date_str: str = "2026-06-19"):
        self.analyzer = CandidateAnalyzer(job_description_text)
        self.scorer = BehavioralScorer(anchor_date_str)
        self.trap_detector = TrapDetector()
        
        # Performance/analytics counters
        self.total_processed = 0
        self.trap_counts = {
            "Keyword Stuffer": 0,
            "Honeypot": 0,
            "Behavioral Twin": 0,
            "Title Contradiction": 0
        }
        self.hidden_star_count = 0

    def calculate_candidate_score(self, candidate: Dict[str, Any]) -> Dict[str, Any]:
        """
        Orchestrates full candidate assessment across four scoring components,
        attributing anti-trap penalties and hidden-star search relevance boosts.
        
        Final Score = Career(45%) + Domain(30%) + Behavior(20%) + Availability(5%) - Penalties + Boosts
        """
        candidate_id = str(candidate.get("candidate_id", candidate.get("id", "unknown")))
        skills = candidate.get("skills", [])
        experiences = candidate.get("experiences", [])
        
        # Fetch portal signals
        signals = {
            "recruiter_response_rate": candidate.get("recruiter_response_rate", 0.5),
            "interview_completion_rate": candidate.get("interview_completion_rate", 0.5),
            "github_activity_score": candidate.get("github_activity_score", 0.0),
            "saved_by_recruiters_30d": candidate.get("saved_by_recruiters_30d", 0),
            "search_appearance_30d": candidate.get("search_appearance_30d", 0),
            "last_active_date": candidate.get("last_active_date")
        }
        
        # Fetch portal flags
        flags = {
            "open_to_work_flag": candidate.get("open_to_work_flag", False),
            "verified_email": candidate.get("verified_email", False),
            "verified_phone": candidate.get("verified_phone", False),
            "linkedin_connected": candidate.get("linkedin_connected", False)
        }
        
        # Calculate sub-scores
        career_res = self.analyzer.analyze_career_path(experiences)
        domain_res = self.analyzer.analyze_domain_relevance(skills, experiences)
        behavior_res = self.scorer.score_behavior(signals)
        availability_res = self.scorer.score_availability(flags)
        
        career_w = career_res["career_raw_score"] * 0.45
        domain_w = domain_res["domain_raw_score"] * 0.30
        behavior_w = behavior_res["behavioral_raw_score"] * 0.20
        availability_w = availability_res["availability_raw_score"] * 0.05
        
        # Calculate Penalties
        trap_res = self.trap_detector.evaluate_all_traps(candidate_id, skills, experiences, signals, flags)
        penalty_deductions = trap_res["total_trap_penalty"]
        
        # Log traps for reporting
        for trap_detail in trap_res["applied_traps"]:
            t_name = trap_detail["trap"]
            self.trap_counts[t_name] += 1
            
        # Calculate Boosts
        is_hidden_star = self.analyzer.detect_hidden_star(skills, experiences)
        boost_addition = 25.0 if is_hidden_star else 0.0
        if is_hidden_star:
            self.hidden_star_count += 1
            
        # Compile total score
        final_score = career_w + domain_w + behavior_w + availability_w - penalty_deductions + boost_addition
        # Safeguard lower and upper bound of candidate scores
        final_score = max(0.0, min(100.0, round(final_score, 2)))
        
        # Build friendly concise reasoning
        reasons = []
        if is_hidden_star:
            reasons.append("Spotlighted Search Relevance Hidden Star (+25 pts).")
        if trap_res["has_traps"]:
            trap_names = [t["trap"] for t in trap_res["applied_traps"]]
            reasons.append(f"Triggered anti-cheat safeguards: {', '.join(trap_names)} (-{penalty_deductions:.0f} pts).")
        if career_res["total_experience_years"] > 5.0 and career_res["progression_score"] > 0.7:
            reasons.append("Exceptional upward senior career progression.")
        if domain_res["domain_raw_score"] > 80.0:
            reasons.append("Top-tier specialized IR and production-ML relevance.")
        if behavior_res["behavioral_raw_score"] > 80.0:
            reasons.append("Exceptional active candidate engagement signals.")
            
        if not reasons:
            reasons.append("Solid career profiles matching baseline specifications.")
            
        reasoning_summary = " ".join(reasons)
        
        # Return complete breakdown
        return {
            "candidate_id": candidate_id,
            "final_score": final_score,
            "reasoning": reasoning_summary,
            "breakdown": {
                "career_score": round(career_w, 2),
                "domain_score": round(domain_w, 2),
                "behavioral_score": round(behavior_w, 1),
                "availability_score": round(availability_w, 2),
                "penalties": penalty_deductions,
                "boosts": boost_addition,
                "is_hidden_star": is_hidden_star,
                "is_trap": trap_res["has_traps"]
            }
        }

    def process_and_rank(self, candidate_stream: Generator[Dict[str, Any], None, None], top_k: int = 100) -> List[Dict[str, Any]]:
        """
        Processes a pipeline of candidate profile records using a low-footprint Top-K min-heap.
        Maintains O(K) memory overhead and is capable of ranking 100,000 candidates in seconds.
        """
        # Store min-heap of size top_k.
        # We store elements as (final_score, candidate_id, evaluated_dict)
        # Python's heapq is a min-heap, so the lowest score of top-k sits at the root.
        top_k_heap = []
        self.total_processed = 0
        
        for candidate in candidate_stream:
            self.total_processed += 1
            evaluated = self.calculate_candidate_score(candidate)
            
            score_tuple = (evaluated["final_score"], evaluated["candidate_id"], evaluated)
            
            if len(top_k_heap) < top_k:
                heapq.heappush(top_k_heap, score_tuple)
            else:
                # Compare against root (worst score in our top_k currently)
                if evaluated["final_score"] > top_k_heap[0][0]:
                    heapq.heapreplace(top_k_heap, score_tuple)
                    
        # Extract, sort descending, and return results
        sorted_results = []
        while top_k_heap:
            _, _, evaluated = heapq.heappop(top_k_heap)
            sorted_results.append(evaluated)
            
        # Return highest score first
        return sorted_results[::-1]
