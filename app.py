import streamlit as st
import json
import gzip
import io
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from src.ranker import CandidateRanker
from src.load_data import stream_candidates

# Set page configs
st.set_page_config(
    page_title="Redrob Candidate Discovery & Ranking Hub",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Render main header
st.title("🤖 Redrob Intelligent Candidate Discovery & Ranking")
st.markdown("##### Production-grade screening, scoring, and automated guardrails for heavy candidate streams.")

# Sidebar controls for pipeline parameters
st.sidebar.header("⚙️ Pipeline Configuration")

st.sidebar.markdown("### Scoring Weights")
w_career = st.sidebar.slider("Career Intelligence (45% Standard)", 0, 100, 45, 5, help="Job duration density, progression steps, authorities.")
w_domain = st.sidebar.slider("Domain Relevance (30% Standard)", 0, 100, 30, 5, help="Keyword matching vectors, recency, search relevance.")
w_behavior = st.sidebar.slider("Behavioral Signals (20% Standard)", 0, 100, 20, 5, help="Portal activity decay, GitHub engagement, click rates.")
w_avail = st.sidebar.slider("Availability Metrics (5% Standard)", 0, 100, 5, 5, help="Immediate response, verified accounts.")

# Normalize sidebar sliders to sum up to 1.0 safely
total_sliders = w_career + w_domain + w_behavior + w_avail
if total_sliders == 0:
    total_sliders = 1
scale_c = w_career / total_sliders
scale_d = w_domain / total_sliders
scale_b = w_behavior / total_sliders
scale_a = w_avail / total_sliders

st.sidebar.markdown(f"**Normalized configuration ratios:**\n* Career: {scale_c:.1%}\n* Domain: {scale_d:.1%}\n* Behavior: {scale_b:.1%}\n* Availability: {scale_a:.1%}")

st.sidebar.markdown("---")
st.sidebar.markdown("### Anti-Cheat Deductions")
p_stuffer = st.sidebar.number_input("Keyword Stuffers Penalty", 10, 100, 45, step=5)
p_honeypot = st.sidebar.number_input("Honeypot Penalty", 20, 150, 80, step=5)
p_twin = st.sidebar.number_input("Behavioral Twin Penalty", 10, 100, 30, step=5)
p_contra = st.sidebar.number_input("Title Contradiction Penalty", 10, 100, 35, step=5)

st.sidebar.markdown("---")
st.sidebar.markdown("### Hidden Star Boost")
b_hidden = st.sidebar.number_input("Relevance Search Boost", 5, 50, 25, step=5)

# Primary Tabs
tab_sandbox, tab_code, tab_guide = st.tabs(["🚀 Discovery Sandbox", "📁 Core Code Repository", "📖 Scoring Playbook"])

with tab_sandbox:
    st.subheader("📊 Live Scoring Engine")
    
    # Text input for Job Description
    default_jd = """# Staff Machine Learning Engineer - Search Relevance & Ranking Systems

We are seeking a seasoned Specialist in Search, Information Retrieval, and Recommendation Engines.

### Key Responsibilities:
- Designing high-scale ranking algorithms, search query retrieval, and hybrid dense/sparse search functions.
- Implementing high-performance personalization models, vector databases, and approximate nearest neighbor (ANN) indexes.
- Tuning learning-to-rank (LTR) algorithms using production-ML engineering pipelines.

### Requirements:
- 5+ years shipping high-scale ranking models, Elasticsearch/Lucene configurations, recommendations, or index pipelines.
- Solid knowledge of machine learning, collaborative filtering, deep retrieval, and vector search technologies."""

    jd_text = st.text_area("🎯 Position Job Description (Markdown)", default_jd, height=180)
    
    # Candidate dataset loading options
    st.markdown("### 📥 Candidate Dataset Inputs")
    uploaded_file = st.file_uploader("Upload candidates file (.jsonl or .jsonl.gz)", type=["jsonl", "gz"])
    
    # Baseline fallback or generated sample records for clean first-run experience
    mock_candidates = [
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
            "candidate_id": "c_hidden_star_02",
            "skills": ["Elasticsearch", "ranking", "search relevance", "Solr", "C++", "Java"],
            "experiences": [
                {
                    "company": "Apple", "title": "Search Infrastructure Architect", "start_date": "2019-01", "end_date": "2024-03",
                    "description": "Designed indexing and ranking algorithms. Optimized Lucene inverted indices and ANN personalization search."
                }
            ],
            "recruiter_response_rate": 0.85, "interview_completion_rate": 0.78, "github_activity_score": 60.0,
            "saved_by_recruiters_30d": 12, "search_appearance_30d": 110, "last_active_date": "2026-05-10",
            "open_to_work_flag": False, "verified_email": True, "verified_phone": True, "linkedin_connected": True
        }
    ]
    
    # Process inputs
    candidates_to_process = []
    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith(".gz"):
                # Gzip decompression
                gzip_file = gzip.GzipFile(fileobj=uploaded_file)
                for line in gzip_file:
                    if line.strip():
                        candidates_to_process.append(json.loads(line))
            else:
                for line in uploaded_file:
                    if line.strip():
                        candidates_to_process.append(json.loads(line))
            st.success(f"✓ Cleanly loaded {len(candidates_to_process)} candidates from upload.")
        except Exception as e:
            st.error(f"Error parsing uploaded file: {e}")
            candidates_to_process = mock_candidates
    else:
        st.info("💡 Streaming boilerplate mock dataset (Upload custom candidate profiles anytime).")
        candidates_to_process = mock_candidates

    # Initialize Ranker
    ranker = CandidateRanker(jd_text)
    
    # Overwrite penalties and weights with slider options
    # We tweak candidate scoring calculation programmatically to map customized params
    def custom_score_cand(candidate):
        res = ranker.calculate_candidate_score(candidate)
        # Apply customized configurations
        breakdown = res["breakdown"]
        
        # Redraw scores using custom sliders
        weighted_total = (
            (breakdown["career_score"] / 0.45) * scale_c +
            (breakdown["domain_score"] / 0.30) * scale_d +
            (breakdown["behavioral_score"] / 0.20) * scale_b +
            (breakdown["availability_score"] / 0.05) * scale_a
        )
        
        # Override penalties
        deduct = 0.0
        applied_custom_traps = []
        if breakdown["penalties"] > 0:
            # Recheck traps to set customized rates
            skills = candidate.get("skills", [])
            experiences = candidate.get("experiences", [])
            candidate_id = res["candidate_id"]
            
            kw_stuffer, _ = ranker.trap_detector.detect_keyword_stuffer(skills, experiences)
            honeypot, _ = ranker.trap_detector.detect_honeypot(skills, experiences, {}, {})
            twin, _ = ranker.trap_detector.check_behavioral_twin(candidate_id, experiences)
            contra, _ = ranker.trap_detector.detect_title_contradiction(experiences)
            
            if kw_stuffer:
                deduct += p_stuffer
                applied_custom_traps.append("Keyword Stuffer")
            if honeypot:
                deduct += p_honeypot
                applied_custom_traps.append("Honeypot")
            if twin:
                deduct += p_twin
                applied_custom_traps.append("Behavioral Twin")
            if contra:
                deduct += p_contra
                applied_custom_traps.append("Title Contradiction")
                
        # Override boosts
        boost = 0.0
        if breakdown["is_hidden_star"]:
            boost = b_hidden
            
        final_score = weighted_total - deduct + boost
        res["final_score"] = max(0.0, min(100.0, round(final_score, 2)))
        res["breakdown"]["penalties"] = deduct
        res["breakdown"]["boosts"] = boost
        return res

    # Score all elements in stream
    results = [custom_score_cand(c) for c in candidates_to_process]
    # Sort results
    results.sort(key=lambda x: x["final_score"], reverse=True)
    
    df_results = pd.DataFrame([
        {
            "Candidate ID": r["candidate_id"],
            "Rank": i,
            "Final Score": r["final_score"],
            "Career Score (Max 45)": r["breakdown"]["career_score"],
            "Domain Score (Max 30)": r["breakdown"]["domain_score"],
            "Behavioral Score (Max 20)": r["breakdown"]["behavioral_score"],
            "Availability Score (Max 5)": r["breakdown"]["availability_score"],
            "Penalties Applied": r["breakdown"]["penalties"],
            "Relevance Boost": r["breakdown"]["boosts"],
            "Reasoning": r["reasoning"]
        }
        for i, r in enumerate(results, 1)
    ])
    
    # Render dashboard metrics
    m1, m2, m3 = st.columns(3)
    with m1:
        st.metric("Profiles Screened", len(results))
    with m2:
        traps_detected = sum(1 for r in results if r["breakdown"]["penalties"] > 0)
        st.metric("Defended Fraud Accounts", traps_detected, delta=f"{traps_detected/max(1, len(results)):.1%} of batch", delta_color="inverse")
    with m3:
        stars_detected = sum(1 for r in results if r["breakdown"]["is_hidden_star"])
        st.metric("Spotlighted Hidden Stars", stars_detected, delta=f"{stars_detected/max(1, len(results)):.1%} of batch")

    # Render ranking table
    st.markdown("### 🏆 Top Selected Matching Candidates")
    st.dataframe(df_results, use_container_width=True)
    
    # Plotly Scores Distribution
    if results:
        col_fig1, col_fig2 = st.columns(2)
        with col_fig1:
            st.markdown("#### Score Component Distribution")
            df_melt = pd.melt(df_results, id_vars=["Candidate ID"], value_vars=["Career Score (Max 45)", "Domain Score (Max 30)", "Behavioral Score (Max 20)", "Availability Score (Max 5)"], var_name="Metric", value_name="Points")
            fig = px.bar(df_melt, x="Candidate ID", y="Points", color="Metric", title="Detailed Scoring Profile Comparison", barmode="stack", color_discrete_sequence=px.colors.qualitative.Antique)
            st.plotly_chart(fig, use_container_width=True)
        with col_fig2:
            st.markdown("#### Overall Score Spread")
            fig_spread = px.violin(df_results, y="Final Score", box=True, points="all", title="Final Cumulative Scores Density", color_discrete_sequence=["#2ca02c"])
            st.plotly_chart(fig_spread, use_container_width=True)
            
    # Candidate Explorer
    st.markdown("### 🕵️ Dynamic Candidate Profile Explorer")
    if results:
        selected_cand_id = st.selectbox("Select a candidate profile to inspect:", df_results["Candidate ID"].unique())
        
        detail_cand = next(r for r in results if r["candidate_id"] == selected_cand_id)
        raw_source = next(c for c in candidates_to_process if str(c.get("candidate_id", c.get("id"))) == selected_cand_id)
        
        d1, d2 = st.columns([1, 2])
        with d1:
            st.markdown("#### 🎯 Score Breakdown Metrics")
            st.metric("Final Score Metric", f"{detail_cand['final_score']} pts")
            
            # Gauge chart of final score out of 100
            fig_gauge = go.Figure(go.Indicator(
                mode = "gauge+number",
                value = detail_cand["final_score"],
                domain = {'x': [0, 1], 'y': [0, 1]},
                title = {'text': "Match Index", 'font': {'size': 20}},
                gauge = {
                    'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "darkblue"},
                    'bar': {'color': "darkblue"},
                    'bgcolor': "white",
                    'borderwidth': 2,
                    'bordercolor': "gray",
                    'steps': [
                        {'range': [0, 50], 'color': 'red'},
                        {'range': [50, 80], 'color': 'orange'},
                        {'range': [80, 100], 'color': 'green'}
                    ],
                }
            ))
            fig_gauge.update_layout(height=240, margin=dict(l=10, r=10, t=30, b=10))
            st.plotly_chart(fig_gauge, use_container_width=True)
            
            st.markdown(f"**Automated Summary Notes:**\n`{detail_cand['reasoning']}`")
            
        with d2:
            st.markdown("#### 👤 Raw Candidate Profile & Work History")
            st.json(raw_source)

