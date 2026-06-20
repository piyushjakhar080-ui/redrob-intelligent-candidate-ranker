# Redrob Intelligent Candidate Discovery & Ranking Platform

Welcome to the production repository for the **Redrob Intelligent Candidate Discovery & Ranking Challenge**. 
This solution represents a state-of-the-art algorithmic vetting, intelligence-discovery, and anti-cheat guardian engine designed to search, evaluate, and rank candidate profiles at a level worthy of high-scale enterprise recruitment pipelines.

---

## 🛠️ System Architecture

Our solution has been architected to handle high-throughput streams (up to 100,000+ candidate profiles) within severe resource limits (CPU only, 16GB RAM, < 5 minutes runtime) without calling external API layers, while maintaining $O(1)$ memory consumption.

```
redrob-ranker/
├── data/
│   └── candidates.jsonl.gz       # Raw candidate inputs (streaming compatible)
├── src/
│   ├── __init__.py
│   ├── load_data.py               # Memory-efficient gzip streaming IO
│   ├── candidate_analyzer.py      # Career progression and domain relevance analyzer
│   ├── behavioral_scorer.py       # Activity decay models and verified signals
│   ├── trap_detector.py           # Multi-layered anti-cheat & contradiction safeguards
│   ├── ranker.py                  # Score orchestrator & streaming Top-K min-heap
│   └── utils.py                   # Parsing helpers, MD5 hashing, & math functions
├── tests/
│   ├── test_candidate_analyzer.py
│   ├── test_behavioral_scorer.py
│   ├── test_trap_detector.py
│   └── test_ranker.py
├── app.py                         # Streamlit Interactive Dashboard
├── rank.py                        # Automated CLI pipeline execution entry point
├── requirements.txt               # Lightweight dependency manifests
├── submission.csv                 # Target outputs (candidate_id, rank, score, reasoning)
└── submission_metadata.yaml       # Exported analytics metadata
```

---

## ⚖️ Scoring Formula & Metrics

Our composite matching algorithm determines candidates' performance across four major pillars, incorporating custom search relevance spotlight boosts and fraud deduplication penalties.

$$\text{Final Score} = \text{Career Intelligence} (45\%) + \text{Domain Relevance} (30\%) + \text{Behavioral Signals} (20\%) + \text{Availability} (5\%) - \text{Penalties} + \text{Boosts}$$

### 1. Career Intelligence (45% Weight)
- **Job Duration Density**: Rewards candidates with stable multi-year tenures; penalizes frequent job hoppers with less than 12-month stints.
- **Career Progression**: Assesses title levels sequentially, tracking horizontal improvements or hierarchical jumps from Junior to Lead roles.
- **Company Authority**: Ranks past hiring employers (Tier 1 like Google/Meta/Netflix gets absolute multipliers, Tier 2 startups get moderate weight).
- **Career Stability**: Evaluates employment gaps and assesses penalties for idle windows longer than 6 months.
- **Promotion Velocity**: Measures the speed of professional advancement to Senior/Architect/Management titles.

### 2. Domain Relevance (30% Weight)
- Matches candidate skill vectors and resume content against ten specialized sub-domains: AI, ML, NLP, LLM, Retrieval, Search, Ranking, Recommender Systems, Vector Databases, and Production ML.
- **Chronological Recency Multiplier**: Matches found in the candidate’s modern roles get **1.5x weight**, whereas distant historical jobs get a reduced multiplier.

### 3. Behavioral Signals (20% Weight)
- Ranks candidate interest indicators: reply rates, interview progress, and GitHub involvement.
- **Exponential Activity Decay**: Inactivity periods are scaled using:
  $$\text{Decay} = 2^{-\frac{\Delta t}{HP}}$$
  Utilizes a gentle 180-day half-life ($HP$) relative to the current hackathon snapshots.

### 4. Availability (5% Weight)
- Weights the `open_to_work_flag` alongside complete email, telephone, and social network verifications.

### 🛡️ Multi-Tiered Anti-Cheat Guardrails (Penalties)
- **Keyword Stuffers (-45 points)**: Identifies profiles with more than 30 listed skills or profiles pasting keywords with zero connection to their physical work descriptions.
- **Honeypot Account Protection (-80 points)**: Catches theoretical high-profile word-spams built on fake accounts showing low activity scores, low interview completion, and no personal verifications.
- **Behavioral Twins (-30 points)**: Uses sequence hashing and MD5 profile fingerprints to immediately identify duplicated templates and bot syndicates.
- **Title Contradictions (-35 points)**: Flags entries highlighting senior staff levels with under 2.5 years of total professional work experience, or careers starting directly in a Lead capacity.

### ⭐ Hidden Star Spotlight Boost (+25 points)
- Accords a performance bonus to classical search, information retrieval, indexing, recommendation, optimization, and search relevance specialists (using tools like FAISS, Lucene, Elasticsearch, OpenSearch) even if they never mention trending buzzwords like RAG, Pinecone, or Langchain in their resumes.

---

## 🚀 Speed Run & Installation

### Prereqs
Ensure you have Python 3.9+ installed.

### 1. Repository Setup & Virtual Env
```bash
# Clone the repository
git clone <url-to-repo> /redrob-ranker
cd /redrob-ranker

# Initialize virtual environment
python3 -m venv venv
source venv/bin/activate
```

### 2. Install Lightweight Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run Pipeline CLI
Process candidates and generate your `submission.csv` in seconds:
```bash
python rank.py --input data/candidates.jsonl --jd job_description.md --output submission.csv
```

### 4. Run Interactive Local Dashboard
Boot the Streamlit visualization hub:
```bash
streamlit run app.py
```

### 5. Running Code Validation Tests
Ensure everything passes cleanly:
```bash
pytest -v
```
