# AI Job Finder Bot 🤖

A Streamlit-based AI job search and application assistant that searches multiple job boards, scores each role against your profile using Gemini AI, generates tailored cover letters, and tracks every application — all in one place.

![Python](https://img.shields.io/badge/Python-3.9+-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-1.35+-red)
![Gemini](https://img.shields.io/badge/Gemini-2.5--Flash-orange)
![License](https://img.shields.io/badge/License-MIT-green)

## Features

- **Multi-board job search** — LinkedIn, Reed.co.uk, Remotive, and Arbeitnow in one click
- **AI match scoring** — Gemini 2.5 Flash scores each job 1–10 against your skills and profile
- **Cover letter generator** — fully tailored, role-specific cover letters in under 10 seconds
- **ATS keyword analyser** — identifies missing keywords and estimates your ATS match score
- **Interview prep** — generates 6 likely technical questions per role with answer hints
- **Application tracker** — SQLite-backed tracker with status pipeline: Saved → Applied → Interview → Offer
- **Dashboard** — application funnel chart, top matches table, action plan

## Screenshots

| Search & Score | Apply | Tracker |
|---|---|---|
| Searches 4 boards, AI-scores results | One-click cover letter + ATS analysis | Full pipeline from saved to offer |

## Quick Start

```bash
# 1. Clone the repo
git clone https://github.com/vishnu0529/ai-job-finder-bot.git
cd ai-job-finder-bot

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set up your API keys
cp .env.example .env
# Edit .env and add your GOOGLE_API_KEY and REED_API_KEY

# 4. Run
streamlit run app.py
```

Open **http://localhost:8501** in your browser.

## API Keys

| Key | Required | Source | Cost |
|---|---|---|---|
| `GOOGLE_API_KEY` | Yes | [Google AI Studio](https://aistudio.google.com/apikey) | Free tier |
| `REED_API_KEY` | Recommended | [Reed Developer](https://www.reed.co.uk/developers/jobseeker) | Free |
| `ADZUNA_APP_ID/KEY` | Optional | [Adzuna Developer](https://developer.adzuna.com/) | Free tier |

LinkedIn and Remotive require no API keys.

## Project Structure

```
ai-job-finder-bot/
├── app.py              # Main Streamlit application
├── config.py           # Candidate profile + source settings
├── searchers/
│   ├── base.py         # Job dataclass
│   ├── linkedin.py     # LinkedIn public job scraper
│   ├── reed.py         # Reed.co.uk API client
│   ├── remotive.py     # Remotive API client (remote jobs)
│   └── arbeitnow.py    # Arbeitnow API client
├── agents/
│   ├── scorer.py       # Gemini-powered job match scorer
│   └── writer.py       # Cover letter + ATS + interview prep generator
├── db/
│   └── tracker.py      # SQLite application tracker
├── .env.example        # Environment variable template
└── requirements.txt
```

## Customising for Your Profile

Edit `config.py` to update your profile before using:

```python
CANDIDATE = {
    "name":    "Your Name",
    "skills":  ["Python", "LangChain", "FastAPI", ...],
    "summary": "Your professional summary...",
    "target_roles": ["AI Engineer", "ML Engineer", ...],
}
```

## Tech Stack

- **Streamlit** — UI framework
- **Google Gemini 2.5 Flash** — AI scoring, cover letter generation, interview prep
- **httpx + BeautifulSoup** — job board scraping
- **SQLite** — local application tracking
- **Reed.co.uk API** — UK job listings
- **Remotive API** — remote job listings

## Part of my AI Engineering Portfolio

This project is part of a larger AI engineering portfolio:

- [AI Resume Matcher](https://github.com/vishnu0529/ai-resume-matcher) — production 4-step agentic LLM system
- [Employee Sentiment Analysis](https://github.com/vishnu0529/Employee-Sentiment-Analysis) — BERT + VADER NLP pipeline
- [Sports AI API](https://github.com/vishnu0529/sports-ai-api) — multi-agent RAG with LangGraph

## License

MIT
