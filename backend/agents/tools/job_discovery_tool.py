# backend/agents/tools/job_discovery_tool.py
from backend.db.vector_db import get_vector_store

vs = get_vector_store()

def discover_jobs(query: str, k: int = 5):
    results = vs.similarity_search_with_score(query, k=k)
    out = []
    for doc, score in results:
        if 'job_id' in doc.metadata:
            out.append({"job_id": doc.metadata['job_id'], "title": doc.metadata.get('title'), "score": float(score)})
    return out
