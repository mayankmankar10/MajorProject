# backend/agents/tools/ai_matching_tool.py
from backend.db.vector_db import get_vector_store

vs = get_vector_store()

def match_candidates_for_job(job_text: str, k: int = 5):
    try:
        results = vs.similarity_search_with_score(job_text, k=k)
    except Exception:
        return []
    out = []
    for doc, score in results:
        if 'employee_id' in doc.metadata:
            out.append((doc, score))
    return out
