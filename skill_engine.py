"""
skill_engine.py - Skill Normalization, Resume Parsing & Career Readiness Engine
This module handles:
1. Normalizing skill names with a synonym dictionary and fuzzy matching.
2. Extracting text safely from uploaded PDF or TXT resumes.
3. Auto-detecting skills within free-form resume text.
4. Computing weighted skill match score against industry job postings.
5. Detecting achievements (projects, certifications, internships, hackathons) and computing an achievement bonus (capped at 15%).
6. Determining the final Career Readiness Score (0-100) and readiness level.
"""

import re
import io
import pandas as pd
import pdfplumber
from rapidfuzz import fuzz, process


# Comprehensive dictionary mapping common aliases, acronyms, and variations to canonical skill names
SKILL_SYNONYMS = {
    # Programming Languages
    "py": "python",
    "python3": "python",
    "python 3": "python",
    "js": "javascript",
    "ecmascript": "javascript",
    "ts": "typescript",
    "cpp": "c++",
    "c plus plus": "c++",
    "csharp": "c#",
    "c sharp": "c#",
    "golang": "go",
    
    # Web & Frameworks
    "reactjs": "react",
    "react.js": "react",
    "nodejs": "node.js",
    "node": "node.js",
    "vuejs": "vue",
    "vue.js": "vue",
    "angularjs": "angular",
    "html5": "html",
    "css3": "css",
    "tailwind": "tailwind css",
    "tailwindcss": "tailwind css",
    "bootstrap": "bootstrap",
    "fast api": "fastapi",
    "django rest": "django",
    "spring": "spring boot",
    "springboot": "spring boot",
    "express": "express.js",
    "expressjs": "express.js",
    
    # Data & AI
    "ml": "machine learning",
    "machine-learning": "machine learning",
    "ai": "artificial intelligence",
    "artificial-intelligence": "artificial intelligence",
    "dl": "deep learning",
    "deep-learning": "deep learning",
    "nlp": "natural language processing",
    "cv": "computer vision",
    "powerbi": "power bi",
    "power-bi": "power bi",
    "ms excel": "excel",
    "advanced excel": "excel",
    "dsa": "data structures & algorithms",
    "data structure": "data structures & algorithms",
    "data structures": "data structures & algorithms",
    "algorithms": "data structures & algorithms",
    "scikit": "scikit-learn",
    "sklearn": "scikit-learn",
    "tf": "tensorflow",
    "torch": "pytorch",
    "bi": "business intelligence",
    
    # Cloud & DevOps
    "amazon web services": "aws",
    "amazon cloud": "aws",
    "gcp": "google cloud",
    "google cloud platform": "google cloud",
    "ms azure": "azure",
    "k8s": "kubernetes",
    "kube": "kubernetes",
    "ci cd": "ci/cd",
    "cicd": "ci/cd",
    "continuous integration": "ci/cd",
    
    # Databases
    "postgres": "postgresql",
    "psql": "postgresql",
    "mongo": "mongodb",
    "ms sql": "sql server",
    "mssql": "sql server",
    "rdbms": "sql",
    
    # Testing & QA
    "qa": "software testing",
    "quality assurance": "software testing",
    "automation testing": "software testing",
    "test automation": "software testing",
    "manual test": "manual testing",
    
    # Design & Product
    "ui ux": "ui/ux design",
    "ui/ux": "ui/ux design",
    "ui design": "ui/ux design",
    "ux design": "ui/ux design",
    "product design": "ui/ux design",
    
    # Embedded & Hardware
    "embedded c": "embedded systems",
    "microcontroller": "microcontrollers",
    "arduino": "microcontrollers",
    "raspberry pi": "embedded systems"
}


def normalize_skill(raw_skill: str, candidate_pool: list[str] | None = None) -> str:
    """
    Normalizes a single skill string:
    - Lowercases, trims surrounding punctuation and whitespace.
    - Resolves synonyms from SKILL_SYNONYMS dictionary.
    - If candidate_pool is provided, checks for fuzzy matches with similarity > 88%
      to resolve minor spelling mistakes (e.g. 'pyton' -> 'python').
    """
    if not raw_skill or not isinstance(raw_skill, str):
        return ""

    cleaned = raw_skill.strip().lower()
    cleaned = re.sub(r"^[^a-zA-Z0-9+#.]+|[^a-zA-Z0-9+#.]+$", "", cleaned)

    if not cleaned:
        return ""

    # Check direct synonym lookup
    if cleaned in SKILL_SYNONYMS:
        return SKILL_SYNONYMS[cleaned]

    # Optional fuzzy match against existing pool of canonical skills
    if candidate_pool:
        best_match = process.extractOne(cleaned, candidate_pool, scorer=fuzz.ratio)
        if best_match and best_match[1] >= 88:
            return best_match[0]

    return cleaned


