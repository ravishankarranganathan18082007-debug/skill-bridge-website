"""
data_loader.py - Job Data Ingestion, Column Mapping, Cleaning & SQLite Storage
This module handles:
1. Scanning the /data directory for any CSV and Excel (.xlsx, .xls) files.
2. Gracefully mapping inconsistent column headers using flexible keyword matching.
3. Cleaning and standardizing job fields, skills, and missing values.
4. Auto-generating a realistic 100+ row Indian/global tech dataset if no files are provided.
5. Persisting everything into a local SQLite database (skillbridge.db) and serving query helpers.
"""

import os
import re
import glob
import sqlite3
import random
from datetime import datetime, timedelta
import pandas as pd


# Expected standard schema for jobs inside SQLite and throughout the app
STANDARD_COLUMNS = [
    "job_title",
    "company",
    "location",
    "required_skills",  # comma-separated string of cleaned lowercase skills
    "salary",
    "experience",
    "number_of_openings",
    "posted_date",
    "job_link",
    "industry"
]

# Keyword dictionary to match various column names found in scraped or downloaded CSVs/XLSX
COLUMN_PATTERNS = {
    "job_title": [r"job.*title", r"title", r"^role", r"position", r"designation", r"job.*role"],
    "company": [r"company.*name", r"company", r"employer", r"organization", r"org", r"hiring.*company"],
    "location": [r"job.*location", r"work.*location", r"location", r"city", r"place", r"workplace"],
    "required_skills": [r"required.*skill", r"key.*skill", r"skill", r"skills", r"tech.*stack", r"technologies", r"mandatory.*skills"],
    "salary": [r"salary.*range", r"salary", r"ctc", r"package", r"compensation", r"pay", r"remuneration"],
    "experience": [r"experience.*required", r"years.*experience", r"experience", r"exp", r"exp.*level", r"min.*exp"],
    "number_of_openings": [r"number.*openings", r"openings", r"vacancies", r"positions", r"open.*positions", r"headcount"],
    "posted_date": [r"posted.*date", r"date.*posted", r"posted.*on", r"posting.*date", r"created.*at", r"date"],
    "job_link": [r"job.*link", r"job.*url", r"apply.*link", r"link", r"url", r"apply.*url"],
    "industry": [r"industry", r"sector", r"domain", r"category", r"business.*unit"]
}


def match_column_name(raw_col_name: str) -> str | None:
    """
    Match an arbitrary column header name to our standard schema using regex patterns.
    Example: 'Job Title Name' -> 'job_title', 'Key_Skills' -> 'required_skills'
    """
    clean_raw = raw_col_name.strip().lower().replace("_", " ")
    for standard_col, patterns in COLUMN_PATTERNS.items():
        for pat in patterns:
            if re.search(pat, clean_raw):
                return standard_col
    return None


def clean_skill_string(skill_text) -> str:
    """
    Takes a raw string of skills (e.g. 'Python, SQL; React | Docker')
    splits by separators, trims, lowercases, removes blanks, and rejoins as clean comma-separated string.
    """
    if pd.isna(skill_text) or not str(skill_text).strip():
        return ""
    
    # Split by comma, semicolon, pipe, forward slash, or newline
    tokens = re.split(r"[,;|/\n]+", str(skill_text))
    cleaned_tokens = []
    seen = set()
    for tok in tokens:
        item = tok.strip().lower()
        # Remove surrounding punctuation
        item = re.sub(r"^[^a-zA-Z0-9+#]+|[^a-zA-Z0-9+#]+$", "", item)
        if item and len(item) > 1 and item not in seen:
            seen.add(item)
            cleaned_tokens.append(item)
            
    return ", ".join(cleaned_tokens)