with tab_code:
    st.subheader("📂 Codebase Distribution Viewer")
    st.markdown("Browse, inspect, or copy files generated inside this production repository:")
    
    file_map = {
        "load_data.py": "src/load_data.py",
        "candidate_analyzer.py": "src/candidate_analyzer.py",
        "behavioral_scorer.py": "src/behavioral_scorer.py",
        "trap_detector.py": "src/trap_detector.py",
        "ranker.py": "src/ranker.py",
        "utils.py": "src/utils.py",
        "rank.py": "rank.py",
        "requirements.txt": "requirements.txt",
        "submission_metadata.yaml": "submission_metadata.yaml"
    }
    
    selected_view = st.selectbox("Select file to read:", list(file_map.keys()))
    
    # Read file content safely
    try:
        f_path = f"redrob-ranker/{file_map[selected_view]}"
        if os.path.exists(f_path):
            with open(f_path, "r", encoding="utf-8") as rf:
                content = rf.read()
            st.code(content, language="python")
        else:
            st.warning(f"File {f_path} not found in virtual space.")
    except Exception as ec:
        st.error(f"Error loading source file: {ec}")

with tab_guide:
    st.subheader("📖 Developer Scoring & Guardrails Cookbook")
    st.markdown("""
    ### 🔬 Advanced AI-Based Match Index Rules
    
    This platform orchestrates professional applicant profile features and applies automated filters:
    
    - **Career Intelligence (45%)**
      Evaluates long-term professional development. Average tenure rates are tested (excluding brief <12-month roles to prevent job hoppers). Promotion leaps between Junior, Senior, and Lead titles are tracked. Gaps greater than 6 months are assessed.
      
    - **Domain Relevance (30%)**
      Analyzes search Relevance, Elasticsearch architectures, Recommender models, ANN indices, and PyTorch configurations. Employs a **chronological multiplier** (recent jobs count twice as heavily as older historic roles).
      
    - **Behavioral Signals (20%)**
      Tests responsive portal interaction. Inactive periods are decay-scaled using an exponential algorithm (180 days half-life).
      
    - **Availability Signals (5%)**
      Rewards active seekers with complete email, telephone, and social verification.
      
    ### 🛡️ Built-in Anti-Cheat Penalties
    
    1. **Keyword Stuffers (-45 pts)**: Occurs when candidates enter over 30 skill sets, or copy-paste words that do not exist inside their historic job responsibilities.
    2. **Honeypot Account Protection (-80 pts)**: Targets automated profiles loading theoretical buzzwords combined with low activity rates, low interviews, and zero verification.
    3. **Behavioral Twins (-30 pts)**: Catches duplicate records utilizing identical phrasing or sequence profiles.
    4. **Title Contradictions (-35 pts)**: Identifies junior profiles calling themselves 'Staff' or starting their careers directly as 'Lead Engineers'.
    
    ### ⭐ Hidden Star Spotting (+25 pts)
    Provides a custom relevancy boost for classical search, index, recommendation, and relevance algorithms experts even if they don't load current trending terms like RAG or Langchain on their CVs.
    """)
