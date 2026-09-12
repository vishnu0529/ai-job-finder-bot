"""LangGraph orchestration for application generation.

    score_job -> check_sponsor -> recall_similar -> write_cover_letter -> critique
                                                          ^                    |
                                                          '-- revise (max N) --'

The critique node routes back to write_cover_letter when the letter scores
below MIN_ACCEPTABLE_SCORE, up to max_revisions times — this is the
conditional/cyclical edge, not a straight-line pipeline. A SQLite
checkpointer persists state per job_id (LangGraph "thread"), so re-running
the graph for a job later, even in a new Streamlit session, resumes from
its last recorded state rather than starting blank.
"""

import sqlite3
from pathlib import Path
from typing import Optional

from langgraph.graph import END, StateGraph
from langgraph.checkpoint.sqlite import SqliteSaver

from agents.graph_state import ApplicationState
from agents.nodes import critique_node, recall_similar_node, score_node, sponsor_node, write_node

MIN_ACCEPTABLE_SCORE = 7
DEFAULT_MAX_REVISIONS = 2

CHECKPOINT_DB_PATH = Path(__file__).parent.parent / "data" / "graph_checkpoints.db"


def _should_revise(state: ApplicationState) -> str:
    max_revisions = state.get("max_revisions", DEFAULT_MAX_REVISIONS)
    # revision_count is the number of drafts written so far (the first draft
    # counts as 1, not 0), so allowing max_revisions *revisions* on top of
    # that first draft means looping while revision_count <= max_revisions.
    if (
        state.get("critic_score", MIN_ACCEPTABLE_SCORE) < MIN_ACCEPTABLE_SCORE
        and state.get("revision_count", 0) <= max_revisions
    ):
        return "write_cover_letter"
    return END


def build_graph():
    graph = StateGraph(ApplicationState)
    graph.add_node("score_job", score_node)
    graph.add_node("check_sponsor", sponsor_node)
    graph.add_node("recall_similar", recall_similar_node)
    graph.add_node("write_cover_letter", write_node)
    graph.add_node("critique", critique_node)

    graph.set_entry_point("score_job")
    graph.add_edge("score_job", "check_sponsor")
    graph.add_edge("check_sponsor", "recall_similar")
    graph.add_edge("recall_similar", "write_cover_letter")
    graph.add_edge("write_cover_letter", "critique")
    graph.add_conditional_edges(
        "critique", _should_revise, {"write_cover_letter": "write_cover_letter", END: END}
    )

    CHECKPOINT_DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(str(CHECKPOINT_DB_PATH), check_same_thread=False)
    checkpointer = SqliteSaver(conn)
    return graph.compile(checkpointer=checkpointer)


_compiled_graph = None


def get_graph():
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = build_graph()
    return _compiled_graph


def run_application_graph(job_id: str, title: str, company: str, location: str, description: str) -> ApplicationState:
    graph = get_graph()
    config = {"configurable": {"thread_id": job_id}}
    initial_state: ApplicationState = {
        "job_id": job_id, "title": title, "company": company,
        "location": location, "description": description,
        "revision_count": 0, "max_revisions": DEFAULT_MAX_REVISIONS,
    }
    return graph.invoke(initial_state, config=config)


def get_last_run(job_id: str) -> Optional[ApplicationState]:
    """Read prior graph state for this job without re-running it — the
    cross-session recall Kyle's message asks about made concrete."""
    graph = get_graph()
    config = {"configurable": {"thread_id": job_id}}
    snapshot = graph.get_state(config)
    return snapshot.values if snapshot and snapshot.values else None
