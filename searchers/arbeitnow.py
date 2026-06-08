import httpx
from searchers.base import Job


def search(keywords: str = "ai engineer", limit: int = 40) -> list:
    """Arbeitnow free job board API — no auth required, good remote/EU coverage."""
    try:
        resp = httpx.get(
            "https://www.arbeitnow.com/api/job-board-api",
            params={"search": keywords},
            timeout=15,
            headers={"User-Agent": "Mozilla/5.0 (compatible; job-finder-bot/1.0)"},
        )
        resp.raise_for_status()
        data = resp.json().get("data", [])
    except Exception:
        return []

    jobs = []
    for item in data[:limit]:
        jid = f"arbeitnow_{item.get('slug', '')}"
        remote = item.get("remote", False)
        tags = item.get("tags", [])
        description = item.get("description", "") or ""
        jobs.append(Job(
            id=jid,
            title=item.get("title", ""),
            company=item.get("company_name", ""),
            location=item.get("location", "Remote" if remote else ""),
            description=description[:3000],
            url=item.get("url", ""),
            source="arbeitnow",
            salary="",
            remote=remote,
            posted_date=str(item.get("created_at", ""))[:10],
        ))
    return jobs
