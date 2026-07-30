"""Google Sheets sync for the headless scheduled search
(scripts/scheduled_search.py). Requires a Google Cloud service account with
the Sheets API enabled, its credentials JSON, and the target sheet shared
with the service account's email — see README's scheduled-search setup
section for exact steps.
"""

import json
import os
from typing import List

import gspread
from google.oauth2.service_account import Credentials

from searchers.base import Job

_SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

_HEADER = [
    "fetched_at", "title", "company", "location", "salary", "source",
    "match_score", "match_reason", "sponsor_licensed", "sponsor_note", "url",
]

_WORKSHEET_NAME = "Jobs"


def _get_client() -> gspread.Client:
    creds_json = os.getenv("GOOGLE_SHEETS_CREDENTIALS_JSON")
    if not creds_json:
        raise RuntimeError("GOOGLE_SHEETS_CREDENTIALS_JSON not set")
    info = json.loads(creds_json)
    creds = Credentials.from_service_account_info(info, scopes=_SCOPES)
    return gspread.authorize(creds)


def _get_worksheet():
    sheet_id = os.getenv("GOOGLE_SHEET_ID")
    if not sheet_id:
        raise RuntimeError("GOOGLE_SHEET_ID not set")
    client = _get_client()
    sh = client.open_by_key(sheet_id)
    try:
        ws = sh.worksheet(_WORKSHEET_NAME)
    except gspread.WorksheetNotFound:
        ws = sh.add_worksheet(title=_WORKSHEET_NAME, rows=1000, cols=len(_HEADER))
        ws.append_row(_HEADER)
    return ws


def _existing_urls(ws) -> set:
    # Jobs don't have a stable id column in the sheet — url is unique per
    # posting and always present, so it's the natural dedup key across runs.
    url_col = _HEADER.index("url") + 1
    values = ws.col_values(url_col)
    return set(values[1:])  # skip header row


def append_new_jobs(jobs: List[Job]) -> int:
    """Appends jobs not already present in the sheet (deduped by URL) so
    repeated daily runs don't spam duplicate rows. Returns rows appended."""
    ws = _get_worksheet()
    existing = _existing_urls(ws)

    new_rows = []
    for job in jobs:
        if not job.url or job.url in existing:
            continue
        new_rows.append([
            job.fetched_at, job.title, job.company, job.location, job.salary,
            job.source, job.match_score, job.match_reason,
            "" if job.sponsor_licensed is None else str(job.sponsor_licensed),
            job.sponsor_note, job.url,
        ])
        existing.add(job.url)

    if new_rows:
        ws.append_rows(new_rows, value_input_option="USER_ENTERED")

    return len(new_rows)
