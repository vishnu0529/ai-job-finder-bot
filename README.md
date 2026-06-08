<div align="center">

# 🤖 AI Job Finder Bot

### Automated job search · AI match scoring · Tailored cover letters · Application tracking

[![Python](https://img.shields.io/badge/Python-3.9+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.35+-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io)
[![Gemini](https://img.shields.io/badge/Gemini-2.5_Flash-4285F4?style=for-the-badge&logo=google&logoColor=white)](https://aistudio.google.com)
[![Reed API](https://img.shields.io/badge/Reed.co.uk-API-CC0000?style=for-the-badge)](https://reed.co.uk)
[![License](https://img.shields.io/badge/License-MIT-22C55E?style=for-the-badge)](LICENSE)

**Stop spending hours manually searching job boards and writing cover letters.**  
This bot searches 4 job boards simultaneously, uses Gemini AI to score every result against your exact skill profile, and generates a tailored cover letter in under 10 seconds — all from a single Streamlit dashboard.

[Features](#-features) · [Quick Start](#-quick-start) · [Architecture](#-architecture) · [Configuration](#-configuration) · [API Keys](#-api-keys)

</div>

---

## 🎯 The Problem This Solves

Applying for AI Engineer roles in the UK typically means:
- Manually checking 4–5 job boards every day
- Reading through dozens of irrelevant postings
- Writing a unique cover letter for every application (or not, and getting ignored)
- Losing track of what you've applied to

This bot collapses that entire workflow into a single dashboard. Search once, get AI-ranked results across all boards, generate application materials in seconds, track everything in one place.

---

## ✨ Features

### 🔍 Multi-Board Job Search
Searches **LinkedIn**, **Reed.co.uk**, **Remotive**, and **Arbeitnow** in a single click — no manual tab-switching. Results are deduplicated and ranked by relevance.

### 🧠 AI Match Scoring (Gemini 2.5 Flash)
Every job result is scored **1–10** against your personal skill profile by Gemini 2.5 Flash. The scorer evaluates:
- Skills alignment (how many of your skills match the JD)
- Seniority level fit
- Location / remote compatibility
- Visa friendliness (critical for sponsored or visa-holder candidates)

Each score comes with a one-line explanation so you know *why* a job ranked where it did.

### ✍️ Tailored Cover Letter Generator
Click one button — get a **350–400 word cover letter** written specifically for that job and company. The generator:
- References the specific role and company (never generic)
- Maps your actual projects to the job's requirements
- Avoids every overused cover letter cliché
- Includes your availability and visa status cleanly

### 🎯 ATS Keyword Analyser
Compares the job description against your CV skills and returns:
- **Missing keywords** to add before applying
- **Keywords already present** in your profile
- **ATS match score estimate** (%)
- **Top 3 requirements** the employer cares most about
- **Tailoring tips** for that specific role

### 💬 Interview Prep Generator
For any saved job, generates **6 likely technical interview questions** based on the actual JD — with answer hints tailored to your specific projects and experience.

### 📌 Application Tracker
Full SQLite-backed pipeline tracker:

```
Saved → Applied → Interview → Offer → Rejected
```

Every application stores the cover letter, ATS notes, applied date, and custom notes. Nothing falls through the cracks.

### 📊 Dashboard
- Application funnel chart
- Top 10 matched jobs table
- Jobs found by source breakdown
- Average match score across all results

---

## 🚀 Quick Start

### 1. Clone & install

```bash
git clone https://github.com/vishnu0529/ai-job-finder-bot.git
cd ai-job-finder-bot
pip install -r requirements.txt
```

### 2. Configure API keys

```bash
cp .env.example .env
```

Edit `.env`:

```env
GOOGLE_API_KEY=your_gemini_api_key    # Required — free at aistudio.google.com
REED_API_KEY=your_reed_api_key        # Recommended — free at reed.co.uk/developers
```

### 3. Run

```bash
streamlit run app.py
```

Open **http://localhost:8501** — the dashboard loads immediately.

### 4. Daily workflow

```
Search tab  →  type "AI Engineer"  →  select all 4 sources  →  🚀 Search
Job Board   →  filter score 7+  →  review top matches
Apply tab   →  select job  →  Generate Cover Letter  →  Open URL  →  paste & submit
Tracker     →  mark Applied  →  repeat
```

---

## 🏗 Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Streamlit Dashboard                       │
│  🔍 Search  │  📋 Job Board  │  ✍️ Apply  │  📌 Track  │  📊  │
└──────────────────────────┬──────────────────────────────────┘
                           │
          ┌────────────────┼────────────────┐
          ▼                ▼                ▼
   ┌─────────────┐  ┌────────────┐  ┌────────────────┐
   │  Searchers  │  │ AI Agents  │  │   DB Tracker   │
   │             │  │            │  │                │
   │ • LinkedIn  │  │ • Scorer   │  │ SQLite         │
   │ • Reed API  │  │   (Gemini) │  │ jobs table     │
   │ • Remotive  │  │ • Writer   │  │ applications   │
   │ • Arbeitnow │  │   (Gemini) │  │ table          │
   └──────┬──────┘  └─────┬──────┘  └────────────────┘
          │               │
          ▼               ▼
   ┌─────────────┐  ┌──────────────────────────────────┐
   │  Job(       │  │  Gemini 2.5 Flash                │
   │   id,       │  │                                  │
   │   title,    │  │  score_job()   → 1–10 + reason   │
   │   company,  │  │  cover_letter()→ 350–400 words   │
   │   desc,     │  │  cv_notes()    → ATS analysis    │
   │   score,    │  │  interview()   → 6 questions     │
   │   ...)      │  └──────────────────────────────────┘
   └─────────────┘
```

---

## 📁 Project Structure

```
ai-job-finder-bot/
│
├── app.py                  # Streamlit UI — 5-tab dashboard (604 lines)
├── config.py               # Candidate profile + source configuration
│
├── searchers/
│   ├── base.py             # Job dataclass
│   ├── linkedin.py         # LinkedIn public job scraper (no auth required)
│   ├── reed.py             # Reed.co.uk REST API client
│   ├── remotive.py         # Remotive API client (remote-first jobs)
│   └── arbeitnow.py        # Arbeitnow API client
│
├── agents/
│   ├── scorer.py           # Gemini-powered job match scorer
│   └── writer.py           # Cover letter + ATS + interview prep generator
│
├── db/
│   └── tracker.py          # SQLite CRUD — jobs + applications tables
│
├── .env.example            # Environment variable template
├── requirements.txt
└── README.md
```

---

## ⚙️ Configuration

Edit `config.py` to set your own profile before running:

```python
CANDIDATE = {
    "name":    "Your Name",
    "email":   "your@email.com",
    "summary": "Your 2–3 sentence professional summary...",

    "skills": [
        "Python", "FastAPI", "LangChain", "RAG", "PyTorch",
        # add your skills here
    ],

    "target_roles": [
        "AI Engineer", "ML Engineer", "NLP Engineer",
        # roles you want to appear in searches
    ],

    "experience": [
        "Senior Consultant at Acme Corp (2023–2025)",
        # your experience lines
    ],

    "projects": [
        "My Project: description of what it does and stack used",
        # your projects — these get referenced in cover letters
    ],

    "visa":         "Your visa / work authorisation status",
    "availability": "Full-time from [date]",
}
```

The cover letter generator and job scorer both use this profile. The more specific your projects and skills, the better the generated materials.

---

## 🔑 API Keys

| Key | Required | Where to get it | Cost |
|---|---|---|---|
| `GOOGLE_API_KEY` | ✅ Yes | [Google AI Studio](https://aistudio.google.com/apikey) | Free tier (generous) |
| `REED_API_KEY` | ⭐ Recommended | [Reed Developer Portal](https://www.reed.co.uk/developers/jobseeker) | Free |
| `ADZUNA_APP_ID` + `ADZUNA_APP_KEY` | Optional | [Adzuna Developer](https://developer.adzuna.com/) | Free tier |

LinkedIn and Remotive require no API keys — they work immediately out of the box.

---

## 🛠 Tech Stack

| Layer | Technology |
|---|---|
| UI | Streamlit 1.35+ |
| AI / LLM | Google Gemini 2.5 Flash via `google-generativeai` |
| HTTP | `httpx` with async-compatible sync client |
| Scraping | `BeautifulSoup4` + `lxml` |
| Database | SQLite via `sqlite3` (zero-config, local) |
| Data | `pandas` for dashboard tables |
| Config | `python-dotenv` |
| Job sources | LinkedIn (public), Reed API, Remotive API, Arbeitnow API |

---

## 🗺 Roadmap

- [ ] Email alert when new high-score jobs are found
- [ ] Adzuna API integration (additional UK job source)
- [ ] PDF export of cover letters
- [ ] Follow-up email drafter (for applications with no response after 7 days)
- [ ] GitHub Actions scheduled search (run daily, push results to a Google Sheet)
- [ ] Salary benchmarking chart by role and location

---

## 🤝 Part of My AI Engineering Portfolio

This project is one of four AI engineering projects I've built publicly:

| Project | Description | Stack |
|---|---|---|
| **[AI Resume Matcher](https://github.com/vishnu0529/ai-resume-matcher)** | Production 4-step agentic LLM system — live on Railway | Gemini 2.5 Flash · FastAPI · Streamlit · Pydantic · CI/CD |
| **[AI Job Finder Bot](https://github.com/vishnu0529/ai-job-finder-bot)** | This project | Gemini · Streamlit · Reed API · SQLite |
| **[Employee Sentiment Analysis](https://github.com/vishnu0529/Employee-Sentiment-Analysis)** | End-to-end NLP pipeline on 2,200 employee emails | BERT · VADER · scikit-learn · pandas |
| **[Sports AI API](https://github.com/vishnu0529/sports-ai-api)** | Multi-agent RAG system with natural language sports queries | LangChain · LangGraph · FastAPI · FAISS |

---

## 📄 License

MIT — free to use, fork, and adapt for your own job search.

---

<div align="center">

Built by [Vishnu Kanth Suryanarayan](https://linkedin.com/in/vishnu-kanth-suryanarayan-a68851167)  
MSc AI & Robotics · University of Hertfordshire · Open to AI Engineer roles from Oct 2026

</div>
