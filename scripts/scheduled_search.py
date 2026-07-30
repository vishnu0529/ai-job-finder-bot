"""Headless CLI: search all sources, score with Gemini, check the real UK
sponsor register, push new jobs to Google Sheets. Built for GitHub Actions'
scheduled (cron) runs.

Deliberately stateless — does NOT touch the local jobs.db (that's the
interactive Streamlit app's job). GitHub Actions runners are ephemeral, so
the Google Sheet is the persistent record for scheduled runs, not SQLite.

Required env vars: GOOGLE_API_KEY, GOOGLE_SHEETS_CREDENTIALS_JSON,
GOOGLE_SHEET_ID. Optional: REED_API_KEY, ADZUNA_APP_ID, ADZUNA_APP_KEY.
See README's scheduled-search setup section for how to obtain these.
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from agents import scorer  # noqa: E402
from config import CANDIDATE  # noqa: E402
from integrations import sheets  # noqa: E402
from searchers import adzuna, arbeitnow, linkedin, reed, remotive  # noqa: E402
from sponsor import register as sponsor_register  # noqa: E402


def main() -> None:
    keywords = " OR ".join(CANDIDATE["target_roles"][:3])
    location = CANDIDATE.get("target_locations", ["London"])[0]
    print(f"Searching for: {keywords!r} in {location!r}")

    all_jobs = []
    all_jobs.extend(linkedin.search(keywords, limit=40))
    all_jobs.extend(remotive.search(keywords, limit=40))
    all_jobs.extend(arbeitnow.search(keywords, limit=40))

    reed_key = os.getenv("REED_API_KEY", "")
    if reed_key:
        all_jobs.extend(reed.search(reed_key, keywords, location, 40))

    adzuna_id = os.getenv("ADZUNA_APP_ID", "")
    adzuna_key = os.getenv("ADZUNA_APP_KEY", "")
    if adzuna_id and adzuna_key:
        all_jobs.extend(adzuna.search(adzuna_id, adzuna_key, keywords, location, 40))

    print(f"Found {len(all_jobs)} jobs total")

    if os.getenv("GOOGLE_API_KEY"):
        for job in all_jobs:
            if job.description:
                job.match_score, job.match_reason, job.visa_note = scorer.score_job(job)
    else:
        print("GOOGLE_API_KEY not set - skipping AI scoring")

    for job in all_jobs:
        try:
            result = sponsor_register.check_company(job.company)
            job.sponsor_licensed = result.licensed
            job.sponsor_note = (
                f"Licensed as '{result.matched_name}' ({', '.join(result.routes)})"
                if result.licensed
                else "Not found on register under this name"
            )
        except Exception as e:
            job.sponsor_licensed = None
            job.sponsor_note = f"Could not check register: {e}"

    appended = sheets.append_new_jobs(all_jobs)
    print(f"Appended {appended} new rows to Google Sheet "
          f"(skipped {len(all_jobs) - appended} already-seen duplicates)")


if __name__ == "__main__":
    main()
