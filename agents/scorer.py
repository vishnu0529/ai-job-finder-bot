import json
import os
import time

import google.generativeai as genai
from google.api_core.exceptions import ResourceExhausted

from config import CANDIDATE
from searchers.base import Job

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


# This project's Gemini free-tier key hits a 429 (ResourceExhausted) after
# only ~6 requests in quick succession, and — confirmed by direct testing,
# not assumed — waiting out a 60s window after hitting the wall does NOT
# clear it; two consecutive 65s waits both still failed. So this isn't a
# simple rolling-window burst limit forgiving a retry; the only reliable
# approach is to never burst in the first place: a fixed minimum gap
# between every single request from the very first call. This makes batch
# scoring slow (~20s/job) but reliable, rather than fast and silently wrong.
_MIN_INTERVAL_SECONDS = 18
_last_request_time = 0.0


def _throttle():
    global _last_request_time
    elapsed = time.time() - _last_request_time
    if elapsed < _MIN_INTERVAL_SECONDS:
        time.sleep(_MIN_INTERVAL_SECONDS - elapsed)
    _last_request_time = time.time()


def _generate_with_retry(model, prompt: str):
    _throttle()
    try:
        return model.generate_content(prompt)
    except ResourceExhausted:
        # One safety-net retry only — testing showed waiting doesn't
        # reliably clear this key's limit, so hammering it with more
        # retries would just waste time rather than actually help.
        time.sleep(_MIN_INTERVAL_SECONDS)
        return model.generate_content(prompt)


SCORE_PROMPT = """
You are an AI career coach. Score how well this job matches the candidate profile.

CANDIDATE:
- Name: {name}
- Skills: {skills}
- Target roles: {targets}
- Experience: {experience}
- Visa: {visa}
- Summary: {summary}

JOB:
- Title: {title}
- Company: {company}
- Location: {location}
- Description (first 800 chars): {description}

Return ONLY valid JSON with exactly these keys:
{{
  "score": <integer 1-10>,
  "reason": "<one sentence max 120 chars>",
  "visa_flag": "<'ok'|'likely_ok'|'may_need_sponsorship'|'unclear'>",
  "level": "<'junior'|'mid'|'senior'|'unknown'>"
}}

Scoring guide:
- 9-10: Perfect match — title and skills align, UK/remote, likely visa-friendly
- 7-8:  Strong match — most skills match, minor gaps
- 5-6:  Partial match — related field, missing 1-2 key skills
- 3-4:  Weak match — different seniority or few skills match
- 1-2:  Poor match — unrelated role or requires skills candidate lacks
"""


def score_job(job: Job) -> tuple[float, str, str]:
    """Returns (score, reason, visa_note)."""
    prompt = SCORE_PROMPT.format(
        name=CANDIDATE["name"],
        skills=", ".join(CANDIDATE["skills"][:20]),
        targets=", ".join(CANDIDATE["target_roles"]),
        experience="; ".join(CANDIDATE["experience"]),
        visa=CANDIDATE["visa"],
        summary=CANDIDATE["summary"],
        title=job.title,
        company=job.company,
        location=job.location,
        description=job.description[:800],
    )
    try:
        model = _get_model()
        resp  = _generate_with_retry(model, prompt)
        text  = resp.text.strip()
        # strip markdown fences if present
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        data = json.loads(text.strip())
        score    = float(data.get("score", 5))
        reason   = data.get("reason", "")
        visa_note = data.get("visa_flag", "unclear")
        return score, reason, visa_note
    except Exception as e:
        return 5.0, f"Could not score — manual review needed ({type(e).__name__})", "unclear"


def batch_score(jobs: list[Job]) -> list[Job]:
    """Score all jobs, mutating match_score / match_reason / visa_note in place."""
    for job in jobs:
        if job.description:
            job.match_score, job.match_reason, job.visa_note = score_job(job)
        else:
            job.match_score = 5.0
            job.match_reason = "No description — manual review"
            job.visa_note = "unclear"
    return sorted(jobs, key=lambda j: j.match_score, reverse=True)
