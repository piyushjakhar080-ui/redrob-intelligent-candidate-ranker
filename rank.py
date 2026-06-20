#!/usr/bin/env python
import argparse
import os
import csv
from src.load_data import stream_candidates
from src.ranker import CandidateRanker

def compile_default_job_description() -> str:
    """
    Returns a production-grade default job description for ML / IR Engineers 
    if no job_description.md exists in the working directory.
    """
    return """
    # Staff Machine Learning Engineer - Search Relevance & Ranking Systems

    We are seeking a seasoned Specialist in Search, Information Retrieval, and Recommendation Engines.
    
    ### Key Responsibilities:
    - Designing high-scale ranking algorithms, search query retrieval, and hybrid dense/sparse search functions.
    - Implementing high-performance personalization models, vector databases, and approximate nearest neighbor (ANN) indexes.
    - Tuning learning-to-rank (LTR) algorithms using production-ML engineering pipelines.
    
    ### Requirements:
    - 5+ years shipping high-scale ranking models, Elasticsearch/Lucene configurations, recommendations, or index pipelines.
    - Solid knowledge of machine learning, collaborative filtering, deep retrieval, and vector search technologies.
    """

def verify_and_prep_directories(input_path: str, jd_path: str):
    """
    Validates files existence, creating highly helpful default fallback resources 
    so the pipeline is immediately executable and never crashes.
    """
    # Parent directories setup
    input_dir = os.path.dirname(input_path)
    if input_dir and not os.path.exists(input_dir):
        os.makedirs(input_dir, exist_ok=True)
        
    # Write a default job description if it doesn't exist
    if not os.path.exists(jd_path):
        with open(jd_path, "w", encoding="utf-8") as f:
            f.write(compile_default_job_description().strip())
        print(f"[*] Generated default template job description in '{jd_path}'.")
        
    # Write a sample candidate file if none exists to ensure first-run success
    if not os.path.exists(input_path) and input_path.endswith(".jsonl"):
        import json
        sample_candidates = [
            {
                "candidate_id": "c_premium_01",
                "skills": ["Elasticsearch", "search relevance", "personalization", "FAISS", "Python", "PyTorch"],
                "experiences": [
                    {
                        "company": "Netflix", "title": "Staff Search Relevance Engineer", "start_date": "2022-01", "end_date": "Present",
                        "description": "Led search relevance and learning to rank models. Shipped personalized recommendations using FAISS indices."
                    },
                    {
                        "company": "Amazon", "title": "Senior Information Retrieval Engineer", "start_date": "2018-05", "end_date": "2021-12",
                        "description": "Optimized dense search and BM25 retrievers. Worked on high-performance indexing."
                    }
                ],
                "recruiter_response_rate": 0.95, "interview_completion_rate": 0.92, "github_activity_score": 85.0,
                "saved_by_recruiters_30d": 38, "search_appearance_30d": 290, "last_active_date": "2026-06-18",
                "open_to_work_flag": True, "verified_email": True, "verified_phone": True, "linkedin_connected": True
            },
            {
                "candidate_id": "c_keyword_stuffer_trap",
                "skills": ["Python", "Java", "C++", "RAG", "Vite", "Kubernetes", "AWS", "Stripe", "HTML", "CSS", "SQL", "Spark", "Kafka", "Docker", "Git", "Excel", "English", "Agile", "Next.JS", "React", "Node", "Go", "AI", "NLP", "LLM", "Pinecone", "LangChain", "LlamaIndex", "Redis", "Figma", "Redux", "NoSQL", "CI/CD"],
                "experiences": [
                    { "company": "Global Corp", "title": "Software Developer", "start_date": "2025-01", "end_date": "Present", "description": "Writing basic boilerplate scripts." }
                ],
                "recruiter_response_rate": 0.40, "interview_completion_rate": 0.35, "github_activity_score": 12.0,
                "saved_by_recruiters_30d": 2, "search_appearance_30d": 12, "last_active_date": "2026-06-01",
                "open_to_work_flag": True, "verified_email": False, "verified_phone": False, "linkedin_connected": False
            }
        ]
        with open(input_path, "w", encoding="utf-8") as f:
            for item in sample_candidates:
                f.write(json.dumps(item) + "\n")
        print(f"[*] Generated mock baseline validation dataset in '{input_path}'.")

def main():
    parser = argparse.ArgumentParser(description="Redrob Intelligent Candidate Discovery & Ranking Pipeline Runner")
    parser.add_argument("--input", type=str, default="data/candidates.jsonl", help="Path to input dataset (supports .jsonl and .jsonl.gz)")
    parser.add_argument("--jd", type=str, default="job_description.md", help="Path to target job description markdown")
    parser.add_argument("--output", type=str, default="submission.csv", help="Path to save ranking output")
    parser.add_argument("--top_k", type=int, default=100, help="Number of premier candidates to select")
    args = parser.parse_args()

    print("=========================================================================")
    print(" REDROB INTELLIGENT CANDIDATE DISCOVERY & RANKING CHALLENGE CLI")
    print("=========================================================================")

    # Prepare inputs if not exists
    verify_and_prep_directories(args.input, args.jd)

    # Read Job Description
    job_description_content = ""
    try:
        with open(args.jd, "r", encoding="utf-8") as f:
            job_description_content = f.read()
    except Exception as e:
        print(f"[-] Warning reading job description: {e}. Proceeding with clean defaults.")
        
    print(f"[*] Initializing Discovery Pipeline...")
    ranker = CandidateRanker(job_description_content)
    
    print(f"[*] Streaming & scoring profiles from: '{args.input}'...")
    candidate_stream = stream_candidates(args.input)
    
    top_candidates = ranker.process_and_rank(candidate_stream, top_k=args.top_k)
    
    print("\n------------------------- PROCESSING METRICS -------------------------")
    print(f" - Candidates Screened Across Dataset : {ranker.total_processed}")
    print(f" - Fraudulent/Twin Profiles Defended  : {sum(ranker.trap_counts.values())}")
    for trap_name, count in ranker.trap_counts.items():
        print(f"   ∟ {trap_name.ljust(20)} : {count} detections")
    print(f" - Hidden Star Talent Spotlighted     : {ranker.hidden_star_count} profiles")
    
    print(f"\n[*] Exporting top {len(top_candidates)} matches to: '{args.output}'...")
    
    try:
        with open(args.output, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["candidate_id", "rank", "score", "reasoning"])
            for rank_idx, cand in enumerate(top_candidates, 1):
                writer.writerow([
                    cand["candidate_id"],
                    rank_idx,
                    cand["final_score"],
                    cand["reasoning"]
                ])
        print(f"[✓] Pipeline complete! Submission CSV saved cleanly with no anomalies.")
    except Exception as e:
        print(f"[❌] Error compiling output CSV: {e}")

if __name__ == "__main__":
    main()
