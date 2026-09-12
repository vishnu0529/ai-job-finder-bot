"""Smoke test for the LangGraph application-generation graph.

Mocks the LLM-calling functions (scorer/writer/sponsor) so this runs
without API keys or network calls, and checks:
- the critic-driven revision loop actually loops when score is low
- it stops at max_revisions rather than looping forever
- the SQLite checkpointer persists state so get_last_run can read it back
  without re-invoking the graph
"""
import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent))

CALLS = {"write": 0, "critique": 0}


def fake_score_job(job):
    return 8.0, "Strong skills match", "ok"


def fake_check_company(company):
    class R:
        licensed = True
        matched_name = company
        routes = ["Skilled Worker"]
    return R()


def fake_generate_cover_letter(**kwargs):
    CALLS["write"] += 1
    return f"Draft #{CALLS['write']} cover letter for the role."


def fake_critique_cover_letter(cover_letter, title, company):
    CALLS["critique"] += 1
    # First two critiques score low to force revisions, third passes.
    if CALLS["critique"] < 3:
        return 5, f"Too generic (attempt {CALLS['critique']})"
    return 9, "none"


with patch("agents.nodes.scorer.score_job", side_effect=fake_score_job), \
     patch("agents.nodes.sponsor_register.check_company", side_effect=fake_check_company), \
     patch("agents.nodes.writer.generate_cover_letter", side_effect=fake_generate_cover_letter), \
     patch("agents.nodes.writer.critique_cover_letter", side_effect=fake_critique_cover_letter), \
     patch("agents.nodes.find_similar_past_applications", return_value=["a past letter"]):

    from agents.graph import run_application_graph, get_last_run

    test_job_id = "test-job-smoke-1"
    result = run_application_graph(
        job_id=test_job_id, title="AI Engineer", company="Acme Ltd",
        location="London", description="Build AI systems.",
    )

    print("revision_count:", result["revision_count"])
    print("critic_score:", result["critic_score"])
    print("cover_letter:", result["cover_letter"])
    assert result["revision_count"] == 3, f"expected 3 drafts (2 forced revisions), got {result['revision_count']}"
    assert result["critic_score"] == 9
    assert CALLS["write"] == 3
    print("Loop behaviour OK: revised until critic passed, then stopped.")

    # Cross-session recall: read state back without invoking the graph again.
    recalled = get_last_run(test_job_id)
    assert recalled is not None
    assert recalled["cover_letter"] == result["cover_letter"]
    print("Checkpoint persistence OK: get_last_run recovered prior state without re-invoking.")

print("ALL CHECKS PASSED")
