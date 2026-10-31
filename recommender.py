"""
recommender.py - Roadmap Generation, Job Matching & Company Hiring Analytics
This module provides:
1. Priority classification of missing skills (High / Medium / Low demand).
2. Personalized 8-week learning roadmap linked to curated free resources.
3. Actionable recommendations to improve achievements and portfolio.
4. Job matching, sorting, filtering, and alternative role discovery.
5. Company hiring analytics, top 3 missing skills per company, and grouping (Apply Now, Almost Ready, Build Skills First).
6. Comprehensive career readiness report generator for instant download.
"""

import pandas as pd
from resources import get_skill_resource
from skill_engine import normalize_skill, calculate_skill_match, calculate_role_skill_frequencies


def get_prioritized_missing_skills(missing_skills_weighted: list[tuple[str, float]]) -> list[dict]:
    """
    Categorizes missing skills into High, Medium, and Low priority based on industry demand weight.
    
    Parameters:
        missing_skills_weighted: List of tuples [(skill_name, demand_weight), ...]
        
    Returns:
        List of dicts with skill, demand_pct, priority ('High', 'Medium', 'Low'), and resource link.
    """
    prioritized = []
    for skill, weight in missing_skills_weighted:
        demand_pct = round(weight * 100, 1)
        if demand_pct >= 65.0:
            priority = "High"
            priority_color = "#EF4444"  # Red
            urgency = "Mandatory in 65%+ job postings"
        elif demand_pct >= 40.0:
            priority = "Medium"
            priority_color = "#F59E0B"  # Amber
            urgency = "Frequently requested"
        else:
            priority = "Low"
            priority_color = "#3B82F6"  # Blue
            urgency = "Good-to-have advantage"

        res = get_skill_resource(skill)
        prioritized.append({
            "skill": skill.title(),
            "raw_skill": skill,
            "demand_weight": weight,
            "demand_pct": demand_pct,
            "priority": priority,
            "priority_color": priority_color,
            "urgency": urgency,
            "resource": res
        })

    return prioritized


def generate_learning_roadmap(missing_skills_weighted: list[tuple[str, float]], target_role: str) -> list[dict]:
    """
    Creates a personalized 8-week learning roadmap covering the student's top missing skills.
    Distributes skills into 4 pedagogical phases (2 weeks each):
    - Weeks 1-2: Core Foundations
    - Weeks 3-4: Applied Tools & Libraries
    - Weeks 5-6: Advanced Topics & Integration
    - Weeks 7-8: Capstone Portfolio Projects & Interview Prep
    """
    if not missing_skills_weighted:
        # If user has all skills, provide an advanced mastery & interview roadmap
        return [
            {
                "week_range": "Weeks 1 - 2",
                "phase_title": "Advanced Mastery & System Architecture",
                "focus_skills": ["System Design", "Clean Architecture"],
                "objective": f"Refine high-level design patterns and production best practices for {target_role}.",
                "project_task": "Architect and document an end-to-end scalable system on GitHub.",
                "resources": [get_skill_resource("python"), get_skill_resource("git")]
            },
            {
                "week_range": "Weeks 3 - 4",
                "phase_title": "Production Deployment & CI/CD",
                "focus_skills": ["Docker", "CI/CD Pipelines"],
                "objective": "Containerize your existing projects and set up automated GitHub Actions.",
                "project_task": "Deploy a live project with automated unit testing and containerization.",
                "resources": [get_skill_resource("docker"), get_skill_resource("git")]
            },
            {
                "week_range": "Weeks 5 - 6",
                "phase_title": "Performance Tuning & Security",
                "focus_skills": ["Performance Optimization", "Security Best Practices"],
                "objective": "Benchmark latency, profile memory usage, and patch security vulnerabilities.",
                "project_task": "Write comprehensive integration tests and conduct a code review audit.",
                "resources": [get_skill_resource("linux"), get_skill_resource("software testing")]
            },
            {
                "week_range": "Weeks 7 - 8",
                "phase_title": "Interview Simulation & Portfolio Polishing",
                "focus_skills": ["Mock Interviews", "Resume Tailoring"],
                "objective": "Practice technical Q&A, live coding assessments, and behavioral storytelling.",
                "project_task": "Publish your portfolio site and submit 10 targeted job applications.",
                "resources": [get_skill_resource("data structures & algorithms")]
            }
        ]

    # Extract missing skills in order of demand priority
    missing_skill_names = [s[0] for s in missing_skills_weighted]
    
    # Partition skills across the 4 two-week blocks
    n = len(missing_skill_names)
    s1 = missing_skill_names[0:1] if n >= 1 else ["Core Basics"]
    s2 = missing_skill_names[1:2] if n >= 2 else (s1 if n >= 1 else ["Tooling"])
    s3 = missing_skill_names[2:4] if n >= 3 else [missing_skill_names[-1]]
    s4 = missing_skill_names[4:6] if n >= 5 else [missing_skill_names[-1]]

    roadmap = [
        {
            "week_range": "Weeks 1 - 2",
            "phase_title": "Foundations & Core Syntax",
            "focus_skills": [s.title() for s in s1],
            "objective": f"Master the core syntax, mental model, and fundamental principles of {', '.join([s.title() for s in s1])}.",
            "project_task": f"Build 3 small mini-scripts or exercises applying {', '.join([s.title() for s in s1])}.",
            "resources": [get_skill_resource(s) for s in s1]
        },
        {
            "week_range": "Weeks 3 - 4",
            "phase_title": "Applied Workflows & Tooling",
            "focus_skills": [s.title() for s in s2],
            "objective": f"Learn practical libraries and industry workflows with {', '.join([s.title() for s in s2])}.",
            "project_task": f"Create a working command-line tool or functional prototype integrating {', '.join([s.title() for s in s2])}.",
            "resources": [get_skill_resource(s) for s in s2]
        },
        {
            "week_range": "Weeks 5 - 6",
            "phase_title": "Real-World Data & Integration",
            "focus_skills": [s.title() for s in s3],
            "objective": f"Connect databases, APIs, or pipelines using {', '.join([s.title() for s in s3])}.",
            "project_task": f"Build a multi-feature application showcasing end-to-end functionality.",
            "resources": [get_skill_resource(s) for s in s3]
        },
        {
            "week_range": "Weeks 7 - 8",
            "phase_title": "Capstone Portfolio & Interview Prep",
            "focus_skills": [s.title() for s in (s4 if s4 else s1)],
            "objective": f"Synthesize your acquired skills into a production-grade portfolio piece for {target_role}.",
            "project_task": "Publish your project with an outstanding README on GitHub, record a 2-minute demo video, and begin interview prep.",
            "resources": [get_skill_resource("git"), get_skill_resource(s4[0] if s4 else s1[0])]
        }
    ]

    return roadmap


