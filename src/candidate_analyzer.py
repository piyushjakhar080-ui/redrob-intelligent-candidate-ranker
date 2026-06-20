import re
from datetime import datetime
from typing import Dict, Any, List, Tuple
from src.utils import calculate_duration_months, parse_date, clean_and_split_skills

# Company Authority tiers
TIER_1_COMPANIES = {
    "google", "meta", "openai", "netflix", "apple", "amazon", "microsoft", 
    "stripe", "nvidia", "uber", "airbnb", "anthropic", "cohere", "databricks"
}
TIER_2_COMPANIES = {
    "snowflake", "confluent", "elastic", "mongodb", "replit", "github", "gitlab",
    "scale ai", "hugging face", "linear", "vercel", "supabase", "midjourney"
}

# Role Level mappings
ROLE_LEVELS = [
    (re.compile(r"\b(vp|vice president|director|head|chief|cto|cio|cfo|ceo|founder|co-founder)\b", re.I), 4),
    (re.compile(r"\b(lead|principal|staff|manager|mgr)\b", re.I), 3.5),
    (re.compile(r"\b(senior|sr|architect|expert)\b", re.I), 3.0),
    (re.compile(r"\b(associate|mid|developer|engineer|analyst|specialist|practitioner|scientist)\b", re.I), 2.0),
    (re.compile(r"\b(junior|jr|intern|trainee|apprentice|co-op)\b", re.I), 1.0)
]

DOMAIN_KEYWORDS = {
    "ai_engineering": ["ai engineer", "ai engineering", "generative ai", "genai", "prompt engineering"],
    "machine_learning": ["machine learning", "ml", "deep learning", "neural network", "pytorch", "tensorflow"],
    "nlp": ["nlp", "natural language", "transformers", "bert", "gpt", "tokenization", "spacy"],
    "llm": ["llm", "large language model", "fine tuning", "llama3", "mistral", "claude", "agentic"],
    "retrieval": ["retrieval", "retriever", "dense retrieval", "sparse retrieval", "hybrid search"],
    "search": ["search", "information retrieval", "bm25", "inverted index", "search relevance", "lucene"],
    "ranking": ["ranking", "learning to rank", "ltr", "re-ranking", "reranker", "ndcg"],
    "recommendation_systems": ["recommendation", "recommender", "collaborative filtering", "personalization"],
    "vector_databases": ["vector database", "milvus", "qdrant", "weaviate", "chromadb", "faiss"],
    "production_ml": ["mlops", "production ml", "triton", "onnx", "kubeflow", "mlflow", "model deployment"]
}

HIDDEN_STAR_TARGETS = {
    "retrieval", "ranking", "search relevance", "recommendation engines", 
    "personalization", "ann search", "faiss", "elasticsearch", "lucene", "opensearch"
}
HIDDEN_STAR_TRAPS = {
    "rag", "langchain", "pinecone", "llamaindex"
}

