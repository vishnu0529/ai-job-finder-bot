from agents import scorer, writer
from agents.graph_state import ApplicationState
from agents.memory import find_similar_past_applications
from searchers.base import Job
from sponsor import register as sponsor_register


def score_node(state: ApplicationState) -> dict:
    job = Job(
        id=state["job_id"], title=state["title"], company=state["company"],
        location=state["location"], description=state["description"],
        url="", source="",
    )
    score, reason, visa_note = scorer.score_job(job)
    return {"match_score": score, "match_reason": reason, "visa_note": visa_note}


def sponsor_node(state: ApplicationState) -> dict:
    try:
        result = sponsor_register.check_company(state["company"])
        note = (
            f"Licensed as '{result.matched_name}' ({', '.join(result.routes)})"
            if result.licensed
            else "Not found on register under this name — verify manually"
        )
        return {"sponsor_licensed": result.licensed, "sponsor_note": note}
    except Exception as e:
        return {"sponsor_licensed": None, "sponsor_note": f"Could not check register: {e}"}


def recall_similar_node(state: ApplicationState) -> dict:
    similar = find_similar_past_applications(
        description=state["description"], exclude_job_id=state["job_id"], k=3,
    )
    return {"similar_past_applications": similar}


def write_node(state: ApplicationState) -> dict:
    revision_note = ""
    if state.get("critic_feedback"):
        revision_note = (
            f"\nA reviewer flagged this issue with your previous draft — fix it "
            f"in this rewrite: {state['critic_feedback']}\n"
        )
    letter = writer.generate_cover_letter(
        title=state["title"], company=state["company"],
        location=state["location"], description=state["description"],
        avoid_openers=state.get("similar_past_applications"),
        revision_note=revision_note,
    )
    return {
        "cover_letter": letter,
        "revision_count": state.get("revision_count", 0) + 1,
    }


def critique_node(state: ApplicationState) -> dict:
    score, feedback = writer.critique_cover_letter(
        cover_letter=state["cover_letter"], title=state["title"], company=state["company"],
    )
    return {"critic_score": score, "critic_feedback": feedback}