def get_achievement_suggestions(achievement_counts: dict, target_role: str, top_missing_skills: list[str]) -> list[str]:
    """
    Generates actionable recommendations to improve the student's achievements and resume strength.
    """
    suggestions = []
    
    # Project suggestions
    primary_missing = top_missing_skills[0].title() if top_missing_skills else "SQL & Python"
    secondary_missing = top_missing_skills[1].title() if len(top_missing_skills) > 1 else "Cloud Deployment"

    if achievement_counts.get("projects", 0) < 2:
        suggestions.append(f"🛠️ **Build 2 Capstone Projects:** Create end-to-end projects implementing **{primary_missing}** and **{secondary_missing}**. Document clean setup instructions and host the code on GitHub.")
    else:
        suggestions.append(f"⭐ **Polish Existing Projects:** Add interactive live demos, unit tests, and architecture diagrams to your GitHub repositories.")

    # Certification suggestions
    if achievement_counts.get("certifications", 0) == 0:
        suggestions.append(f"📜 **Earn a Recognized Credential:** Complete a free verified learning track (e.g. freeCodeCamp Certification, Kaggle Micro-courses, or NPTEL) related to **{target_role}**.")
    
    # Internship suggestions
    if achievement_counts.get("internships", 0) == 0:
        suggestions.append("💼 **Gain Practical Experience:** Apply for virtual internships or open-source programs (like Google Summer of Code, GirlScript Summer of Code, or Forage job simulations).")

    # Hackathon suggestions
    if achievement_counts.get("hackathons", 0) == 0:
        suggestions.append("🏆 **Compete in Hackathons:** Participate in 1-2 beginner-friendly hackathons on Unstop, Devpost, or Kaggle to prove your rapid problem-solving skills under time constraints.")

    return suggestions


