import sqlite3
import json
from pathlib import Path
from datetime import datetime
from typing import Optional
from searchers.base import Job

DB_PATH = Path(__file__).parent.parent / "data" / "jobs.db"


def _conn() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def _add_column_if_missing(conn, table: str, column: str, coltype: str):
    existing = {row["name"] for row in conn.execute(f"PRAGMA table_info({table})")}
    if column not in existing:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {coltype}")


def init_db():
    with _conn() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS jobs (
            id          TEXT PRIMARY KEY,
            title       TEXT,
            company     TEXT,
            location    TEXT,
            salary      TEXT,
            url         TEXT,
            source      TEXT,
            remote      INTEGER,
            description TEXT,
            posted_date TEXT,
            match_score REAL DEFAULT 0,
            match_reason TEXT,
            visa_note   TEXT,
            fetched_at  TEXT
        );

        CREATE TABLE IF NOT EXISTS applications (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id          TEXT REFERENCES jobs(id),
            status          TEXT DEFAULT 'saved',
            cover_letter    TEXT,
            cv_notes        TEXT,
            interview_notes TEXT,
            applied_date    TEXT,
            follow_up_date  TEXT,
            notes           TEXT,
            created_at      TEXT DEFAULT (datetime('now')),
            updated_at      TEXT DEFAULT (datetime('now'))
        );
        """)
        # Idempotent migrations for columns added after the initial release —
        # existing jobs.db files must not break.
        _add_column_if_missing(conn, "jobs", "sponsor_licensed", "INTEGER")
        _add_column_if_missing(conn, "jobs", "sponsor_note", "TEXT")


def upsert_job(job: Job):
    with _conn() as conn:
        conn.execute("""
        INSERT OR REPLACE INTO jobs
            (id, title, company, location, salary, url, source, remote,
             description, posted_date, match_score, match_reason, visa_note,
             sponsor_licensed, sponsor_note, fetched_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (job.id, job.title, job.company, job.location, job.salary,
              job.url, job.source, int(job.remote), job.description,
              job.posted_date, job.match_score, job.match_reason,
              job.visa_note,
              None if job.sponsor_licensed is None else int(job.sponsor_licensed),
              job.sponsor_note, job.fetched_at))


def get_all_jobs(min_score: float = 0.0) -> list:
    with _conn() as conn:
        rows = conn.execute("""
        SELECT j.*, a.status, a.applied_date, a.cover_letter
        FROM jobs j
        LEFT JOIN applications a ON j.id = a.job_id
        WHERE j.match_score >= ?
        ORDER BY j.match_score DESC, j.fetched_at DESC
        """, (min_score,)).fetchall()
    return [dict(r) for r in rows]


def get_job(job_id: str) -> Optional[dict]:
    with _conn() as conn:
        row = conn.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
    return dict(row) if row else None


def get_application(job_id: str) -> Optional[dict]:
    with _conn() as conn:
        row = conn.execute(
            "SELECT * FROM applications WHERE job_id=? ORDER BY created_at DESC LIMIT 1",
            (job_id,)
        ).fetchone()
    return dict(row) if row else None


def save_application(job_id: str, cover_letter: str = "", cv_notes: str = "",
                     status: str = "saved", notes: str = ""):
    now = datetime.utcnow().isoformat()
    with _conn() as conn:
        existing = conn.execute(
            "SELECT id FROM applications WHERE job_id=?", (job_id,)
        ).fetchone()
        if existing:
            conn.execute("""
            UPDATE applications SET cover_letter=?, cv_notes=?, status=?,
            notes=?, updated_at=? WHERE job_id=?
            """, (cover_letter, cv_notes, status, notes, now, job_id))
        else:
            conn.execute("""
            INSERT INTO applications (job_id, cover_letter, cv_notes, status, notes, created_at, updated_at)
            VALUES (?,?,?,?,?,?,?)
            """, (job_id, cover_letter, cv_notes, status, notes, now, now))


def update_status(job_id: str, status: str, notes: str = ""):
    now = datetime.utcnow().isoformat()
    with _conn() as conn:
        applied_date = now if status == "applied" else None
        conn.execute("""
        UPDATE applications SET status=?, notes=?, updated_at=?,
        applied_date=COALESCE(?, applied_date)
        WHERE job_id=?
        """, (status, notes, now, applied_date, job_id))


def get_stats() -> dict:
    with _conn() as conn:
        total_jobs   = conn.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
        by_status    = conn.execute("""
            SELECT status, COUNT(*) as n FROM applications GROUP BY status
        """).fetchall()
        avg_score    = conn.execute("SELECT AVG(match_score) FROM jobs WHERE match_score > 0").fetchone()[0]
        top_sources  = conn.execute("""
            SELECT source, COUNT(*) as n FROM jobs GROUP BY source ORDER BY n DESC
        """).fetchall()
    return {
        "total_jobs":  total_jobs,
        "by_status":   {r["status"]: r["n"] for r in by_status},
        "avg_score":   round(avg_score or 0, 1),
        "top_sources": {r["source"]: r["n"] for r in top_sources},
    }
