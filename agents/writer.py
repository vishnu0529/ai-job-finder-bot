import os
import json
from typing import Optional
import google.generativeai as genai
from agents.gemini_client import generate_with_retry
from config import CANDIDATE

_model = None

def _get_model():
    global _model
    if _model is None:
        key = os.getenv("GOOGLE_API_KEY", "")
        if not key:
            raise ValueError("GOOGLE_API_KEY not set")
        genai.configure(api_key=key)
        _model = genai.GenerativeModel("gemini-2.5-flash")
    return _model


COVER_LETTER_PROMPT = """
You are an expert AI career coach writing a cover letter for {name}.

CANDIDATE PROFILE:
{summary}

Skills: {skills}

Projects:
{projects}

Experience: {experience}

Visa status: {visa}

JOB BEING APPLIED TO:
Title: {title}
Company: {company}
Location: {location}
Description:
{description}

Write a compelling, specific cover letter (350–400 words) that:
1. Opens with a strong hook referencing THIS company/role specifically — not generic
2. References the AI Resume Matcher (FastAPI, Anthropic Claude, FAISS semantic matching) as concrete evidence of applied AI skills
3. Maps 2–3 SPECIFIC requirements from the job description to the candidate's specific skills/projects
4. Mentions MSc AI & Robotics completion date (Sep 2026) and full-time availability from Oct 2026
5. Is professional but human, not robotic
6. Ends with a clear call to action

NEVER use these phrases: "I am writing to express my interest", "I would be a great fit",
"passionate about", "I am excited to", "I believe I would".
{avoid_openers_section}
{revision_note}
Return ONLY the cover letter text, no preamble.
"""

CRITIQUE_PROMPT = """
You are a blunt, experienced hiring manager reviewing a cover letter before it goes out.

JOB: {title} at {company}

COVER LETTER:
{cover_letter}

Score it 1-10 on: specificity to this company/role, whether it maps real
skills/projects to real requirements (not generic claims), and whether the
opening hook is fresh rather than templated. Be strict — a 7+ should be rare.

Return ONLY valid JSON:
{{"score": <integer 1-10>, "feedback": "<one sentence, the single biggest issue to fix, or 'none' if score >= 8>"}}
"""

CV_TAILOR_PROMPT = """
You are an ATS and recruiter expert. Analyse this job description and the candidate's CV summary.

JOB TITLE: {title}
COMPANY: {company}
JOB DESCRIPTION:
{description}

CANDIDATE SKILLS: {skills}

Respond with ONLY valid JSON:
{{
  "ats_keywords_missing": ["keyword1", "keyword2"],
  "ats_keywords_present": ["keyword1", "keyword2"],
  "top_3_requirements": ["req1", "req2", "req3"],
  "tailoring_tips": ["tip1", "tip2", "tip3"],
  "ats_score_estimate": <integer 1-100>
}}
"""

FOLLOW_UP_PROMPT = """
You are an expert career coach writing a brief follow-up email on behalf of {name}.

They applied to the {title} role at {company} on {applied_date} and have not
heard back since. Write a short, polite follow-up email (under 120 words) that:
1. References the specific role and the original application date
2. Briefly reaffirms interest without repeating the whole cover letter
3. Asks politely whether there's any update on the hiring timeline
4. Is warm but not pushy or apologetic

Return ONLY the email text (including a short subject line as the first line,
prefixed "Subject: "), no preamble.
"""

INTERVIEW_PREP_PROMPT = """
You are an expert AI interview coach.

JOB: {title} at {company}
DESCRIPTION (first 1200 chars): {description}

Generate 6 likely technical interview questions for this specific role with brief answer hints for the candidate.

Candidate's strongest points to weave in:
- AI Resume Matcher (FastAPI, Anthropic Claude, FAISS semantic matching)
- RAG + LangChain experience (enterprise-rag-assistant)
- FastAPI + CI/CD

Return as JSON array:
[
  {{"question": "...", "hint": "..."}},
  ...
]
"""


def generate_cover_letter(
    title: str, company: str, location: str, description: str,
    avoid_openers: Optional[list[str]] = None, revision_note: str = "",
) -> str:
    avoid_openers_section = ""
    if avoid_openers:
        snippets = "\n".join(f"- {o[:150]}..." for o in avoid_openers)
        avoid_openers_section = (
            f"\nOpening hooks used in past cover letters — do NOT reuse these "
            f"phrasings or structures, write a genuinely different opener:\n{snippets}\n"
        )
    prompt = COVER_LETTER_PROMPT.format(
        name=CANDIDATE["name"],
        summary=CANDIDATE["summary"],
        skills=", ".join(CANDIDATE["skills"]),
        projects="\n".join(f"- {p}" for p in CANDIDATE["projects"]),
        experience="; ".join(CANDIDATE["experience"]),
        visa=CANDIDATE["visa"],
        title=title,
        company=company,
        location=location,
        description=description[:2000],
        avoid_openers_section=avoid_openers_section,
        revision_note=revision_note,
    )
    try:
        return generate_with_retry(_get_model(), prompt).text.strip()
    except Exception as e:
        return f"Error generating cover letter: {e}"


def critique_cover_letter(cover_letter: str, title: str, company: str) -> tuple[int, str]:
    """Returns (score, feedback). Used by the critic node in the graph to
    decide whether write_cover_letter should revise."""
    prompt = CRITIQUE_PROMPT.format(title=title, company=company, cover_letter=cover_letter)
    try:
        text = generate_with_retry(_get_model(), prompt).text.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        data = json.loads(text.strip())
        return int(data.get("score", 7)), data.get("feedback", "")
    except Exception:
        return 7, ""


def generate_cv_notes(title: str, company: str, description: str) -> dict:
    prompt = CV_TAILOR_PROMPT.format(
        title=title,
        company=company,
        description=description[:2000],
        skills=", ".join(CANDIDATE["skills"]),
    )
    try:
        text = generate_with_retry(_get_model(), prompt).text.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        return json.loads(text.strip())
    except Exception:
        return {}


def generate_follow_up_email(title: str, company: str, applied_date: str) -> str:
    prompt = FOLLOW_UP_PROMPT.format(
        name=CANDIDATE["name"],
        title=title,
        company=company,
        applied_date=applied_date,
    )
    try:
        return generate_with_retry(_get_model(), prompt).text.strip()
    except Exception as e:
        return f"Error generating follow-up email: {e}"


def generate_interview_prep(title: str, company: str, description: str) -> list[dict]:
    prompt = INTERVIEW_PREP_PROMPT.format(
        title=title,
        company=company,
        description=description[:1200],
    )
    try:
        text = generate_with_retry(_get_model(), prompt).text.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        return json.loads(text.strip())
    except Exception:
        return []