def generate_sample_dataset() -> pd.DataFrame:
    """
    Auto-generates a realistic sample dataset with 100+ job postings across 10 roles,
    using well-known Indian and global tech companies and locations like Chennai, Bengaluru, etc.
    """
    roles_data = {
        "Data Analyst": {
            "skills": ["python", "sql", "power bi", "excel", "tableau", "statistics", "pandas"],
            "industry": "Analytics & BI",
            "base_salary": "₹5,00,000 - ₹9,00,000"
        },
        "Python Developer": {
            "skills": ["python", "django", "fastapi", "sql", "git", "rest api", "docker", "postgresql"],
            "industry": "Software Engineering",
            "base_salary": "₹6,00,000 - ₹11,00,000"
        },
        "Web Developer": {
            "skills": ["html", "css", "javascript", "react", "node.js", "git", "typescript", "tailwind"],
            "industry": "Web & Cloud Services",
            "base_salary": "₹5,50,000 - ₹10,00,000"
        },
        "Software Tester": {
            "skills": ["software testing", "selenium", "manual testing", "python", "jira", "sql", "api testing"],
            "industry": "Quality Assurance",
            "base_salary": "₹4,50,000 - ₹8,00,000"
        },
        "Data Scientist": {
            "skills": ["python", "machine learning", "deep learning", "sql", "pandas", "numpy", "statistics", "scikit-learn"],
            "industry": "AI & Advanced Analytics",
            "base_salary": "₹8,00,000 - ₹15,00,000"
        },
        "Cloud Engineer": {
            "skills": ["aws", "azure", "docker", "kubernetes", "linux", "git", "terraform", "ci/cd"],
            "industry": "Cloud Infrastructure",
            "base_salary": "₹7,50,000 - ₹14,00,000"
        },
        "Cybersecurity Analyst": {
            "skills": ["cybersecurity", "networking", "linux", "python", "ethical hacking", "siem", "wireshark"],
            "industry": "Information Security",
            "base_salary": "₹6,50,000 - ₹12,00,000"
        },
        "UI/UX Designer": {
            "skills": ["ui/ux design", "figma", "wireframing", "prototyping", "user research", "html", "css"],
            "industry": "Design & Product",
            "base_salary": "₹5,00,000 - ₹9,50,000"
        },
        "Embedded Engineer": {
            "skills": ["embedded systems", "c", "c++", "microcontrollers", "rtos", "linux", "pcb design"],
            "industry": "Hardware & IoT",
            "base_salary": "₹6,00,000 - ₹11,00,000"
        },
        "Business Analyst": {
            "skills": ["business analysis", "sql", "excel", "agile", "jira", "power bi", "requirements gathering"],
            "industry": "Management Consulting & IT",
            "base_salary": "₹6,00,000 - ₹10,50,000"
        }
    }

    companies = [
        "Tata Consultancy Services (TCS)", "Infosys", "Wipro", "Zoho Corporation",
        "Google", "Microsoft", "Amazon", "Accenture", "Swiggy", "Flipkart",
        "HCLTech", "Cognizant", "Razorpay", "PhonePe", "Capgemini", "Dell Technologies",
        "Cisco Systems", "L&T Technology Services", "Freshworks", "Paytm"
    ]

    locations = ["Chennai", "Bengaluru", "Hyderabad", "Pune", "Mumbai", "Remote"]
    exp_levels = ["Fresher", "1-3 years", "3+ years"]

    rows = []
    # Seed for consistent yet varied demo generation
    random.seed(42)

    today = datetime.now()

    for role_name, info in roles_data.items():
        # Generate 10 to 11 listings per role for a total of ~105 records
        num_jobs_for_role = 11
        for i in range(num_jobs_for_role):
            comp = random.choice(companies)
            loc = random.choice(locations)
            exp = random.choice(exp_levels)
            openings = random.choice([1, 2, 2, 3, 4, 5, 8])
            
            # Select core skills plus 1-2 random variations from role's skills
            pool = list(info["skills"])
            random.shuffle(pool)
            selected_skills = pool[:random.randint(4, len(pool))]
            skills_str = ", ".join(selected_skills)

            # Random posting date within past 30 days
            posted = (today - timedelta(days=random.randint(1, 28))).strftime("%Y-%m-%d")
            
            job_link = f"https://careers.{comp.split()[0].lower().replace('(', '')}.com/jobs/{random.randint(10000, 99999)}"

            rows.append({
                "job_title": role_name,
                "company": comp,
                "location": loc,
                "required_skills": skills_str,
                "salary": info["base_salary"],
                "experience": exp,
                "number_of_openings": openings,
                "posted_date": posted,
                "job_link": job_link,
                "industry": info["industry"]
            })

    df = pd.DataFrame(rows)
    return df


