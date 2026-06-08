import httpx
import hashlib
import re
from bs4 import BeautifulSoup
from searchers.base import Job

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

# geoId 101165590 = United Kingdom
SEARCH_URL = (
    "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
    "?keywords={keywords}&location=United+Kingdom&geoId=101165590&start={start}&count=25"
)


def search(keywords: str = "AI Engineer", limit: int = 50) -> list:
    jobs: list[Job] = []
    start = 0
    while len(jobs) < limit:
        url = SEARCH_URL.format(
            keywords=keywords.replace(" ", "+"), start=start
        )
        try:
            resp = httpx.get(url, headers=HEADERS, timeout=20, follow_redirects=True)
            if resp.status_code != 200:
                break
            soup = BeautifulSoup(resp.text, "html.parser")
            cards = soup.find_all("div", class_=re.compile(r"base-card"))
            if not cards:
                break
            for card in cards:
                title_el   = card.find(class_=re.compile(r"base-search-card__title"))
                company_el = card.find(class_=re.compile(r"base-search-card__subtitle"))
                loc_el     = card.find(class_=re.compile(r"job-search-card__location"))
                link_el    = card.find("a", class_=re.compile(r"base-card__full-link"))
                date_el    = card.find("time")
                if not title_el or not link_el:
                    continue
                title   = title_el.get_text(strip=True)
                company = company_el.get_text(strip=True) if company_el else ""
                loc     = loc_el.get_text(strip=True) if loc_el else "UK"
                href    = link_el.get("href", "").split("?")[0]
                date    = date_el.get("datetime", "") if date_el else ""
                jid     = "linkedin_" + hashlib.md5(href.encode()).hexdigest()[:12]
                jobs.append(Job(
                    id=jid,
                    title=title,
                    company=company,
                    location=loc,
                    description="",   # fetched on demand
                    url=href,
                    source="linkedin",
                    remote="remote" in loc.lower() or "remote" in title.lower(),
                    posted_date=date,
                ))
            start += 25
            if len(cards) < 25:
                break
        except Exception:
            break
    return jobs[:limit]


def fetch_description(url: str) -> str:
    """Fetch job description for a single LinkedIn listing."""
    try:
        resp = httpx.get(url, headers=HEADERS, timeout=15, follow_redirects=True)
        soup = BeautifulSoup(resp.text, "html.parser")
        desc = soup.find("div", class_=re.compile(r"description__text|show-more-less-html"))
        return desc.get_text(separator="\n", strip=True)[:3000] if desc else ""
    except Exception:
        return ""
