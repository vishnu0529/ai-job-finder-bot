CANDIDATE = {
    "name":       "Vishnu Kanth Suryanarayan",
    "email":      "vishnuks0529@gmail.com",
    "phone":      "+44 7344 701151",
    "location":   "London, UK",
    "linkedin":   "linkedin.com/in/vishnu-kanth-suryanarayan-a68851167",
    "github":     "github.com/vishnu0529",
    "visa":       "UK Student Visa (20 hrs/week). Graduate Visa eligible Oct 2026.",
    "availability": "Part-time until Sep 2026. Full-time from Oct 2026.",

    "summary": (
        "AI Engineer completing an MSc in Artificial Intelligence & Robotics at the University "
        "of Hertfordshire (Sep 2026). Built and shipped a live production 4-step agentic LLM "
        "system (AI Resume Matcher) using Google Gemini 2.5 Flash, FastAPI, and Railway CI/CD. "
        "Background in enterprise digital delivery at Deloitte Digital."
    ),

    "skills": [
        "Python", "FastAPI", "LangChain", "LangGraph", "RAG", "FAISS", "ChromaDB",
        "HuggingFace Transformers", "DistilBERT", "BERT", "PyTorch", "scikit-learn",
        "NLP", "Prompt Engineering", "Agentic AI", "LLM Orchestration",
        "Google Gemini API", "Anthropic Claude API", "Pydantic", "Docker",
        "GitHub Actions", "CI/CD", "Railway", "Streamlit", "pandas", "NumPy",
        "SQL", "REST APIs", "Microservices", "Git",
    ],

    "experience": [
        "Senior Consultant at Deloitte Digital (Jun 2024 – Sep 2025) — enterprise digital platforms",
        "Front-End Engineer at PinkLemonade (Nov 2021 – Jul 2023)",
    ],

    "projects": [
        "AI Resume Matcher: live 4-step agentic LLM system (Gemini 2.5 Flash, FastAPI, Railway)",
        "Agentic Sports Intelligence API: multi-agent RAG with LangGraph + FAISS",
        "Employee Sentiment Analysis: BERT + VADER NLP pipeline on 2,200 emails",
        "Phishing Email Detection (MSc): Random Forest vs DistilBERT comparison (in progress)",
    ],

    "target_roles": [
        "AI Engineer", "ML Engineer", "NLP Engineer", "Applied AI Engineer",
        "LLM Engineer", "Generative AI Engineer", "Junior AI Engineer",
        "Machine Learning Engineer", "AI Developer",
    ],

    "target_locations": ["London", "Remote", "Hybrid", "UK"],
    "min_salary_gbp": 45000,
}

import os as _os

# Job boards — keys loaded from .env automatically
SOURCES = {
    "remotive":  {"enabled": True,  "key": ""},
    "linkedin":  {"enabled": True,  "key": ""},
    "arbeitnow": {"enabled": True,  "key": ""},
    "reed":      {"enabled": bool(_os.getenv("REED_API_KEY")), "key": _os.getenv("REED_API_KEY", "")},
    "adzuna":    {"enabled": False,  "key": _os.getenv("ADZUNA_APP_KEY", ""), "id": _os.getenv("ADZUNA_APP_ID", "")},
}
