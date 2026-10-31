"""
resources.py - Curated Free Learning Resources
This module provides a rich repository of high-quality, free learning resources
(YouTube tutorials, freeCodeCamp courses, Coursera audit links, NPTEL, Kaggle,
and official documentation) for top industry skills, plus a dynamic fallback generator.
"""

import urllib.parse

# Curated free learning resources for at least 35 popular tech and data skills.
# Each entry includes:
# - platform: The website or organization hosting the resource
# - title: Name of the course or tutorial
# - url: Direct link to access the material for free
# - type: Format (Video Course, Interactive, Documentation, Audit Course)
SKILL_RESOURCES = {
    "python": {
        "platform": "freeCodeCamp",
        "title": "Scientific Computing with Python & Full Course",
        "url": "https://www.freecodecamp.org/learn/scientific-computing-with-python/",
        "type": "Interactive Course"
    },
    "sql": {
        "platform": "Kaggle Learn",
        "title": "Intro to SQL & Advanced SQL Micro-Courses",
        "url": "https://www.kaggle.com/learn/intro-to-sql",
        "type": "Interactive Tutorials"
    },
    "machine learning": {
        "platform": "Coursera (Audit)",
        "title": "Machine Learning Specialization by Andrew Ng (Audit for Free)",
        "url": "https://www.coursera.org/specializations/machine-learning-introduction",
        "type": "Audit / Free Videos"
    },
    "deep learning": {
        "platform": "fast.ai",
        "title": "Practical Deep Learning for Coders",
        "url": "https://course.fast.ai/",
        "type": "Comprehensive Free Course"
    },
    "data science": {
        "platform": "freeCodeCamp",
        "title": "Data Analysis with Python Certification",
        "url": "https://www.freecodecamp.org/learn/data-analysis-with-python/",
        "type": "Hands-on Projects"
    },
    "pandas": {
        "platform": "Kaggle Learn",
        "title": "Pandas Data Manipulation Course",
        "url": "https://www.kaggle.com/learn/pandas",
        "type": "Interactive Exercises"
    },
    "numpy": {
        "platform": "Official Docs",
        "title": "NumPy Quickstart & Absolute Beginners Guide",
        "url": "https://numpy.org/doc/stable/user/absolute_beginners.html",
        "type": "Documentation"
    },
    "power bi": {
        "platform": "Microsoft Learn",
        "title": "Microsoft Power BI Data Analyst Guided Learning",
        "url": "https://learn.microsoft.com/en-us/training/powerplatform/power-bi",
        "type": "Free Official Modules"
    },
    "tableau": {
        "platform": "Tableau Free Training",
        "title": "Tableau Free Starter Training Videos",
        "url": "https://www.tableau.com/learn/training/2022-1",
        "type": "Video Tutorials"
    },
    "excel": {
        "platform": "Excel Easy",
        "title": "Excel Basics to Advanced Master Guide",
        "url": "https://www.excel-easy.com/",
        "type": "Tutorials & Examples"
    },
    "javascript": {
        "platform": "The Odin Project",
        "title": "Full Stack JavaScript Track",
        "url": "https://www.theodinproject.com/paths/full-stack-javascript",
        "type": "Curated Open Curriculum"
    },
    "typescript": {
        "platform": "TypeScript Official Docs",
        "title": "TypeScript Handbook for JavaScript Developers",
        "url": "https://www.typescriptlang.org/docs/handbook/intro.html",
        "type": "Documentation"
    },
    "react": {
        "platform": "React Docs",
        "title": "React.dev Learn: Modern Interactive React",
        "url": "https://react.dev/learn",
        "type": "Interactive Docs"
    },
    "html": {
        "platform": "MDN Web Docs",
        "title": "HTML: Structuring the Web on Mozilla MDN",
        "url": "https://developer.mozilla.org/en-US/docs/Learn/HTML",
        "type": "Interactive Guides"
    },
    "css": {
        "platform": "web.dev",
        "title": "Learn CSS by Google Web Dev Team",
        "url": "https://web.dev/learn/css/",
        "type": "Interactive Modules"
    },
    "node.js": {
        "platform": "Node.js Learn",
        "title": "Official Node.js Learning Guides",
        "url": "https://nodejs.org/en/learn",
        "type": "Official Tutorials"
    },
    "git": {
        "platform": "Pro Git Book",
        "title": "Pro Git by Scott Chacon and Ben Straub (Free Book)",
        "url": "https://git-scm.com/book/en/v2",
        "type": "Free Online Book"
    },
    "docker": {
        "platform": "Docker Docs",
        "title": "Getting Started with Containers on Docker Docs",
        "url": "https://docs.docker.com/get-started/",
        "type": "Hands-on Guide"
    },
    "kubernetes": {
        "platform": "Kubernetes.io",
        "title": "Kubernetes Interactive Tutorials & Katacoda Labs",
        "url": "https://kubernetes.io/docs/tutorials/",
        "type": "Interactive Labs"
    },
    "aws": {
        "platform": "AWS Skill Builder",
        "title": "AWS Cloud Essentials & Foundations (Free Tier)",
        "url": "https://explore.skillbuilder.aws/learn",
        "type": "Self-paced Training"
    },
    "azure": {
        "platform": "Microsoft Learn",
        "title": "Azure Fundamentals Learning Path (AZ-900)",
        "url": "https://learn.microsoft.com/en-us/training/paths/azure-fundamentals/",
        "type": "Modular Course"
    },
    "linux": {
        "platform": "Linux Journey",
        "title": "Linux Journey: Grasshopper to Penguin Mastery",
        "url": "https://linuxjourney.com/",
        "type": "Free Interactive Lessons"
    },
    "data structures & algorithms": {
        "platform": "NeetCode / freeCodeCamp",
        "title": "DSA Algorithms & Data Structures Roadmap",
        "url": "https://neetcode.io/roadmap",
        "type": "Visual Practice Roadmap"
    },
    "java": {
        "platform": "MOOC.fi",
        "title": "University of Helsinki Java Programming I & II",
        "url": "https://java-programming.mooc.fi/",
        "type": "Comprehensive Open Course"
    },
    "c++": {
        "platform": "LearnCpp.com",
        "title": "Comprehensive Modern C++ Guide",
        "url": "https://www.learncpp.com/",
        "type": "Free In-Depth Tutorials"
    },
    "c#": {
        "platform": "Microsoft Learn",
        "title": "Foundational C# Certification with freeCodeCamp",
        "url": "https://www.freecodecamp.org/learn/foundational-c-sharp-with-microsoft/",
        "type": "Certified Free Program"
    },
    "fastapi": {
        "platform": "FastAPI Official",
        "title": "FastAPI Interactive Tutorial & Documentation",
        "url": "https://fastapi.tiangolo.com/tutorial/",
        "type": "Step-by-Step Docs"
    },
    "django": {
        "platform": "Django Project",
        "title": "Writing Your First Django App Official Tutorial",
        "url": "https://docs.djangoproject.com/en/stable/intro/tutorial01/",
        "type": "Official Tutorial"
    },
    "spring boot": {
        "platform": "Spring.io",
        "title": "Building a RESTful Web Service with Spring Boot",
        "url": "https://spring.io/guides/gs/rest-service/",
        "type": "Official Quickstart"
    },
    "mongodb": {
        "platform": "MongoDB University",
        "title": "MongoDB Basics & Developer Learning Path",
        "url": "https://learn.mongodb.com/",
        "type": "Free Guided Courses"
    },
    "postgresql": {
        "platform": "PostgreSQL Tutorial",
        "title": "PostgreSQL Mastery for Beginners and Pros",
        "url": "https://www.postgresqltutorial.com/",
        "type": "Free Structured Guide"
    },
    "cybersecurity": {
        "platform": "TryHackMe & NPTEL",
        "title": "TryHackMe Pre-Security & NPTEL Information Security",
        "url": "https://tryhackme.com/path/outline/pre-security",
        "type": "Gamified Hands-on Labs"
    },
    "ui/ux design": {
        "platform": "Figma Learn",
        "title": "Figma for Beginners & Design Systems Guide",
        "url": "https://help.figma.com/hc/en-us/categories/360002051613-Learn-design",
        "type": "Video Series & Templates"
    },
    "software testing": {
        "platform": "Guru99 / Ministry of Testing",
        "title": "Manual & Automated Testing Full Course",
        "url": "https://www.guru99.com/software-testing.html",
        "type": "Comprehensive Tutorials"
    },
    "selenium": {
        "platform": "Selenium.dev",
        "title": "Selenium WebDriver Official Documentation & Labs",
        "url": "https://www.selenium.dev/documentation/",
        "type": "Official Docs"
    },
    "embedded systems": {
        "platform": "NPTEL",
        "title": "Embedded System Design by IIT Kharagpur (NPTEL)",
        "url": "https://nptel.ac.in/courses/106105159",
        "type": "University Lectures"
    },
    "business analysis": {
        "platform": "Coursera (Audit)",
        "title": "Agile Business Analysis & Scrum Fundamentals",
        "url": "https://www.coursera.org/learn/agile-at-work",
        "type": "Free Audit Course"
    },
    "natural language processing": {
        "platform": "Hugging Face",
        "title": "The Hugging Face NLP Course",
        "url": "https://huggingface.co/learn/nlp-course/",
        "type": "Hands-on Code & Transformers"
    },
    "computer vision": {
        "platform": "OpenCV.org",
        "title": "OpenCV Python Tutorials & Image Processing",
        "url": "https://docs.opencv.org/4.x/d6/d00/tutorial_py_root.html",
        "type": "Hands-on Code Examples"
    },
    "statistics": {
        "platform": "Khan Academy",
        "title": "Statistics and Probability for Data Science",
        "url": "https://www.khanacademy.org/math/statistics-probability",
        "type": "Interactive Practice"
    }
}


