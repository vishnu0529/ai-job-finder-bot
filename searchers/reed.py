import httpx
import base64
from searchers.base import Job


def search(api_key: str, keywords: str = "AI Engineer",
           location: str = "London", limit: int = 40) -> list:
    """Reed.co.uk API — free key at https://www.reed.co.uk/developers/jobseeker"""
    if not api_key:
        return []
    token = base64.b64encode(f"{api_key}:".encode()).decode()
    try:
        resp = httpx.get(
            "https://www.reed.co.uk/api/1.0/search",
            params={
                "keywords": keywords,
                "locationName": location,
                "distancefromLocation": 15,
                "resultsToTake": limit,
            },
            headers={
                "Authorization": f"Basic {token}",
                "User-Agent": "job-finder-bot/1.0",
            },
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json().get("results", [])
    except Exception:
        return []

    jobs = []
    for item in data:
        jid = f"reed_{item.get('jobId', '')}"
        salary = ""
        lo, hi = item.get("minimumSalary"), item.get("maximumSalary")
        if lo and hi:
            salary = f"£{lo:,.0f}–£{hi:,.0f}"
        elif lo:
            salary = f"£{lo:,.0f}+"
        jobs.append(Job(
            id=jid,
            title=item.get("jobTitle", ""),
            company=item.get("employerName", ""),
            location=item.get("locationName", ""),
            description=(item.get("jobDescription", "") or "")[:3000],
            url=item.get("jobUrl", f"https://www.reed.co.uk/jobs/{item.get('jobId')}"),
            source="reed",
            salary=salary,
            remote="remote" in (item.get("locationName", "") or "").lower(),
            posted_date=str(item.get("date", ""))[:10],
        ))
    return jobs