class CandidateAnalyzer:
    def __init__(self, job_description_text: str = ""):
        self.job_description = job_description_text.lower()
        
    def get_role_level(self, title: str) -> float:
        """
        Calculates numerical hierarchy level of a given job title.
        Ranges from 1.0 (Junior/Intern) to 4.0 (Executive/Founder).
        """
        title_lower = title.lower()
        for pattern, score in ROLE_LEVELS:
            if pattern.search(title_lower):
                return score
        return 2.0 # Default mid

    def analyze_career_path(self, experiences: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyzes 5 dimensions of Career Intelligence (45% total score weight):
        1. Job Duration Density (average length per job)
        2. Career Progression (monotonic level increase)
        3. Company Authority (past company ranking)
        4. Career Stability (employment consistency, gaps)
        5. Promotion Velocity (speed of vertical steps)
        """
        if not experiences:
            return {
                "duration_density_score": 0.0,
                "progression_score": 0.0,
                "company_authority_score": 0.0,
                "stability_score": 0.0,
                "promotion_velocity_score": 0.0,
                "total_experience_years": 0.0,
                "career_raw_score": 0.0
            }
            
        # Parse dates and durations
        parsed_jobs = []
        total_months = 0.0
        company_score_sum = 0.0
        
        for job in experiences:
            comp = str(job.get("company", "")).strip().lower()
            title = str(job.get("title", "")).strip()
            start = job.get("start_date")
            end = job.get("end_date")
            desc = str(job.get("description", "")).strip()
            
            dur = calculate_duration_months(start, end)
            total_months += dur
            
            # Company authority
            comp_score = 0.4 # base
            if any(tc in comp for tc in TIER_1_COMPANIES):
                comp_score = 1.0
            elif any(tc in comp for tc in TIER_2_COMPANIES):
                comp_score = 0.8
            company_score_sum += comp_score
            
            level = self.get_role_level(title)
            start_dt = parse_date(start)
            end_dt = parse_date(end)
            
            parsed_jobs.append({
                "company": comp,
                "title": title,
                "duration": dur,
                "level": level,
                "start": start_dt,
                "end": end_dt,
                "desc": desc
            })
            
        # Sort jobs chronologically (oldest first)
        parsed_jobs.sort(key=lambda x: x["start"])
        num_jobs = len(parsed_jobs)
        
        # 1. Job Duration Density
        # penalize many hyper-short stints (< 12 months), reward stable stays (24-48 months)
        avg_months = total_months / num_jobs if num_jobs > 0 else 0
        if avg_months >= 36:
            duration_density_score = 1.0
        elif avg_months >= 24:
            duration_density_score = 0.9
        elif avg_months >= 15:
            duration_density_score = 0.7
        elif avg_months >= 8:
            duration_density_score = 0.4
        else:
            duration_density_score = 0.15
            
        # 2. Career Progression
        # Compare levels sequentially. Reward increases, penalize downgrades unless logical.
        progression_points = 0
        progression_opportunities = 0
        
        for i in range(1, len(parsed_jobs)):
            prev_level = parsed_jobs[i-1]["level"]
            curr_level = parsed_jobs[i]["level"]
            progression_opportunities += 1
            if curr_level > prev_level:
                progression_points += 1.0
            elif curr_level == prev_level:
                progression_points += 0.5
            else:
                progression_points -= 0.5
                
        progression_score = 0.5 # Default middle score if 1 job
        if progression_opportunities > 0:
            progression_score = max(0.0, min(1.0, (progression_points / progression_opportunities) + 0.5))
            
        # 3. Company Authority
        company_authority_score = company_score_sum / num_jobs if num_jobs > 0 else 0.4
        
        # 4. Career Stability (employment gaps)
        gap_penalty = 0.0
        for i in range(1, len(parsed_jobs)):
            prev_end = parsed_jobs[i-1]["end"]
            curr_start = parsed_jobs[i]["start"]
            if curr_start > prev_end:
                gap_days = (curr_start - prev_end).days
                if gap_days > 180: # gap more than 6 months
                    gap_penalty += min(0.3, (gap_days - 180) / 365)
        stability_score = max(0.1, 1.0 - gap_penalty)
        
        # 5. Promotion Velocity
        # Time it took to hit Sr (lvl >= 3) or Lead (lvl >= 3.5) from start of career
        promotion_velocity_score = 0.5 # neutral default
        total_exp_years = total_months / 12.0
        
        first_start = parsed_jobs[0]["start"]
        hit_sr_or_above_yrs = None
        for job in parsed_jobs:
            if job["level"] >= 3.0:
                hit_sr_or_above_yrs = (job["start"] - first_start).days / 365.25
                break
                
        if hit_sr_or_above_yrs is not None:
            if hit_sr_or_above_yrs <= 2.5:
                promotion_velocity_score = 1.0 # ultra fast
            elif hit_sr_or_above_yrs <= 4.0:
                promotion_velocity_score = 0.85
            elif hit_sr_or_above_yrs <= 6.0:
                promotion_velocity_score = 0.70
            else:
                promotion_velocity_score = 0.50
        else:
            # If they have high exp but never hit Sr, penalize velocity
            if total_exp_years > 6.0:
                promotion_velocity_score = 0.2
            else:
                promotion_velocity_score = 0.5 # young career, neutral
                
        # Combined weighted Career score out of 100 points
        career_raw_score = (
            duration_density_score * 0.25 + 
            progression_score * 0.25 + 
            company_authority_score * 0.20 + 
            stability_score * 0.15 + 
            promotion_velocity_score * 0.15
        ) * 100.0
        
        return {
            "duration_density_score": duration_density_score,
            "progression_score": progression_score,
            "company_authority_score": company_authority_score,
            "稳定性_score": stability_score, # standardizing to clear english stability_score internally
            "stability_score": stability_score,
            "promotion_velocity_score": promotion_velocity_score,
            "total_experience_years": total_exp_years,
            "career_raw_score": career_raw_score
        }

    def analyze_domain_relevance(self, skills: List[str], experiences: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculates Domain Relevance score (30% total score weight):
        Extracts expertise match across work histories and formal skills list.
        Recent roles match carries twice the weighting of older historic roles.
        """
        scores_by_domain = {domain: 0.0 for domain in DOMAIN_KEYWORDS}
        unified_skills_set = set(clean_and_split_skills(skills))
        
        # Analyze skills list matches (base 40% weight of domain score)
        skills_matched = 0
        matched_kw_tracker = {}
        
        for domain, keywords in DOMAIN_KEYWORDS.items():
            matched_kw_tracker[domain] = []
            domain_points = 0.0
            for kw in keywords:
                if kw in unified_skills_set:
                    domain_points += 0.5
                    matched_kw_tracker[domain].append(kw)
            scores_by_domain[domain] += domain_points

        # Sort experiences chronologically to determine recency weights
        sorted_jobs = []
        for job in experiences:
            start = job.get("start_date")
            sorted_jobs.append({
                "title": str(job.get("title", "")).lower(),
                "desc": str(job.get("description", "")).lower(),
                "start_dt": parse_date(start)
            })
        sorted_jobs.sort(key=lambda x: x["start_dt"], reverse=True) # newest first
        
        # Recency Multipliers
        # Newer jobs get higher weight. Job 0 is newest.
        for idx, job in enumerate(sorted_jobs):
            recency_multiplier = 1.0
            if idx == 0:
                recency_multiplier = 1.5
            elif idx == 1:
                recency_multiplier = 1.1
            else:
                recency_multiplier = 0.6
                
            combined_text = f"{job['title']} {job['desc']}"
            
            for domain, keywords in DOMAIN_KEYWORDS.items():
                domain_points = 0.0
                for kw in keywords:
                    count = combined_text.count(kw)
                    if count > 0:
                        domain_points += min(1.5, count * 0.4) * recency_multiplier
                        if kw not in matched_kw_tracker[domain]:
                            matched_kw_tracker[domain].append(kw)
                scores_by_domain[domain] += domain_points
                
        # Total domain match out of 100 points
        raw_sum = sum(scores_by_domain.values())
        # Max domain relevance capacity is 25.0 points of raw summed metrics. Standardize.
        normalized_domain_score = min(100.0, (raw_sum / 15.0) * 100.0)
        
        return {
            "domain_scores": scores_by_domain,
            "matched_keywords": matched_kw_tracker,
            "domain_raw_score": normalized_domain_score
        }

    def detect_hidden_star(self, skills: List[str], experiences: List[Dict[str, Any]]) -> bool:
        """
        Hidden Star Boost (+25 points):
        Spot traditional core intelligence / IR engineering masters who describe deep indexing,
        ranking, personalization and search routing, even if they omit hype buzzwords 
        like RAG, LangChain, Pinecone, or LlamaIndex.
        """
        unified_skills_set = set(clean_and_split_skills(skills))
        
        # Combine all experiences text
        all_exp_text = ""
        for job in experiences:
            all_exp_text += " " + str(job.get("title", "")).lower() + " " + str(job.get("description", "")).lower()
            
        # Combine skills list & experience description
        target_found = False
        for target in HIDDEN_STAR_TARGETS:
            if target in unified_skills_set or target in all_exp_text:
                target_found = True
                break
                
        trap_found = False
        for trap in HIDDEN_STAR_TRAPS:
            if trap in unified_skills_set or trap in all_exp_text:
                trap_found = True
                break
                
        return target_found and not trap_found
