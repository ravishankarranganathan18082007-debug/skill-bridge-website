"""
app.py - SkillBridge: Skill Gap Analysis & Career Readiness Web Application
Streamlit UI layer integrating data loading, skill parsing, job matching,
interactive visualizations, and career roadmap generation.
"""

import os
import io
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Local application modules
from data_loader import (
    load_and_process_jobs,
    get_all_jobs,
    get_unique_roles,
    get_unique_locations,
    get_unique_experience_levels,
    get_jobs_for_role,
    get_all_job_skills
)
from skill_engine import (
    normalize_skill,
    extract_text_from_file,
    detect_skills_from_text,
    calculate_role_skill_frequencies,
    calculate_career_readiness
)
from recommender import (
    get_prioritized_missing_skills,
    generate_learning_roadmap,
    get_achievement_suggestions,
    match_jobs_for_user,
    find_alternative_roles,
    get_company_hiring_analytics,
    generate_career_report_text
)


# ==============================================================================
# STREAMLIT CONFIGURATION & CUSTOM STYLING
# ==============================================================================
st.set_page_config(
    page_title="SkillBridge: Skill Gap Analysis & Career Readiness",
    page_icon="🌉",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for modern blue/teal aesthetic, rounded cards, and responsive badges
st.markdown("""
<style>
    /* Global Styles */
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* Header Container */
    .sb-header {
        background: linear-gradient(135deg, #0F172A 0%, #1E3A8A 50%, #0D9488 100%);
        color: white;
        padding: 1.8rem 2rem;
        border-radius: 14px;
        margin-bottom: 1.5rem;
        box-shadow: 0 10px 25px -5px rgba(15, 23, 42, 0.15);
    }
    .sb-title {
        font-size: 2.2rem;
        font-weight: 800;
        letter-spacing: -0.5px;
        margin: 0;
        color: #FFFFFF;
    }
    .sb-tagline {
        font-size: 1.05rem;
        color: #99F6E4;
        margin-top: 0.35rem;
        font-weight: 500;
    }
    
    /* Card Component */
    .sb-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 1.25rem 1.5rem;
        margin-bottom: 1rem;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.02);
    }
    
    /* Skill Chips / Tags */
    .skill-chip {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.82rem;
        font-weight: 600;
        margin: 3px 4px;
    }
    .skill-green {
        background-color: #DCFCE7;
        color: #166534;
        border: 1px solid #BBF7D0;
    }
    .skill-red {
        background-color: #FEE2E2;
        color: #991B1B;
        border: 1px solid #FECACA;
    }
    .skill-blue {
        background-color: #DBEAFE;
        color: #1E40AF;
        border: 1px solid #BFDBFE;
    }
    
    /* Priority Badges */
    .badge-high {
        background-color: #FEE2E2;
        color: #991B1B;
        padding: 3px 10px;
        border-radius: 6px;
        font-weight: 700;
        font-size: 0.75rem;
    }
    .badge-medium {
        background-color: #FEF3C7;
        color: #92400E;
        padding: 3px 10px;
        border-radius: 6px;
        font-weight: 700;
        font-size: 0.75rem;
    }
    .badge-low {
        background-color: #E0E7FF;
        color: #3730A3;
        padding: 3px 10px;
        border-radius: 6px;
        font-weight: 700;
        font-size: 0.75rem;
    }
    
    /* Roadmap Week Card */
    .roadmap-card {
        border-left: 4px solid #0D9488;
        background: #F8FAFC;
        padding: 1rem 1.25rem;
        border-radius: 8px;
        margin-bottom: 0.85rem;
    }
</style>
""", unsafe_allow_html=True)


# ==============================================================================
# DATA LOADING WITH STREAMLIT CACHING
# ==============================================================================
@st.cache_data(show_spinner=False)
def get_cached_job_data():
    """
    Loads all job CSV/XLSX files from the /data directory or generates sample data.
    Caches the dataframe for high performance across user interactions.
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_dir, "data")
    db_path = os.path.join(base_dir, "skillbridge.db")
    df, is_sample = load_and_process_jobs(data_dir=data_dir, db_path=db_path)
    return df, is_sample, db_path


# Initialize dataset
jobs_df, is_sample_data, db_path = get_cached_job_data()

# Pre-fetch dynamic filter options from database
available_roles = get_unique_roles(db_path=db_path)
if not available_roles:
    available_roles = ["Data Analyst", "Python Developer", "Web Developer", "Data Scientist"]

available_locations = ["Anywhere"] + get_unique_locations(db_path=db_path)
available_exp_levels = ["Fresher", "1-3 years", "3+ years"]

# Collect all distinct skills present in job postings for multi-select suggestion
all_db_skills = sorted(list(get_all_job_skills(db_path=db_path)))
if not all_db_skills:
    all_db_skills = ["python", "sql", "javascript", "react", "html", "css", "docker", "git", "aws", "power bi"]


# ==============================================================================
# SESSION STATE INITIALIZATION
# ==============================================================================
# Using st.session_state ensures analysis results and user selections persist
# across tab switches, filters, and widget triggers.
if "analyzed" not in st.session_state:
    st.session_state.analyzed = False
if "user_name" not in st.session_state:
    st.session_state.user_name = "Priya Sharma"
if "education" not in st.session_state:
    st.session_state.education = "Bachelor's (B.Tech / B.E. / B.Sc)"
if "field" not in st.session_state:
    st.session_state.field = "Computer Science & Engineering"
if "selected_skills" not in st.session_state:
    st.session_state.selected_skills = ["python", "sql", "excel"]
if "extra_skills_text" not in st.session_state:
    st.session_state.extra_skills_text = "git, pandas"
if "achievements_text" not in st.session_state:
    st.session_state.achievements_text = (
        "• Built an automated sales forecasting dashboard using Python and Pandas on GitHub\n"
        "• Completed HackerRank 5-Star Python badge & SQL Fundamentals certification\n"
        "• 2-month summer internship as a Junior Data Trainee at TechCorp\n"
        "• Finalist in College TechFest Hackathon 2025"
    )
if "target_role" not in st.session_state:
    st.session_state.target_role = "Data Analyst" if "Data Analyst" in available_roles else available_roles[0]
if "preferred_location" not in st.session_state:
    st.session_state.preferred_location = "Anywhere"
if "exp_level" not in st.session_state:
    st.session_state.exp_level = "Fresher"
if "analysis_results" not in st.session_state:
    st.session_state.analysis_results = None
if "detected_resume_skills" not in st.session_state:
    st.session_state.detected_resume_skills = []


# ==============================================================================
# HEADER & DEMO BANNER
# ==============================================================================
st.markdown("""
<div class="sb-header">
    <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 10px;">
        <div>
            <h1 class="sb-title">🌉 SkillBridge</h1>
            <div class="sb-tagline">Know your gap. Bridge it. Get hired.</div>
        </div>
        <div style="background: rgba(255,255,255,0.15); padding: 8px 16px; border-radius: 30px; font-weight: 600; font-size: 0.9rem;">
            🎯 7-Hour Hackathon Demo Edition
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# Sample demo data banner (required by specification when /data has no files)
if is_sample_data:
    st.info("ℹ️ **Using sample demo data** (100+ realistic job postings across top Indian and global companies). Drop your custom CSV/Excel files into `data/` to automatically analyze your own live market data!")

# Collapsible 'How It Works' section for judges
with st.expander("ℹ️ How it works (Guide for Judges & Students)", expanded=False):
    st.markdown("""
    **SkillBridge** solves the critical gap between academic curriculum and current industry hiring standards:
    1. **Dynamic Market Ingestion:** Reads all CSV/Excel files in `data/`, automatically adapts to varying column schemas, and indexes jobs into an embedded SQLite database.
    2. **Skill Normalization & AI Synonym Resolution:** Uses an intelligent taxonomy and fuzzy string matching (`rapidfuzz`) to map acronyms (`ml` → `machine learning`, `js` → `javascript`, `py` → `python`).
    3. **Weighted Gap Scoring:** Evaluates your profile against the target role's real-time skill distribution, weighting skills by employer demand frequency.
    4. **Achievement & Experience Boost:** Rewards verified proof-of-work (projects, certifications, internships, hackathons) with up to +15% bonus.
    5. **Actionable 8-Week Roadmap:** Recommends 100% free, high-yield learning resources (YouTube bootcamps, freeCodeCamp, NPTEL, Coursera audit, Kaggle).
    6. **Company Matching & Career Report:** Categorizes employers into *Apply Now*, *Almost Ready*, and *Build Skills First*, with instant CSV and text report exports.
    """)


# ==============================================================================
# SIDEBAR / USER INPUT FORM
# ==============================================================================
with st.sidebar:
    st.markdown("### 👤 Your Profile & Target")
    st.markdown("Enter your background details or load sample student profiles:")

    # Quick demo profile loader for convenience
    col_demo1, col_demo2 = st.columns(2)
    with col_demo1:
        if st.button("⚡ Data Profile", use_container_width=True):
            st.session_state.user_name = "Priya Sharma"
            st.session_state.education = "Bachelor's (B.Tech / B.E. / B.Sc)"
            st.session_state.field = "Computer Science & Engineering"
            st.session_state.selected_skills = ["python", "sql", "excel"]
            st.session_state.extra_skills_text = "git, pandas"
            st.session_state.achievements_text = (
                "• Built sales forecasting dashboard in Python & Pandas on GitHub\n"
                "• 5-star HackerRank SQL badge\n"
                "• 2-month summer internship as Junior Data Trainee\n"
                "• Finalist in College TechFest Hackathon"
            )
            st.session_state.target_role = "Data Analyst"
            st.session_state.preferred_location = "Bengaluru"
            st.session_state.exp_level = "Fresher"
            st.session_state.analyzed = False
            st.rerun()

    with col_demo2:
        if st.button("⚡ Web Dev", use_container_width=True):
            st.session_state.user_name = "Rahul Verma"
            st.session_state.education = "Bachelor's (B.Tech / B.E. / B.Sc)"
            st.session_state.field = "Information Technology"
            st.session_state.selected_skills = ["html", "css", "javascript"]
            st.session_state.extra_skills_text = "git, react"
            st.session_state.achievements_text = (
                "• Developed personal portfolio and blog with React and GitHub Pages\n"
                "• freeCodeCamp Responsive Web Design Certification\n"
                "• Won 2nd place in 24hr Web Design Hackathon"
            )
            st.session_state.target_role = "Web Developer"
            st.session_state.preferred_location = "Chennai"
            st.session_state.exp_level = "Fresher"
            st.session_state.analyzed = False
            st.rerun()

    st.markdown("---")

    # 1. Candidate Details
    user_name_input = st.text_input("Full Name", value=st.session_state.user_name)
    education_input = st.selectbox(
        "Education Level",
        [
            "Bachelor's (B.Tech / B.E. / B.Sc)",
            "Master's (M.Tech / MCA / M.Sc)",
            "Diploma",
            "High School",
            "PhD / Doctorate"
        ],
        index=0
    )
    field_input = st.text_input("Field of Study", value=st.session_state.field)

    st.markdown("---")

    # 2. Target Role & Preferences
    st.markdown("#### 🎯 Target Career Goal")
    role_idx = available_roles.index(st.session_state.target_role) if st.session_state.target_role in available_roles else 0
    target_role_input = st.selectbox("Target Job Role", available_roles, index=role_idx)
    
    loc_idx = available_locations.index(st.session_state.preferred_location) if st.session_state.preferred_location in available_locations else 0
    location_input = st.selectbox("Preferred Location", available_locations, index=loc_idx)
    
    exp_idx = available_exp_levels.index(st.session_state.exp_level) if st.session_state.exp_level in available_exp_levels else 0
    exp_level_input = st.selectbox("Experience Level", available_exp_levels, index=exp_idx)

    st.markdown("---")

    # 3. Resume Upload (PDF or TXT)
    st.markdown("#### 📄 Resume Upload (Optional)")
    st.caption("Upload your resume to auto-detect skills:")
    uploaded_resume = st.file_uploader("Upload Resume (PDF or TXT)", type=["pdf", "txt"], label_visibility="collapsed")

    if uploaded_resume is not None:
        extracted_text, extract_err = extract_text_from_file(uploaded_resume)
        if extract_err:
            st.warning(f"⚠️ {extract_err}")
        else:
            # Detect skills from the uploaded resume text
            candidate_pool = all_db_skills + ["python", "sql", "java", "c++", "c#", "html", "css", "javascript", "react", "docker", "git", "aws"]
            newly_detected = detect_skills_from_text(extracted_text, candidate_pool)
            if newly_detected:
                st.session_state.detected_resume_skills = newly_detected
                st.success(f"✅ Auto-detected {len(newly_detected)} skills from your resume!")
            else:
                st.info("ℹ️ No specific keywords matched. Please select or type your skills below.")

    # Show detected resume skills with option to add to active skills
    if st.session_state.detected_resume_skills:
        st.markdown("**Skills detected in resume:**")
        st.caption(", ".join([s.title() for s in st.session_state.detected_resume_skills[:8]]))
        if st.button("➕ Merge Detected Skills with My Selection", use_container_width=True):
            for s in st.session_state.detected_resume_skills:
                if s not in st.session_state.selected_skills:
                    st.session_state.selected_skills.append(s)
            st.rerun()

    # 4. Skills Input (Multi-select + Extra free text)
    st.markdown("#### 🛠️ Your Skills")
    
    # Filter default list
    valid_defaults = [s for s in st.session_state.selected_skills if s in all_db_skills]
    user_multi_skills = st.multiselect(
        "Select your common skills",
        options=all_db_skills,
        default=valid_defaults,
        help="Select any technologies and tools you are familiar with."
    )

    user_extra_skills = st.text_input(
        "Extra skills (comma separated)",
        value=st.session_state.extra_skills_text,
        help="Example: Docker, FastApi, PyTorch, Figma"
    )

    st.markdown("---")

    # 5. Achievements
    st.markdown("#### 🏆 Achievements & Practical Experience")
    st.caption("Projects, certifications, internships, hackathons, awards (1 per line):")
    user_achievements = st.text_area(
        "Achievements",
        value=st.session_state.achievements_text,
        height=110,
        label_visibility="collapsed"
    )

    st.markdown("---")

    # Action Button
    analyze_clicked = st.button("🚀 Analyse My Profile", type="primary", use_container_width=True)


# ==============================================================================
# PROFILE ANALYSIS EXECUTION LOGIC
# ==============================================================================
if analyze_clicked:
    # Combine multi-select skills and extra free-text skills
    combined_raw_skills = list(user_multi_skills)
    if user_extra_skills.strip():
        for item in user_extra_skills.split(","):
            if item.strip():
                combined_raw_skills.append(item.strip())

    # Normalize all skills using the synonym engine
    normalized_user_skills = list(set([normalize_skill(s) for s in combined_raw_skills if normalize_skill(s)]))

    if not normalized_user_skills:
        st.error("⚠️ Please select or enter at least one skill before analyzing!")
        st.session_state.analyzed = False
    else:
        # Save inputs to session state
        st.session_state.user_name = user_name_input
        st.session_state.education = education_input
        st.session_state.field = field_input
        st.session_state.target_role = target_role_input
        st.session_state.preferred_location = location_input
        st.session_state.exp_level = exp_level_input
        st.session_state.selected_skills = user_multi_skills
        st.session_state.extra_skills_text = user_extra_skills
        st.session_state.achievements_text = user_achievements

        # 1. Fetch job postings for target role
        role_jobs = get_jobs_for_role(target_role_input, db_path=db_path)
        if role_jobs.empty:
            role_jobs = jobs_df[jobs_df["job_title"].str.lower() == target_role_input.lower()]

        # 2. Compute industry skill demand weights for target role
        role_weights = calculate_role_skill_frequencies(role_jobs)

        # 3. Compute Career Readiness Score & Gap Analysis
        readiness_data = calculate_career_readiness(
            user_skills=normalized_user_skills,
            role_skill_weights=role_weights,
            achievements_text=user_achievements
        )

        # 4. Generate prioritized missing skills & 8-week learning roadmap
        prioritized_missing = get_prioritized_missing_skills(readiness_data["missing_skills"])
        roadmap = generate_learning_roadmap(readiness_data["missing_skills"], target_role_input)
        
        # 5. Generate achievement improvement recommendations
        missing_names_only = [m[0] for m in readiness_data["missing_skills"]]
        achievement_tips = get_achievement_suggestions(
            readiness_data["achievement_counts"],
            target_role_input,
            missing_names_only
        )

        # 6. Match all jobs against user skills
        matched_jobs_df = match_jobs_for_user(
            all_jobs_df=jobs_df,
            user_skills=normalized_user_skills,
            preferred_location=location_input,
            experience_level=exp_level_input
        )

        # 7. Find alternative roles where user has >= 50% match
        alt_roles = find_alternative_roles(
            all_jobs_df=jobs_df,
            user_skills=normalized_user_skills,
            current_target_role=target_role_input
        )

        # 8. Compute company hiring analytics
        companies_analytics_df = get_company_hiring_analytics(
            all_jobs_df=jobs_df,
            user_skills=normalized_user_skills,
            target_role=target_role_input
        )

        # Store full results bundle into session state
        st.session_state.analysis_results = {
            "normalized_user_skills": normalized_user_skills,
            "readiness_data": readiness_data,
            "role_weights": role_weights,
            "role_jobs": role_jobs,
            "prioritized_missing": prioritized_missing,
            "roadmap": roadmap,
            "achievement_tips": achievement_tips,
            "matched_jobs_df": matched_jobs_df,
            "alt_roles": alt_roles,
            "companies_analytics_df": companies_analytics_df
        }
        st.session_state.analyzed = True
        st.toast("🎉 Analysis complete! Explore your 3 tabs below.", icon="🚀")


# ==============================================================================
# MAIN DISPLAY: THREE TABS AFTER ANALYSIS
# ==============================================================================
if not st.session_state.analyzed or st.session_state.analysis_results is None:
    # Friendly landing placeholder before the user clicks 'Analyse My Profile'
    st.markdown("""
    <div class="sb-card" style="text-align: center; padding: 3rem 1.5rem;">
        <h2 style="color: #1E3A8A; font-weight: 800;">Welcome to SkillBridge! 🎯</h2>
        <p style="font-size: 1.1rem; color: #475569; max-width: 650px; margin: 0.5rem auto 1.5rem auto;">
            Bridge the gap between your student competencies and entry-level industry demand.
            Fill in your details in the sidebar or click one of the <b>Quick Demo Profiles</b> on the left to start!
        </p>
        <div style="display: flex; justify-content: center; gap: 15px; flex-wrap: wrap; margin-top: 1rem;">
            <div style="background: #F1F5F9; padding: 12px 20px; border-radius: 10px; font-weight: 600; color: #1E293B;">
                ⚡ 100% Offline & Local
            </div>
            <div style="background: #F1F5F9; padding: 12px 20px; border-radius: 10px; font-weight: 600; color: #1E293B;">
                📊 Real Employer Demand Weights
            </div>
            <div style="background: #F1F5F9; padding: 12px 20px; border-radius: 10px; font-weight: 600; color: #1E293B;">
                🗺️ Curated 8-Week Roadmap
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

else:
    # Unpack cached results from session state
    res = st.session_state.analysis_results
    readiness = res["readiness_data"]
    role_weights = res["role_weights"]
    role_jobs = res["role_jobs"]
    prioritized_missing = res["prioritized_missing"]
    roadmap = res["roadmap"]
    achievement_tips = res["achievement_tips"]
    matched_jobs_df = res["matched_jobs_df"]
    alt_roles = res["alt_roles"]
    comp_df = res["companies_analytics_df"]
    norm_skills = res["normalized_user_skills"]

    # Top Bar Summary Card with Candidate Info & Download Button
    col_summary, col_report_btn = st.columns([3, 1])
    with col_summary:
        st.markdown(f"""
        <div style="margin-bottom: 0.5rem;">
            <h3 style="margin: 0; color: #0F172A;">Career Analysis for <b>{st.session_state.user_name}</b></h3>
            <span style="color: #64748B; font-size: 0.95rem;">
                Target Role: <b>{st.session_state.target_role}</b> | 
                Location: <b>{st.session_state.preferred_location}</b> | 
                Experience: <b>{st.session_state.exp_level}</b>
            </span>
        </div>
        """, unsafe_allow_html=True)

    with col_report_btn:
        report_text = generate_career_report_text(
            user_name=st.session_state.user_name,
            education=st.session_state.education,
            field=st.session_state.field,
            target_role=st.session_state.target_role,
            readiness_data=readiness,
            roadmap=roadmap,
            top_companies_df=comp_df
        )
        st.download_button(
            label="📥 Download Career Report",
            data=report_text,
            file_name=f"SkillBridge_Report_{st.session_state.user_name.replace(' ', '_')}.txt",
            mime="text/plain",
            use_container_width=True
        )

    # ==========================================================================
    # THE THREE MAIN TABS
    # ==========================================================================
    tab1, tab2, tab3 = st.tabs([
        "📊 Tab 1: Skills to Improve",
        "💼 Tab 2: Job Availability",
        "🏢 Tab 3: Companies That Can Hire You"
    ])

    # --------------------------------------------------------------------------
    # TAB 1: SKILLS TO IMPROVE
    # --------------------------------------------------------------------------
    with tab1:
        # Row 1: Gauge Chart & Executive Readiness Overview
        g_col1, g_col2 = st.columns([1.3, 1.7])

        with g_col1:
            # Plotly Gauge Chart for Career Readiness Score
            fig_gauge = go.Figure(go.Indicator(
                mode="gauge+number",
                value=readiness["readiness_score"],
                domain={"x": [0, 1], "y": [0, 1]},
                title={"text": f"<b>Career Readiness</b><br><span style='font-size:0.85em;color:#64748B'>{readiness['badge']}</span>", "font": {"size": 20, "color": "#0F172A"}},
                number={"suffix": "%", "font": {"size": 38, "weight": 800, "color": readiness["color"]}},
                gauge={
                    "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": "#CBD5E1"},
                    "bar": {"color": readiness["color"], "thickness": 0.28},
                    "bgcolor": "#F1F5F9",
                    "borderwidth": 1,
                    "bordercolor": "#E2E8F0",
                    "steps": [
                        {"range": [0, 40], "color": "#FEE2E2"},
                        {"range": [40, 70], "color": "#FEF3C7"},
                        {"range": [70, 85], "color": "#DCFCE7"},
                        {"range": [85, 100], "color": "#CCFBF1"}
                    ],
                    "threshold": {
                        "line": {"color": "#0F172A", "width": 4},
                        "thickness": 0.75,
                        "value": readiness["readiness_score"]
                    }
                }
            ))
            fig_gauge.update_layout(
                height=260,
                margin=dict(l=20, r=20, t=40, b=10),
                paper_bgcolor="rgba(0,0,0,0)"
            )
            st.plotly_chart(fig_gauge, use_container_width=True)

        with g_col2:
            st.markdown(f"""
            <div class="sb-card" style="height: 240px; display: flex; flex-direction: column; justify-content: center;">
                <div style="font-size: 0.85rem; font-weight: 700; color: #64748B; text-transform: uppercase; letter-spacing: 0.5px;">Readiness Diagnosis</div>
                <h3 style="margin: 0.2rem 0; color: {readiness['color']}; font-weight: 800;">{readiness['badge']}</h3>
                <p style="color: #334155; font-size: 0.95rem; margin-bottom: 0.8rem; line-height: 1.45;">
                    {readiness['summary']}
                </p>
                <div style="display: flex; gap: 15px; font-size: 0.9rem;">
                    <div><b>Skill Match:</b> {readiness['skill_match_pct']}%</div>
                    <div><b>Achievement Boost:</b> +{readiness['achievement_bonus']}% (Max 15%)</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")

        # Row 2: Skills You Have (Green) vs Missing Skills (Red)
        col_have, col_need = st.columns(2)

        with col_have:
            st.markdown("#### ✅ Skills You Already Have")
            if readiness["matched_skills"]:
                chips_html = "".join([f'<span class="skill-chip skill-green">✓ {s.title()}</span>' for s in readiness["matched_skills"]])
                st.markdown(f'<div class="sb-card">{chips_html}</div>', unsafe_allow_html=True)
            else:
                st.info("No matching skills detected yet for this role. Check the missing skills below to start building your foundation!")

        with col_need:
            st.markdown("#### ❌ Skills You Need to Build")
            if readiness["missing_skills"]:
                chips_html = "".join([f'<span class="skill-chip skill-red">✗ {s[0].title()}</span>' for s in readiness["missing_skills"]])
                st.markdown(f'<div class="sb-card">{chips_html}</div>', unsafe_allow_html=True)
            else:
                st.success("🎉 Incredible! You already possess all core skills required for this job role!")

        # Row 3: Bar Chart of In-Demand Skills for Target Role with User Skills Highlighted
        st.markdown(f"#### 📊 In-Demand Skills for {st.session_state.target_role}")
        st.caption("Green bars indicate skills you already have; Red bars indicate missing skills you need to acquire.")

        if role_weights:
            chart_skills = list(role_weights.keys())[:10]
            chart_pcts = [round(role_weights[s] * 100, 1) for s in chart_skills]
            chart_colors = [
                "#10B981" if s in readiness["matched_skills"] else "#EF4444"
                for s in chart_skills
            ]
            chart_status = [
                "Acquired (In your profile)" if s in readiness["matched_skills"] else "Missing (Gap to bridge)"
                for s in chart_skills
            ]

            fig_demand = go.Figure(go.Bar(
                x=[s.title() for s in chart_skills],
                y=chart_pcts,
                marker=dict(color=chart_colors, cornerradius=6),
                text=[f"{p}%" for p in chart_pcts],
                textposition="outside",
                hovertext=chart_status,
                hoverinfo="x+y+text"
            ))
            fig_demand.update_layout(
                yaxis=dict(title="% of Postings Requesting Skill", range=[0, 115]),
                xaxis=dict(title="Technical Skill"),
                margin=dict(l=20, r=20, t=20, b=20),
                height=320,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)"
            )
            st.plotly_chart(fig_demand, use_container_width=True)

        # Row 4: Priority List of Missing Skills Ranked by Demand
        st.markdown("#### 🎯 Priority Ranking of Missing Skills")
        st.caption("Skills are ranked strictly by employer demand frequency so you study the most impactful topics first.")

        if prioritized_missing:
            table_rows = []
            for item in prioritized_missing:
                res_link = f"<a href='{item['resource']['url']}' target='_blank' style='color:#0D9488; font-weight:600;'>{item['resource']['platform']} ↗</a>"
                table_rows.append({
                    "Priority": f"<span class='badge-{item['priority'].lower()}'>{item['priority'].upper()}</span>",
                    "Skill": f"<b>{item['skill']}</b>",
                    "Employer Demand": f"{item['demand_pct']}% of jobs",
                    "Impact Reason": item["urgency"],
                    "Free Resource": res_link
                })

            df_prio = pd.DataFrame(table_rows)
            st.write(df_prio.to_html(escape=False, index=False), unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)
        else:
            st.success("No missing skills to prioritize!")

        # Row 5: Personalized 8-Week Learning Roadmap
        st.markdown(f"#### 🗺️ Personalized 8-Week Learning Roadmap for {st.session_state.target_role}")
        st.caption("A structured, step-by-step curriculum with verified free tutorials, interactive exercises, and capstone tasks:")

        for phase in roadmap:
            res_links_html = " • ".join([
                f"<a href='{r['url']}' target='_blank' style='color:#0D9488; text-decoration: underline; font-weight:600;'>{r['platform']}: {r['title']} ↗</a>"
                for r in phase["resources"]
            ])

            st.markdown(f"""
            <div class="roadmap-card">
                <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">
                    <span style="font-weight: 800; color: #0D9488; font-size: 0.95rem;">{phase['week_range']}</span>
                    <span style="font-size: 0.85rem; font-weight: 700; background: #E2E8F0; padding: 2px 8px; border-radius: 4px; color: #1E293B;">
                        Focus: {', '.join(phase['focus_skills'])}
                    </span>
                </div>
                <h4 style="margin: 0.4rem 0 0.2rem 0; color: #0F172A;">{phase['phase_title']}</h4>
                <div style="font-size: 0.9rem; color: #334155; margin-bottom: 0.4rem;">
                    <b>Target Objective:</b> {phase['objective']}
                </div>
                <div style="font-size: 0.88rem; color: #475569; margin-bottom: 0.5rem;">
                    <b>🛠️ Practical Task:</b> {phase['project_task']}
                </div>
                <div style="font-size: 0.85rem; color: #1E3A8A; background: #EEF2F6; padding: 6px 12px; border-radius: 6px;">
                    <b>Free Learning Material:</b> {res_links_html}
                </div>
            </div>
            """, unsafe_allow_html=True)

        # Row 6: Suggestions to Improve Achievements
        st.markdown("#### ⭐ Boost Your Profile & Portfolio")
        st.caption("Targeted tips to increase your Career Readiness score into the Job-Ready / Strong Candidate bracket:")
        for tip in achievement_tips:
            st.markdown(f"- {tip}")

    # --------------------------------------------------------------------------
    # TAB 2: JOB AVAILABILITY
    # --------------------------------------------------------------------------
    with tab2:
        st.markdown(f"### 💼 Market Demand & Openings: {st.session_state.target_role}")

        # Target role specific job subset for metrics
        target_role_jobs = jobs_df[jobs_df["job_title"].str.lower() == st.session_state.target_role.lower()]
        if target_role_jobs.empty:
            target_role_jobs = jobs_df

        # 4 KPI Metrics Cards
        k1, k2, k3, k4 = st.columns(4)
        with k1:
            total_openings_role = int(target_role_jobs["number_of_openings"].sum())
            st.metric("Total Openings", f"{total_openings_role} positions")
        with k2:
            num_hiring_comps = target_role_jobs["company"].nunique()
            st.metric("Companies Hiring", f"{num_hiring_comps} firms")
        with k3:
            # Display median salary or range
            sample_salary = target_role_jobs["salary"].iloc[0] if not target_role_jobs.empty else "Competitive"
            st.metric("Average Salary Range", sample_salary)
        with k4:
            active_locations_count = target_role_jobs["location"].nunique()
            st.metric("Hiring Locations", f"{active_locations_count} cities")

        st.markdown("---")

        # Charts: Openings by Location & Top Related Roles
        c_loc, c_rel = st.columns(2)

        with c_loc:
            st.markdown("##### 📍 Openings by Location")
            loc_series = target_role_jobs.groupby("location")["number_of_openings"].sum().reset_index()
            loc_series = loc_series.sort_values(by="number_of_openings", ascending=False)
            
            fig_loc = px.bar(
                loc_series,
                x="location",
                y="number_of_openings",
                text="number_of_openings",
                color="number_of_openings",
                color_continuous_scale="Teal",
                labels={"number_of_openings": "Openings", "location": "City"}
            )
            fig_loc.update_layout(height=280, margin=dict(l=10, r=10, t=10, b=10), coloraxis_showscale=False)
            st.plotly_chart(fig_loc, use_container_width=True)

        with c_rel:
            st.markdown("##### 🏢 Top Roles by Market Openings")
            all_roles_series = jobs_df.groupby("job_title")["number_of_openings"].sum().reset_index()
            all_roles_series = all_roles_series.sort_values(by="number_of_openings", ascending=False).head(7)

            fig_rel = px.bar(
                all_roles_series,
                x="number_of_openings",
                y="job_title",
                orientation="h",
                text="number_of_openings",
                color="number_of_openings",
                color_continuous_scale="Blues",
                labels={"number_of_openings": "Openings", "job_title": "Role"}
            )
            fig_rel.update_layout(height=280, margin=dict(l=10, r=10, t=10, b=10), coloraxis_showscale=False)
            st.plotly_chart(fig_rel, use_container_width=True)

        # Job posting trend over time (if date column exists)
        if "posted_date" in jobs_df.columns:
            st.markdown("##### 📈 Recent Job Postings Trend")
            date_df = jobs_df.groupby("posted_date")["number_of_openings"].sum().reset_index()
            date_df = date_df.sort_values(by="posted_date")
            fig_trend = px.line(
                date_df,
                x="posted_date",
                y="number_of_openings",
                markers=True,
                labels={"posted_date": "Posting Date", "number_of_openings": "New Openings"}
            )
            fig_trend.update_traces(line_color="#0D9488", line_width=3)
            fig_trend.update_layout(height=240, margin=dict(l=10, r=10, t=10, b=10))
            st.plotly_chart(fig_trend, use_container_width=True)

        st.markdown("---")

        # Interactive Filterable Matching Jobs Table
        st.markdown("#### 📋 Matched Job Listings for Your Skills")
        st.caption("Sorted by your personal skill match percentage. Filter by location and experience level dynamically:")

        f_col1, f_col2, f_col3 = st.columns([1.5, 1.5, 1])
        with f_col1:
            table_loc_filter = st.selectbox(
                "Filter Table by Location",
                ["All Locations"] + list(jobs_df["location"].unique()),
                index=0
            )
        with f_col2:
            table_exp_filter = st.selectbox(
                "Filter Table by Experience",
                ["All Levels", "Fresher", "1-3 years", "3+ years"],
                index=0
            )
        with f_col3:
            min_match_filter = st.slider("Min Match %", min_value=0, max_value=100, value=20, step=10)

        # Apply table filters
        filtered_table = matched_jobs_df.copy()
        if table_loc_filter != "All Locations":
            filtered_table = filtered_table[filtered_table["location"].str.lower() == table_loc_filter.lower()]
        if table_exp_filter != "All Levels":
            filtered_table = filtered_table[filtered_table["experience"].str.lower().str.contains(table_exp_filter.lower(), na=False)]
        filtered_table = filtered_table[filtered_table["match_percentage"] >= min_match_filter]

        if not filtered_table.empty:
            display_jobs = filtered_table[[
                "job_title", "company", "location", "salary", "experience",
                "match_percentage", "required_skills", "job_link"
            ]].copy()
            
            display_jobs.columns = [
                "Job Title", "Company", "Location", "Salary Range", "Experience",
                "Match %", "Required Skills", "Apply Link"
            ]
            
            st.dataframe(
                display_jobs,
                column_config={
                    "Match %": st.column_config.ProgressColumn(
                        "Your Skill Match",
                        help="Calculated based on your matched skills vs job requirements",
                        format="%d%%",
                        min_value=0,
                        max_value=100
                    ),
                    "Apply Link": st.column_config.LinkColumn("Apply Link")
                },
                use_container_width=True,
                hide_index=True
            )
        else:
            st.warning("No jobs found matching your specific filter criteria. Try relaxing your location or minimum match threshold!")

        st.markdown("---")

        # Alternative Roles Close to User
        st.markdown("#### 🔄 Alternative Roles You Are Close To")
        st.caption("Roles where your current skill match is 50% or above:")

        if alt_roles:
            cols = st.columns(min(3, len(alt_roles)))
            for idx, role_info in enumerate(alt_roles[:6]):
                col_target = cols[idx % len(cols)]
                with col_target:
                    st.markdown(f"""
                    <div class="sb-card" style="border-top: 4px solid #3B82F6;">
                        <h4 style="margin: 0; color: #1E3A8A;">{role_info['role']}</h4>
                        <div style="font-size: 1.25rem; font-weight: 800; color: #2563EB; margin: 0.3rem 0;">
                            {role_info['match_percentage']}% Match
                        </div>
                        <div style="font-size: 0.85rem; color: #475569; margin-bottom: 0.4rem;">
                            <b>Openings:</b> {role_info['total_openings']} across {role_info['companies_count']} companies
                        </div>
                        <div style="font-size: 0.82rem; color: #166534;">
                            <b>Skills you have:</b> {', '.join([s.title() for s in role_info['top_matched_skills']])}
                        </div>
                        <div style="font-size: 0.82rem; color: #991B1B; margin-top: 3px;">
                            <b>To unlock:</b> {', '.join(role_info['top_missing_skills'])}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("No alternative roles currently exceed 50% match. Focus on your primary target role roadmap to build broad transferable skills!")

    # --------------------------------------------------------------------------
    # TAB 3: COMPANIES THAT CAN HIRE YOU
    # --------------------------------------------------------------------------
    with tab3:
        st.markdown(f"### 🏢 Companies Hiring for {st.session_state.target_role}")
        st.caption("Employers ranked by your skill match percentage and open vacancies:")

        # Top 10 Companies by Openings Bar Chart
        if not comp_df.empty:
            chart_comp = comp_df.sort_values(by="number_of_openings", ascending=False).head(10)
            fig_comp = px.bar(
                chart_comp,
                x="company",
                y="number_of_openings",
                color="match_percentage",
                text="number_of_openings",
                color_continuous_scale="Teal",
                labels={"number_of_openings": "Vacancies", "company": "Company", "match_percentage": "Match %"}
            )
            fig_comp.update_layout(
                title="Top 10 Hiring Companies by Vacancies (Color = Your Match %)",
                height=320,
                margin=dict(l=20, r=20, t=40, b=20)
            )
            st.plotly_chart(fig_comp, use_container_width=True)

        st.markdown("---")

        # Download button for matched companies & jobs CSV
        c_csv_download, c_csv_space = st.columns([1, 2])
        with c_csv_download:
            csv_data = comp_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Export Matched Companies as CSV",
                data=csv_data,
                file_name="SkillBridge_Matched_Companies.csv",
                mime="text/csv",
                use_container_width=True
            )

        st.markdown("#### 🏢 Ranked Company Opportunities")

        # Group tabs or sections: Apply Now, Almost Ready, Build Skills First
        subtab_all, subtab_apply, subtab_ready, subtab_build = st.tabs([
            "All Companies",
            "🟢 Apply Now (Match ≥ 70%)",
            "🟡 Almost Ready (40% - 69%)",
            "🔴 Build Skills First (< 40%)"
        ])

        def render_company_cards(df_to_render):
            if df_to_render.empty:
                st.info("No companies in this category.")
                return

            for _, row in df_to_render.iterrows():
                badge_bg = "#DCFCE7" if row["group_label"] == "Apply Now" else ("#FEF3C7" if row["group_label"] == "Almost Ready" else "#FEE2E2")
                badge_fg = "#166534" if row["group_label"] == "Apply Now" else ("#92400E" if row["group_label"] == "Almost Ready" else "#991B1B")

                st.markdown(f"""
                <div class="sb-card" style="margin-bottom: 0.85rem;">
                    <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 8px;">
                        <div>
                            <h4 style="margin: 0; color: #0F172A; font-size: 1.15rem;">{row['company']}</h4>
                            <div style="font-size: 0.88rem; color: #475569; margin-top: 3px;">
                                <b>Roles:</b> {row['roles']} | <b>Locations:</b> {row['locations']}
                            </div>
                        </div>
                        <div style="text-align: right;">
                            <span style="background: {badge_bg}; color: {badge_fg}; font-weight: 700; padding: 4px 10px; border-radius: 6px; font-size: 0.8rem;">
                                {row['badge_icon']} {row['group_label']} ({row['match_percentage']}%)
                            </span>
                            <div style="font-size: 0.82rem; color: #64748B; margin-top: 4px;">
                                <b>{row['number_of_openings']}</b> Open Positions
                            </div>
                        </div>
                    </div>
                    <div style="margin-top: 0.65rem; padding-top: 0.5rem; border-top: 1px dashed #E2E8F0; font-size: 0.85rem; color: #334155;">
                        <b>Top Skills to Close Before Interview:</b> <span style="color: #991B1B; font-weight: 600;">{row['top_3_missing_skills']}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

        with subtab_all:
            render_company_cards(comp_df)

        with subtab_apply:
            apply_df = comp_df[comp_df["group_label"] == "Apply Now"]
            render_company_cards(apply_df)

        with subtab_ready:
            ready_df = comp_df[comp_df["group_label"] == "Almost Ready"]
            render_company_cards(ready_df)

        with subtab_build:
            build_df = comp_df[comp_df["group_label"] == "Build Skills First"]
            render_company_cards(build_df)


# ==============================================================================
# FOOTER
# ==============================================================================
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #94A3B8; font-size: 0.85rem; padding: 1.5rem 0;">
    <b>SkillBridge: Skill Gap Analysis & Career Readiness Platform</b><br>
    Built with Python, Streamlit, SQLite, Plotly & RapidFuzz • 100% Offline & Open-Source Ready
</div>
""", unsafe_allow_html=True)
