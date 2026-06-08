from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Job:
    id: str
    title: str
    company: str
    location: str
    description: str
    url: str
    source: str                        # reed | linkedin | remotive | adzuna
    salary: str = ""
    remote: bool = False
    posted_date: str = ""
    match_score: float = 0.0
    match_reason: str = ""
    visa_note: str = ""
    fetched_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def short_description(self, chars: int = 500) -> str:
        return self.description[:chars] + "..." if len(self.description) > chars else self.description