def load_and_process_jobs(data_dir: str = "data", db_path: str = "skillbridge.db") -> tuple[pd.DataFrame, bool]:
    """
    Scans the data_dir for all CSV and XLSX files.
    - If files are found, reads each file, applies flexible column mapping,
      merges them, cleans the data, and stores in SQLite.
    - If no files found or data_dir is empty, generates the sample demo dataset.
    
    Returns:
        tuple (pd.DataFrame, bool): Processed DataFrame and is_sample_data boolean flag.
    """
    if not os.path.exists(data_dir):
        os.makedirs(data_dir, exist_ok=True)

    csv_files = glob.glob(os.path.join(data_dir, "*.csv"))
    xlsx_files = glob.glob(os.path.join(data_dir, "*.xlsx")) + glob.glob(os.path.join(data_dir, "*.xls"))
    all_files = csv_files + xlsx_files

    is_sample_data = False
    merged_dfs = []

    if not all_files:
        # Fallback to realistic sample dataset
        is_sample_data = True
        df = generate_sample_dataset()
        merged_dfs.append(df)
    else:
        for f in all_files:
            try:
                if f.endswith(".csv"):
                    # Try reading with common encodings
                    try:
                        raw_df = pd.read_csv(f, encoding="utf-8")
                    except UnicodeDecodeError:
                        raw_df = pd.read_csv(f, encoding="latin1")
                else:
                    raw_df = pd.read_excel(f)

                if raw_df.empty:
                    continue

                # Map columns dynamically
                mapped_data = {}
                used_raw_cols = set()

                for std_col in STANDARD_COLUMNS:
                    matched = False
                    for raw_col in raw_df.columns:
                        if raw_col in used_raw_cols:
                            continue
                        if match_column_name(str(raw_col)) == std_col:
                            mapped_data[std_col] = raw_df[raw_col]
                            used_raw_cols.add(raw_col)
                            matched = True
                            break
                    if not matched:
                        # Graceful fallback for missing columns
                        if std_col == "number_of_openings":
                            mapped_data[std_col] = 1
                        elif std_col == "posted_date":
                            mapped_data[std_col] = datetime.now().strftime("%Y-%m-%d")
                        elif std_col == "job_link":
                            mapped_data[std_col] = "https://www.linkedin.com/jobs/"
                        else:
                            mapped_data[std_col] = "Not specified"

                standardized_df = pd.DataFrame(mapped_data)
                merged_dfs.append(standardized_df)

            except Exception as e:
                # Log or print error, don't crash
                print(f"Warning: Could not read file {f}: {e}")

        if not merged_dfs:
            is_sample_data = True
            df = generate_sample_dataset()
            merged_dfs.append(df)

    final_df = pd.concat(merged_dfs, ignore_index=True)

    # Clean fields
    final_df["job_title"] = final_df["job_title"].fillna("Not specified").astype(str).str.strip()
    final_df["company"] = final_df["company"].fillna("Not specified").astype(str).str.strip()
    final_df["location"] = final_df["location"].fillna("Anywhere").astype(str).str.strip()
    final_df["salary"] = final_df["salary"].fillna("Not specified").astype(str).str.strip()
    final_df["experience"] = final_df["experience"].fillna("Fresher").astype(str).str.strip()
    final_df["industry"] = final_df["industry"].fillna("Technology").astype(str).str.strip()
    final_df["job_link"] = final_df["job_link"].fillna("#").astype(str).str.strip()

    # Clean numeric openings
    final_df["number_of_openings"] = pd.to_numeric(
        final_df["number_of_openings"], errors="coerce"
    ).fillna(1).astype(int)
    # Ensure openings is at least 1
    final_df["number_of_openings"] = final_df["number_of_openings"].apply(lambda x: max(1, x))

    # Standardize skills column
    final_df["required_skills"] = final_df["required_skills"].apply(clean_skill_string)

    # Standardize dates
    def sanitize_date(d):
        try:
            parsed = pd.to_datetime(d)
            return parsed.strftime("%Y-%m-%d")
        except Exception:
            return datetime.now().strftime("%Y-%m-%d")

    final_df["posted_date"] = final_df["posted_date"].apply(sanitize_date)

    # Remove duplicates
    final_df = final_df.drop_duplicates(subset=["job_title", "company", "location"]).reset_index(drop=True)

    # Persist to SQLite
    save_to_sqlite(final_df, db_path=db_path)

    return final_df, is_sample_data


