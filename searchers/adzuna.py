import httpx
from searchers.base import Job


def search(app_id: str, app_key: str, keywords: str = "AI Engineer",
           location: str = "London", limit: int = 40) -> list:
    """Adzuna UK job search — free key at https://developer.adzuna.com/"""
    if not app_id or not app_key:
        return []
    try:
        resp = httpx.get(
            f"https://api.adzuna.com/v1/api/jobs/gb/search/1",
            params={
                "app_id": app_id,
                "app_key": app_key,
                "what": keywords,
                "where": location,
                "results_per_page": min(limit, 50),
                "content-type": "application/json",
            },
            headers={"User-Agent": "job-finder-bot/1.0"},
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json().get("results", [])
    except Exception:
        return []

    jobs = []
    for item in data:
        jid = f"adzuna_{item.get('id', '')}"
        salary = ""
        lo, hi = item.get("salary_min"), item.get("salary_max")
        if lo and hi and lo != hi:
            salary = f"£{lo:,.0f}–£{hi:,.0f}"
        elif lo:
            salary = f"£{lo:,.0f}+"

        company = (item.get("company") or {}).get("display_name", "")
        loc_display = (item.get("location") or {}).get("display_name", "")

        jobs.append(Job(
            id=jid,
            title=item.get("title", ""),
            company=company,
            location=loc_display,
            description=(item.get("description", "") or "")[:3000],
            url=item.get("redirect_url", ""),
            source="adzuna",
            salary=salary,
            remote="remote" in loc_display.lower() or "remote" in (item.get("title", "") or "").lower(),
            posted_date=str(item.get("created", ""))[:10],
        ))
    return jobs