def extract_text_from_file(uploaded_file) -> tuple[str, str | None]:
    """
    Extracts text from an uploaded resume file (PDF or TXT).
    Returns a tuple of (extracted_text, error_message).
    If an error occurs, extracted_text will be empty and error_message will explain the issue.
    """
    if uploaded_file is None:
        return "", None

    file_name = uploaded_file.name.lower()
    try:
        if file_name.endswith(".pdf"):
            text_parts = []
            with pdfplumber.open(uploaded_file) as pdf:
                for page_idx, page in enumerate(pdf.pages):
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)
            
            full_text = "\n".join(text_parts).strip()
            if not full_text:
                return "", "The uploaded PDF appears to be empty or contains scanned images without selectable text. Please enter your skills manually."
            return full_text, None

        elif file_name.endswith(".txt"):
            content = uploaded_file.read()
            # Try utf-8 first, fallback to latin-1
            try:
                decoded = content.decode("utf-8")
            except UnicodeDecodeError:
                decoded = content.decode("latin-1")
            return decoded.strip(), None

        else:
            return "", "Unsupported file format. Please upload a PDF (.pdf) or Plain Text (.txt) file."

    except Exception as e:
        return "", f"Could not read file ({str(e)}). Please enter your skills in the text box below instead."


def detect_skills_from_text(text: str, known_skills: set[str] | list[str]) -> list[str]:
    """
    Scans the provided text for occurrences of known skills and synonyms.
    Uses regex word boundaries to avoid false positives (e.g. matching 'c' in 'clean').
    Returns a sorted list of unique canonical skills found in the text.
    """
    if not text:
        return []

    lower_text = " " + text.lower() + " "
    detected = set()

    # Build search list: known skills + all synonym keys
    search_items = set(known_skills)
    for alias in SKILL_SYNONYMS.keys():
        search_items.add(alias)

    for item in search_items:
        clean_item = item.strip().lower()
        if not clean_item or len(clean_item) < 2:
            continue

        # Regex pattern with word boundaries, taking care of special characters like +, #, .
        escaped = re.escape(clean_item)
        pattern = rf"(?<![a-zA-Z0-9]){escaped}(?![a-zA-Z0-9])"

        if re.search(pattern, lower_text):
            canonical = normalize_skill(clean_item)
            if canonical:
                detected.add(canonical)

    return sorted(list(detected))


def calculate_role_skill_frequencies(jobs_for_role_df) -> dict[str, float]:
    """
    Calculates how frequently each skill is required for a specific role across all postings.
    Returns a dictionary of {skill_name: frequency_weight} sorted in descending order of frequency.
    """
    if jobs_for_role_df.empty:
        return {}

    total_postings = len(jobs_for_role_df)
    skill_counts = {}

    for skills_val in jobs_for_role_df["required_skills"]:
        if pd.isna(skills_val) or not str(skills_val).strip():
            continue
        skills_list = [s.strip().lower() for s in str(skills_val).split(",") if s.strip()]
        for s in set(skills_list):  # Set to count once per job posting
            normalized = normalize_skill(s)
            skill_counts[normalized] = skill_counts.get(normalized, 0) + 1

    # Frequency weight is the percentage of postings requiring that skill
    frequencies = {skill: round(count / total_postings, 3) for skill, count in skill_counts.items()}
    # Sort by frequency descending
    sorted_freq = dict(sorted(frequencies.items(), key=lambda item: item[1], reverse=True))
    return sorted_freq


def calculate_skill_match(user_skills: list[str], role_skill_weights: dict[str, float]) -> tuple[float, list[str], list[tuple[str, float]]]:
    """
    Computes the weighted skill match percentage for the target role.
    
    Formula:
    Match Score = (Sum of weights of matched skills / Sum of all weights of required skills for role) * 100
    
    Returns:
        tuple: (match_score_pct, matched_skills_list, missing_skills_ranked_list)
    """
    if not role_skill_weights:
        return 0.0, [], []

    normalized_user_skills = set(normalize_skill(s) for s in user_skills if s.strip())

    total_possible_weight = sum(role_skill_weights.values())
    matched_weight = 0.0
    matched_skills = []
    missing_skills = []

    for skill, weight in role_skill_weights.items():
        if skill in normalized_user_skills:
            matched_weight += weight
            matched_skills.append(skill)
        else:
            missing_skills.append((skill, weight))

    match_percentage = round((matched_weight / total_possible_weight) * 100, 1) if total_possible_weight > 0 else 0.0
    match_percentage = min(100.0, max(0.0, match_percentage))

    # Missing skills are already ordered by demand weight descending
    return match_percentage, matched_skills, missing_skills


