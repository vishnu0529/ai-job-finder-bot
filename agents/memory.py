"""Semantic recall over previously generated cover letters.

This is the cross-agent/cross-session memory piece: the write_cover_letter
node in the graph doesn't just see the current job, it retrieves similar
past applications (stored in SQLite from earlier graph runs, possibly in a
previous Streamlit session) so it can avoid repeating the same opening
hooks and phrasing across applications.
"""

import numpy as np

_model = None


def _get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model


def find_similar_past_applications(description: str, exclude_job_id: str, k: int = 3) -> list[str]:
    """Return up to k past cover letters for jobs semantically similar to
    the given description, most recent first if FAISS/embeddings aren't
    available."""
    from db.tracker import get_all_jobs  # local import: avoids a circular import with app.py

    past = [
        j for j in get_all_jobs()
        if j.get("cover_letter") and j["id"] != exclude_job_id
    ]
    if not past:
        return []

    try:
        import faiss
        model = _get_model()
    except ImportError:
        return [p["cover_letter"] for p in past[:k]]

    corpus = [f"{p['title']} at {p['company']}: {(p.get('description') or '')[:300]}" for p in past]
    corpus_embs = np.array(model.encode(corpus, normalize_embeddings=True), dtype="float32")
    query_emb = np.array(model.encode([description[:300]], normalize_embeddings=True), dtype="float32")

    index = faiss.IndexFlatIP(corpus_embs.shape[1])
    index.add(corpus_embs)
    _, indices = index.search(query_emb, min(k, len(past)))

    return [past[i]["cover_letter"] for i in indices[0] if 0 <= i < len(past)]
