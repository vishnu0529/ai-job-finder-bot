import httpx
import hashlib
from searchers.base import Job


def search(keywords: str = "ai engineer", limit: int = 40) -> list:
    try:
        resp = httpx.get(
            "https://remotive.com/api/remote-jobs",
            params={"search": keywords, "limit": limit},
            timeout=15,
            headers={"User-Agent": "Mozilla/5.0 (compatible; job-finder-bot/1.0)"},
        )
        resp.raise_for_status()
        data = resp.json().get("jobs", [])
    except Exception:
        return []

    jobs = []
    for item in data:
        jid = f"remotive_{item.get('id', '')}"
        tags = " · ".join(item.get("tags", []))
        jobs.append(Job(
            id=jid,
            title=item.get("job_type", ""),
            company=item.get("company_name", ""),
            location="Remote",
            description=(item.get("description", "") or "")[:3000],
            url=item.get("url", ""),
            source="remotive",
            salary=item.get("salary", ""),
            remote=True,
            posted_date=item.get("publication_date", "")[:10],
        ))
        # Override title from candidate_required_location + job title fields
        jobs[-1].title = item.get("title", jobs[-1].title)

    return jobs