def save_to_sqlite(df: pd.DataFrame, db_path: str = "skillbridge.db"):
    """
    Saves the processed job DataFrame into SQLite database.
    Creates table 'jobs' and indexes for fast searching.
    """
    conn = sqlite3.connect(db_path)
    df.to_sql("jobs", conn, if_exists="replace", index=False)
    
    # Create indexes for performant queries
    cursor = conn.cursor()
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_job_title ON jobs(job_title)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_company ON jobs(company)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_location ON jobs(location)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_experience ON jobs(experience)")
    conn.commit()
    conn.close()


def get_all_jobs(db_path: str = "skillbridge.db") -> pd.DataFrame:
    """Fetch all jobs from the SQLite database."""
    conn = sqlite3.connect(db_path)
    try:
        df = pd.read_sql_query("SELECT * FROM jobs", conn)
    except Exception:
        df = pd.DataFrame(columns=STANDARD_COLUMNS)
    finally:
        conn.close()
    return df


def get_unique_roles(db_path: str = "skillbridge.db") -> list[str]:
    """Retrieve distinct list of job roles present in the database."""
    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT job_title FROM jobs WHERE job_title != 'Not specified' ORDER BY job_title")
        roles = [row[0] for row in cursor.fetchall() if row[0]]
    except Exception:
        roles = []
    finally:
        conn.close()
    return roles


def get_unique_locations(db_path: str = "skillbridge.db") -> list[str]:
    """Retrieve distinct list of locations present in the database."""
    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT location FROM jobs WHERE location != 'Not specified' ORDER BY location")
        locs = [row[0] for row in cursor.fetchall() if row[0]]
    except Exception:
        locs = []
    finally:
        conn.close()
    return locs


def get_unique_experience_levels(db_path: str = "skillbridge.db") -> list[str]:
    """Retrieve distinct experience levels present in the database."""
    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT experience FROM jobs WHERE experience != 'Not specified' ORDER BY experience")
        exps = [row[0] for row in cursor.fetchall() if row[0]]
    except Exception:
        exps = []
    finally:
        conn.close()
    return exps if exps else ["Fresher", "1-3 years", "3+ years"]


def get_jobs_for_role(role: str, db_path: str = "skillbridge.db") -> pd.DataFrame:
    """Fetch jobs matching a specific target role."""
    conn = sqlite3.connect(db_path)
    try:
        query = "SELECT * FROM jobs WHERE LOWER(job_title) = LOWER(?)"
        df = pd.read_sql_query(query, conn, params=(role,))
    except Exception:
        df = pd.DataFrame(columns=STANDARD_COLUMNS)
    finally:
        conn.close()
    return df


def get_all_job_skills(db_path: str = "skillbridge.db") -> set[str]:
    """Extract a set of all unique skills mentioned across all job postings in the database."""
    conn = sqlite3.connect(db_path)
    all_skills = set()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT required_skills FROM jobs")
        for row in cursor.fetchall():
            if row[0]:
                for s in row[0].split(","):
                    val = s.strip().lower()
                    if val:
                        all_skills.add(val)
    except Exception:
        pass
    finally:
        conn.close()
    return all_skills