def calculate_achievement_bonus(achievements_text: str) -> tuple[float, dict[str, int]]:
    """
    Analyzes the achievements text (projects, certifications, internships, hackathons, awards).
    Awards bonus points:
    - Projects: +3% each (max 6%)
    - Certifications: +3% each (max 6%)
    - Internships: +4% each (max 8%)
    - Hackathons & Awards: +3% each (max 6%)
    
    The total achievement bonus is capped strictly at 15.0%.
    
    Returns:
        tuple: (bonus_points, breakdown_counts_dict)
    """
    if not achievements_text or not achievements_text.strip():
        return 0.0, {"projects": 0, "certifications": 0, "internships": 0, "hackathons": 0}

    lines = [line.strip().lower() for line in achievements_text.split("\n") if line.strip()]

    counts = {
        "projects": 0,
        "certifications": 0,
        "internships": 0,
        "hackathons": 0
    }

    # Keyword patterns for category detection
    project_kw = [r"project", r"portfolio", r"built\b", r"developed\b", r"created\b", r"capstone", r"github\.com"]
    cert_kw = [r"certif", r"license", r"badge", r"nptel", r"coursera", r"udemy", r"aws certified", r"microsoft certified"]
    intern_kw = [r"intern\b", r"internship", r"trainee", r"apprentice", r"fellowship"]
    hackathon_kw = [r"hackathon", r"award", r"winner", r"runner.*up", r"first place", r"ranked", r"contest", r"competition", r"published", r"paper"]

    for line in lines:
        matched = False
        if any(re.search(kw, line) for kw in intern_kw):
            counts["internships"] += 1
            matched = True
        elif any(re.search(kw, line) for kw in hackathon_kw):
            counts["hackathons"] += 1
            matched = True
        elif any(re.search(kw, line) for kw in cert_kw):
            counts["certifications"] += 1
            matched = True
        elif any(re.search(kw, line) for kw in project_kw):
            counts["projects"] += 1
            matched = True
        
        # If no specific keyword matched, treat as project if length > 10 chars
        if not matched and len(line) >= 10:
            counts["projects"] += 1

    # Point calculations
    pts_projects = min(6.0, counts["projects"] * 3.0)
    pts_certs = min(6.0, counts["certifications"] * 3.0)
    pts_interns = min(8.0, counts["internships"] * 4.0)
    pts_hacks = min(6.0, counts["hackathons"] * 3.0)

    total_bonus = min(15.0, pts_projects + pts_certs + pts_interns + pts_hacks)
    return round(total_bonus, 1), counts


def calculate_career_readiness(
    user_skills: list[str],
    role_skill_weights: dict[str, float],
    achievements_text: str = ""
) -> dict:
    """
    Computes complete Career Readiness score combining:
    1. Skill Match Score (weighted percentage of target role skills)
    2. Achievement Bonus (up to 15% extra)
    
    Labels:
    - 0 to 39%: 'Beginner'
    - 40 to 69%: 'Developing'
    - 70 to 84%: 'Job-Ready'
    - 85 to 100%: 'Strong Candidate'
    
    Returns a comprehensive dict with score, label, matched skills, missing skills, and bonus breakdown.
    """
    skill_match_pct, matched, missing = calculate_skill_match(user_skills, role_skill_weights)
    achievement_bonus, ach_counts = calculate_achievement_bonus(achievements_text)

    readiness_score = min(100.0, round(skill_match_pct + achievement_bonus, 1))

    # Determine readiness label
    if readiness_score < 40.0:
        label = "Beginner"
        color = "#EF4444"  # Red
        badge = "🌱 Beginner"
        summary = "You are at the foundation stage. Focus on core technical requirements to unlock entry-level roles."
    elif readiness_score < 70.0:
        label = "Developing"
        color = "#F59E0B"  # Amber
        badge = "🚀 Developing"
        summary = "You have solid foundational skills! Closing your top missing skills will quickly make you job-ready."
    elif readiness_score < 85.0:
        label = "Job-Ready"
        color = "#10B981"  # Emerald
        badge = "🎯 Job-Ready"
        summary = "You match the primary requirements for this role! Start applying and sharpening interview prep."
    else:
        label = "Strong Candidate"
        color = "#0D9488"  # Teal
        badge = "⭐ Strong Candidate"
        summary = "Outstanding profile! Your skills and achievements place you among top competitive candidates."

    return {
        "readiness_score": readiness_score,
        "skill_match_pct": skill_match_pct,
        "achievement_bonus": achievement_bonus,
        "achievement_counts": ach_counts,
        "label": label,
        "color": color,
        "badge": badge,
        "summary": summary,
        "matched_skills": matched,
        "missing_skills": missing  # List of tuples: [(skill, weight), ...]
    }