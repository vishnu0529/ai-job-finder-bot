"""Parses the free-text salary field already stored on Job/jobs.db rows.

Real data in this project's jobs.db mixes GBP annual salaries
("£45,000–£60,000"), GBP day/contract rates ("£400–£450"), and USD figures
("$80k - $100k", "$50-$75 /hour") across sources. Benchmarking only makes
sense against comparable, plausible-annual GBP figures — silently averaging
day rates in with annual salaries would produce a misleading chart.
"""

import re
from typing import Optional, Tuple

# UK tech annual salaries are essentially never below this; day/hourly rates
# commonly show up as a few hundred pounds in this data — anything under the
# floor is assumed to not be an annual salary and is excluded.
ANNUAL_SALARY_FLOOR_GBP = 15000

_GBP_NUMBER_RE = re.compile(r"£\s*([\d,]+(?:\.\d+)?)\s*(k)?", re.IGNORECASE)


def parse_gbp_salary(text: str) -> Optional[Tuple[float, float]]:
    """Returns (min, max) annual GBP salary, or None if the string isn't
    GBP, is empty/unparseable, or doesn't look like a plausible annual
    figure (e.g. a day rate)."""
    if not text or "£" not in text:
        return None

    values = []
    for num_str, k_suffix in _GBP_NUMBER_RE.findall(text):
        try:
            num = float(num_str.replace(",", ""))
        except ValueError:
            continue
        if k_suffix:
            num *= 1000
        values.append(num)

    if not values:
        return None

    lo, hi = min(values), max(values)
    if hi < ANNUAL_SALARY_FLOOR_GBP:
        return None
    return (lo, hi)


def match_target_role(title: str, target_roles: list) -> str:
    title_lower = (title or "").lower()
    for role in target_roles:
        if role.lower() in title_lower:
            return role
    return "Other"
