"""Shared rate-limited Gemini call helper.

This project's Gemini free-tier key hits a 429 (ResourceExhausted) after
only ~6 requests in quick succession, and — confirmed by direct testing,
not assumed — waiting out a 60s window after hitting the wall does NOT
clear it; two consecutive 65s waits both still failed. So this isn't a
simple rolling-window burst limit forgiving a retry; the only reliable
approach is to never burst in the first place: a fixed minimum gap
between every single request from the very first call.

This state is process-wide (not per-module) because a single graph run
now makes calls from both scorer.py and writer.py in the same pass
(score -> write -> critique -> write -> critique...); two independent
per-module timers would each individually pace their own calls but still
let a scorer call and a writer call land back-to-back, burning through
the quota just as fast as no throttling at all.
"""

import time

from google.api_core.exceptions import ResourceExhausted

_MIN_INTERVAL_SECONDS = 18
_last_request_time = 0.0


class GeminiQuotaExceeded(Exception):
    """Raised when the Gemini free-tier daily request quota (not just a
    per-minute burst limit) is exhausted. Distinct from other errors so
    callers can show a clean, expected message instead of dumping the raw
    Google API error text (which includes internal quota-metric IDs) into
    the UI — important on the live public deployment."""

    def __init__(self):
        super().__init__(
            "Daily AI quota reached for this demo — please try again tomorrow, "
            "or see the GitHub repo for the full write-up."
        )


def _throttle():
    global _last_request_time
    elapsed = time.time() - _last_request_time
    if elapsed < _MIN_INTERVAL_SECONDS:
        time.sleep(_MIN_INTERVAL_SECONDS - elapsed)
    _last_request_time = time.time()


def generate_with_retry(model, prompt: str):
    _throttle()
    try:
        return model.generate_content(prompt)
    except ResourceExhausted:
        # One safety-net retry only — testing showed waiting doesn't
        # reliably clear this key's limit, so hammering it with more
        # retries would just waste time rather than actually help.
        time.sleep(_MIN_INTERVAL_SECONDS)
        try:
            return model.generate_content(prompt)
        except ResourceExhausted:
            raise GeminiQuotaExceeded()