def match_jobs_for_user(
    all_jobs_df: pd.DataFrame,
    user_skills: list[str],
    preferred_location: str = "Anywhere",
    experience_level: str = "Fresher"
) -> pd.DataFrame:
    """
    Computes user skill match percentage against every job posting.
    Applies location and experience level filters, and sorts by match percentage descending.
    """
    if all_jobs_df.empty:
        return pd.DataFrame()

    normalized_user_skills = set(normalize_skill(s) for s in user_skills if s.strip())

    results = []
    for _, row in all_jobs_df.iterrows():
        job_skills_raw = str(row.get("required_skills", ""))
        if not job_skills_raw.strip():
            job_skills_list = []
        else:
            job_skills_list = [normalize_skill(s.strip()) for s in job_skills_raw.split(",") if s.strip()]

        total_req = len(job_skills_list)
        if total_req == 0:
            match_pct = 50.0
            matched_count = 0
        else:
            matched = [s for s in job_skills_list if s in normalized_user_skills]
            matched_count = len(matched)
            match_pct = round((matched_count / total_req) * 100, 1)

        row_dict = row.to_dict()
        row_dict["match_percentage"] = match_pct
        row_dict["matched_skills_count"] = matched_count
        row_dict["total_required_skills"] = total_req
        results.append(row_dict)

    df_matched = pd.DataFrame(results)

    # Filter by Location if not 'Anywhere'
    if preferred_location and preferred_location != "Anywhere":
        df_matched = df_matched[df_matched["location"].str.lower() == preferred_location.lower()]

    # Filter by Experience Level if specified
    if experience_level and experience_level != "All Levels":
        # Check if experience column contains experience_level
        df_matched = df_matched[
            df_matched["experience"].str.lower().str.contains(experience_level.lower(), na=False) |
            (df_matched["experience"] == "Not specified")
        ]

    # Sort by match percentage descending, then openings descending
    df_matched = df_matched.sort_values(by=["match_percentage", "number_of_openings"], ascending=[False, False]).reset_index(drop=True)
    return df_matched


def find_alternative_roles(
    all_jobs_df: pd.DataFrame,
    user_skills: list[str],
    current_target_role: str
) -> list[dict]:
    """
    Finds alternative job roles where the user's skill match is >= 50%
    (excluding their primary target role).
    """
    if all_jobs_df.empty:
        return []

    unique_roles = all_jobs_df["job_title"].unique()
    alternative_roles = []

    for role in unique_roles:
        if role.lower() == current_target_role.lower() or role == "Not specified":
            continue

        role_jobs = all_jobs_df[all_jobs_df["job_title"] == role]
        weights = calculate_role_skill_frequencies(role_jobs)
        match_score, matched_skills, missing_skills = calculate_skill_match(user_skills, weights)

        if match_score >= 50.0:
            alternative_roles.append({
                "role": role,
                "match_percentage": match_score,
                "total_openings": int(role_jobs["number_of_openings"].sum()),
                "companies_count": role_jobs["company"].nunique(),
                "top_matched_skills": matched_skills[:4],
                "top_missing_skills": [m[0].title() for m in missing_skills[:3]]
            })

    # Sort alternatives by match percentage descending
    alternative_roles.sort(key=lambda x: x["match_percentage"], reverse=True)
    return alternative_roles


def get_company_hiring_analytics(
    all_jobs_df: pd.DataFrame,
    user_skills: list[str],
    target_role: str | None = None
) -> pd.DataFrame:
    """
    Aggregates company hiring metrics for the user:
    - Company name
    - Matching roles
    - Locations
    - Number of openings
    - User's overall match %
    - Top 3 skills the user still needs to get hired there
    - Group category: 'Apply Now' (>= 70%), 'Almost Ready' (40% - 69%), 'Build Skills First' (< 40%)
    """
    if all_jobs_df.empty:
        return pd.DataFrame()

    normalized_user_skills = set(normalize_skill(s) for s in user_skills if s.strip())

    # Optionally filter to target role if desired, or all roles
    data_to_analyze = all_jobs_df.copy()
    if target_role and target_role != "All Roles":
        subset = data_to_analyze[data_to_analyze["job_title"].str.lower() == target_role.lower()]
        if not subset.empty:
            data_to_analyze = subset

    companies_data = []

    for comp, group in data_to_analyze.groupby("company"):
        total_openings = int(group["number_of_openings"].sum())
        roles_list = list(group["job_title"].unique())
        locations_list = list(group["location"].unique())

        # Collect all required skills across this company's postings
        comp_skills_all = []
        for s_str in group["required_skills"]:
            if pd.notna(s_str) and str(s_str).strip():
                comp_skills_all.extend([normalize_skill(x.strip()) for x in str(s_str).split(",") if x.strip()])

        total_req = len(comp_skills_all)
        if total_req > 0:
            matched_items = [s for s in comp_skills_all if s in normalized_user_skills]
            comp_match_pct = round((len(matched_items) / total_req) * 100, 1)
        else:
            comp_match_pct = 50.0

        # Find top 3 missing skills specifically required by this company
        missing_comp_skills = {}
        for s in comp_skills_all:
            if s not in normalized_user_skills:
                missing_comp_skills[s] = missing_comp_skills.get(s, 0) + 1

        top_3_missing = sorted(missing_comp_skills.items(), key=lambda x: x[1], reverse=True)[:3]
        top_3_missing_names = [m[0].title() for m in top_3_missing] if top_3_missing else ["None (Ready!)"]

        # Assign readiness group
        if comp_match_pct >= 70.0:
            group_label = "Apply Now"
            badge_icon = "🟢"
        elif comp_match_pct >= 40.0:
            group_label = "Almost Ready"
            badge_icon = "🟡"
        else:
            group_label = "Build Skills First"
            badge_icon = "🔴"

        companies_data.append({
            "company": comp,
            "roles": ", ".join(roles_list[:3]),
            "locations": ", ".join(locations_list[:3]),
            "number_of_openings": total_openings,
            "match_percentage": comp_match_pct,
            "top_3_missing_skills": ", ".join(top_3_missing_names),
            "group_label": group_label,
            "badge_icon": badge_icon
        })

    comp_df = pd.DataFrame(companies_data)
    if not comp_df.empty:
        comp_df = comp_df.sort_values(by=["match_percentage", "number_of_openings"], ascending=[False, False]).reset_index(drop=True)
    return comp_df


