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
        "Independent AI Consultant with a professional background as a Senior Consultant at "
        "Deloitte Digital, delivering enterprise digital platforms. Currently building AI Business "
        "Automation Hub, a multi-agent LangGraph SaaS platform for SME workflow automation, "
        "alongside an AI Resume Matcher (FastAPI, Anthropic Claude, FAISS) and this AI Job Finder "
        "Bot (LangGraph orchestration, Gemini-powered scoring, real UK sponsor-register checks). "
        "Completing an MSc in Artificial Intelligence & Robotics at the University of Hertfordshire "
        "(Sep 2026)."
    ),

    "skills": [
        "Python", "FastAPI", "LangChain", "RAG", "FAISS", "Qdrant",
        "HuggingFace Transformers", "DistilBERT", "BERT", "PyTorch", "scikit-learn",
        "NLP", "Prompt Engineering", "LLM Orchestration",
        "Google Gemini API", "Anthropic Claude API", "Pydantic", "Docker",
        "GitHub Actions", "CI/CD", "Streamlit", "pandas", "NumPy",
        "SQL", "REST APIs", "Microservices", "Git",
    ],

    "experience": [
        "Independent AI Consultant (Sep 2026 – present) — building AI Business Automation Hub, "
        "a SaaS platform for SME workflow automation with multi-agent LangGraph orchestration "
        "(supervisor + specialist agents, RAG-backed knowledge base, n8n integration)",
        "Senior Consultant at Deloitte Digital (Jun 2024 – Sep 2025) — enterprise digital platforms",
        "Front-End Engineer at PinkLemonade (Nov 2021 – Jul 2023)",
    ],

    "projects": [
        "AI Business Automation Hub: multi-agent SaaS platform for SME workflow automation — "
        "LangGraph supervisor routing to specialist agents, RAG-backed knowledge base, n8n "
        "integration, FastAPI + Next.js",
        "AI Resume Matcher: FastAPI service matching resumes to job descriptions using FAISS "
        "semantic similarity + Anthropic Claude for skills-gap analysis",
        "AI Job Finder Bot: this project — multi-source job search, Gemini-based match scoring, "
        "automated cover letters, real UK sponsor-register checks",
        "Sports AI Prediction API: FastAPI service using OpenAI for natural-language sports "
        "match predictions",
        "Employee Sentiment Analysis: BERT + VADER NLP pipeline on 2,200 emails",
        "Phishing Email Detection (MSc): Random Forest, Naive Bayes & DistilBERT comparison "
        "with adversarial robustness testing",
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
