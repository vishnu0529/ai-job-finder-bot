"""Checks a company name against the real UK Home Office register of
licensed sponsors (Worker/Temporary Worker routes) — replacing a pure LLM
guess with the same authoritative source used to manually vet employers.

Downloads and caches the register CSV locally (re-fetched if the cache is
older than CACHE_MAX_AGE_SECONDS), then does a normalised exact-match
lookup: punctuation stripped, common suffixes/filler words (Ltd, Limited,
Group, etc.) removed from both the query and every register entry. This
correctly matches e.g. "Citi" against the register's "Citi Group" entry,
while avoiding substring-scan false positives against unrelated
similarly-named companies.
"""

import csv
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import httpx

CACHE_DIR = Path(__file__).parent.parent / "data"
CACHE_PATH = CACHE_DIR / "sponsors_cache.csv"
CACHE_MAX_AGE_SECONDS = 7 * 24 * 3600

PUBLICATION_PAGE = (
    "https://www.gov.uk/government/publications/"
    "register-of-licensed-sponsors-workers"
)

_STOPWORDS = {"ltd", "limited", "llp", "plc", "inc", "the", "group", "uk", "co"}

_CSV_LINK_RE = re.compile(
    r'href="(https://assets\.publishing\.service\.gov\.uk/media/[^"]+\.csv)"'
)


@dataclass
class SponsorResult:
    licensed: bool
    matched_name: str = ""
    routes: list = field(default_factory=list)


def _normalise(name: str) -> str:
    name = (name or "").lower().strip()
    name = re.sub(r"[^a-z0-9 ]", " ", name)
    words = [w for w in name.split() if w and w not in _STOPWORDS]
    return " ".join(words).strip()


def _find_csv_url() -> str:
    resp = httpx.get(PUBLICATION_PAGE, timeout=20, follow_redirects=True)
    resp.raise_for_status()
    match = _CSV_LINK_RE.search(resp.text)
    if not match:
        raise RuntimeError(
            "Could not find the sponsor register CSV link on the gov.uk "
            "publication page — the page layout may have changed."
        )
    return match.group(1)


def _ensure_cache() -> Path:
    CACHE_DIR.mkdir(exist_ok=True)
    if CACHE_PATH.exists():
        age = time.time() - CACHE_PATH.stat().st_mtime
        if age < CACHE_MAX_AGE_SECONDS:
            return CACHE_PATH
    csv_url = _find_csv_url()
    resp = httpx.get(csv_url, timeout=90, follow_redirects=True)
    resp.raise_for_status()
    CACHE_PATH.write_bytes(resp.content)
    return CACHE_PATH


_INDEX: Optional[dict] = None


def _load_index() -> dict:
    global _INDEX
    if _INDEX is not None:
        return _INDEX
    path = _ensure_cache()
    index: dict[str, list[dict]] = {}
    with path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            org = (row.get("Organisation Name") or "").strip()
            if not org:
                continue
            key = _normalise(org)
            if not key:
                continue
            index.setdefault(key, []).append(row)
    _INDEX = index
    return index


def check_company(name: str) -> SponsorResult:
    """Look up a company name against the cached register. Returns
    licensed=False both when the company genuinely isn't licensed and when
    it simply couldn't be matched under this exact name — a "not found"
    result is a prompt to double-check manually, not proof of no licence."""
    key = _normalise(name)
    if not key:
        return SponsorResult(licensed=False)

    index = _load_index()
    rows = index.get(key)
    if not rows:
        return SponsorResult(licensed=False)

    routes = sorted({(r.get("Route") or "").strip() for r in rows if r.get("Route")})
    return SponsorResult(
        licensed=True,
        matched_name=rows[0]["Organisation Name"].strip(),
        routes=routes,
    )


def refresh_cache() -> None:
    """Force a re-download of the register, ignoring cache age."""
    if CACHE_PATH.exists():
        CACHE_PATH.unlink()
    global _INDEX
    _INDEX = None
    _ensure_cache()