def get_skill_resource(skill_name: str) -> dict:
    """
    Look up learning resources for a given skill.
    If the skill is in our curated dictionary, returns the verified link.
    Otherwise, generates a reliable free tutorial search link on YouTube / freeCodeCamp.
    
    Parameters:
        skill_name (str): The name of the skill (e.g., 'Python', 'Docker', 'GraphQL')
        
    Returns:
        dict: Containing 'platform', 'title', 'url', and 'type'
    """
    cleaned_name = skill_name.strip().lower()

    # Direct match in dictionary
    if cleaned_name in SKILL_RESOURCES:
        res = SKILL_RESOURCES[cleaned_name].copy()
        res["skill"] = skill_name.title()
        return res

    # Check partial match (e.g. 'c++ programming' -> 'c++', 'reactjs' -> 'react')
    for key, val in SKILL_RESOURCES.items():
        if key in cleaned_name or cleaned_name in key:
            res = val.copy()
            res["skill"] = skill_name.title()
            return res

    # Generic fallback: Search on YouTube and freeCodeCamp
    encoded_query = urllib.parse.quote_plus(f"{skill_name} full course tutorial beginner")
    fallback_url = f"https://www.youtube.com/results?search_query={encoded_query}"

    return {
        "skill": skill_name.title(),
        "platform": "YouTube / Community Guides",
        "title": f"Master {skill_name.title()} from Scratch (Free Video Bootcamp)",
        "url": fallback_url,
        "type": "Free Video Search"
    }