def generate_career_report_text(
    user_name: str,
    education: str,
    field: str,
    target_role: str,
    readiness_data: dict,
    roadmap: list[dict],
    top_companies_df: pd.DataFrame
) -> str:
    """
    Generates a structured, professional text summary of the student's career readiness analysis,
    gap analysis, 8-week learning plan, and hiring companies. Ready for download.
    """
    report_lines = [
        "=" * 70,
        "🌉 SKILLBRIDGE: PERSONALIZED CAREER READINESS & GAP ANALYSIS REPORT",
        "=" * 70,
        f"Candidate Name:    {user_name if user_name else 'Candidate'}",
        f"Education Level:   {education}",
        f"Field of Study:    {field}",
        f"Target Job Role:   {target_role}",
        f"Overall Readiness: {readiness_data['readiness_score']}% ({readiness_data['label']})",
        f"Skill Match Score: {readiness_data['skill_match_pct']}%",
        f"Achievement Bonus: +{readiness_data['achievement_bonus']}%",
        "-" * 70,
        "",
        "🎯 EXECUTIVE SUMMARY",
        f"{readiness_data['summary']}",
        "",
        "✅ SKILLS YOU ALREADY HAVE:",
        ", ".join([s.title() for s in readiness_data['matched_skills']]) if readiness_data['matched_skills'] else "None recorded yet",
        "",
        "❌ KEY SKILLS TO DEVELOP (Ranked by Industry Demand):",
    ]

    for item in readiness_data['missing_skills'][:6]:
        skill_name, weight = item
        report_lines.append(f"  • {skill_name.title()} (Required in {round(weight*100, 1)}% of job postings)")

    report_lines.extend([
        "",
        "-" * 70,
        "🗺️ PERSONALIZED 8-WEEK LEARNING ROADMAP",
        "-" * 70
    ])

    for phase in roadmap:
        report_lines.append(f"\n[{phase['week_range']}] {phase['phase_title']}")
        report_lines.append(f"Focus Skills: {', '.join(phase['focus_skills'])}")
        report_lines.append(f"Objective:    {phase['objective']}")
        report_lines.append(f"Project Task: {phase['project_task']}")
        report_lines.append("Free Learning Resources:")
        for r in phase['resources']:
            report_lines.append(f"  - {r['platform']}: {r['title']} ({r['url']})")

    report_lines.extend([
        "",
        "-" * 70,
        "🏢 TOP MATCHING HIRING COMPANIES",
        "-" * 70
    ])

    if not top_companies_df.empty:
        for idx, row in top_companies_df.head(5).iterrows():
            report_lines.append(
                f"{idx+1}. {row['company']} | Match: {row['match_percentage']}% | Openings: {row['number_of_openings']} | Status: {row['group_label']}"
            )
            report_lines.append(f"   Locations: {row['locations']}")
            report_lines.append(f"   Skills to close: {row['top_3_missing_skills']}")
    else:
        report_lines.append("No company records matching criteria.")

    report_lines.extend([
        "",
        "=" * 70,
        "Generated with SkillBridge – Know your gap. Bridge it. Get hired.",
        "=" * 70
    ])

    return "\n".join(report_lines)