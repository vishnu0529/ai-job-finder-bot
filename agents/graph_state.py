from typing import Optional, TypedDict


class ApplicationState(TypedDict, total=False):
    """Shared state threaded through the application-generation graph.

    One instance flows through every node (score -> sponsor check ->
    write -> critique -> [loop back to write | end]); nodes read the
    fields they need and write back only the fields they own.
    """

    # job input
    job_id: str
    title: str
    company: str
    location: str
    description: str

    # scorer node output
    match_score: float
    match_reason: str
    visa_note: str

    # sponsor node output
    sponsor_licensed: Optional[bool]
    sponsor_note: str

    # writer node output
    cover_letter: str

    # critic node output + loop control
    critic_score: int
    critic_feedback: str
    revision_count: int
    max_revisions: int

    # memory node output (past applications retrieved for context)
    similar_past_applications: list[str]
