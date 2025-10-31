# backend/agents/employee_agent.py
import logging
from difflib import SequenceMatcher
from backend.db.sql_db import SessionLocal
from backend.db.models import Employee, Job, Application
from backend.agents.tools.resume_parser_tool import parse_resume_text
from backend.db.vector_db import get_vector_store

logger = logging.getLogger(__name__)

class EmployeeConnectorAgent:
    """
    The EmployeeConnectorAgent manages worker/candidate data and 
    handles skill-based matching with job postings.
    """

    def __init__(self):
        logger.info("👷 EmployeeConnectorAgent initialized successfully.")

    def get_available_candidates(self):
        """Retrieve candidates from SQL DB.

        Falls back to an empty list when DB isn't available.
        """
        db = SessionLocal()
        try:
            rows = db.query(Employee).all()
            candidates = []
            for r in rows:
                candidates.append({
                    "id": r.id,
                    "name": r.name,
                    "resume_text": r.resume_text,
                    "created_at": r.created_at,
                })
            logger.info(f"🧑‍💼 Found {len(candidates)} available candidates.")
            return candidates
        finally:
            db.close()

    def match_candidates_with_jobs(self, jobs, candidates):
        """
        Perform skill-based matching between job postings and candidates.
        Uses a basic text similarity heuristic for demonstration.
        """
        # jobs expected as dicts with 'title' and 'description' or as Job ORM objects
        matches = []
        for job in jobs:
            job_skills = []
            if isinstance(job, Job):
                title = job.title or ""
                description = job.description or ""
                job_text = title + "\n" + description
                job_skills = [title, description]
            else:
                job_text = (job.get("title", "") + "\n" + job.get("description", ""))
                job_skills = job.get("skills", [])

            for candidate in candidates:
                # candidate may have resume_text; fall back to skills if present
                candidate_skills = []
                if isinstance(candidate, dict) and "resume_text" in candidate:
                    parsed = parse_resume_text(candidate.get("resume_text", ""))
                    candidate_skills = parsed.get("skills", []) or [parsed.get("summary", "")]
                else:
                    candidate_skills = candidate.get("skills", []) if isinstance(candidate, dict) else []

                score = 0
                if candidate_skills and job_skills:
                    score = self._calculate_match_score(job_skills, candidate_skills)
                else:
                    # fallback: text similarity between job text and candidate resume/summary
                    a = job_text
                    b = candidate.get("resume_text", "") if isinstance(candidate, dict) else ""
                    score = SequenceMatcher(None, a, b).ratio()

                if score > 0.35:  # lowered threshold for broader matches
                    matches.append({
                        "job": job_text if not isinstance(job, Job) else {"id": job.id, "title": job.title},
                        "candidate": candidate,
                        "score": round(score, 2)
                    })

        logger.info(f"� Matched {len(matches)} candidate-job pairs.")
        return matches

    def register_employee(self, name: str, email: str, resume_text: str):
        """Create an Employee record and index resume into vector store if available."""
        db = SessionLocal()
        try:
            emp = Employee(name=name, email=email, resume_text=resume_text)
            db.add(emp)
            db.commit()
            db.refresh(emp)

            # Try to index in vector store (if embeddings available)
            try:
                vs = get_vector_store()
                # store a simple document with metadata
                vs.add_documents([{
                    "page_content": resume_text,
                    "metadata": {"employee_id": emp.id, "email": email}
                }])
            except Exception:
                logger.info("Vector store not available, skipping resume indexing.")

            return {"id": emp.id, "name": emp.name, "email": emp.email}
        finally:
            db.close()

    def discover_jobs(self, query: str, k: int = 5):
        """Return list of jobs matching the query. Uses vector store if available, otherwise DB fuzzy search."""
        # try vector store search for jobs
        try:
            vs = get_vector_store()
            results = vs.similarity_search_with_score(query, k=k)
            out = []
            for doc, score in results:
                if doc.metadata.get("job_id"):
                    out.append({"job_id": doc.metadata.get("job_id"), "score": score, "text": doc.page_content})
            if out:
                return out
        except Exception:
            pass

        # fallback: search DB jobs by simple substring or similarity
        db = SessionLocal()
        try:
            rows = db.query(Job).filter(Job.is_active == True).all()
            scored = []
            for j in rows:
                text = (j.title or "") + "\n" + (j.description or "")
                score = SequenceMatcher(None, text, query).ratio()
                scored.append((j, score))
            scored.sort(key=lambda x: x[1], reverse=True)
            return [{"job_id": j.id, "title": j.title, "score": round(s, 2)} for j, s in scored[:k]]
        finally:
            db.close()

    def apply_to_job(self, employee_id: int, job_id: int):
        db = SessionLocal()
        try:
            app = Application(job_id=job_id, employee_id=employee_id)
            db.add(app)
            db.commit()
            db.refresh(app)
            return {"application_id": app.id, "status": app.status}
        finally:
            db.close()

    def _calculate_match_score(self, job_skills, candidate_skills):
        """
        Calculates a basic skill similarity score.
        """
        total_score = 0
        for js in job_skills:
            for cs in candidate_skills:
                total_score += SequenceMatcher(None, js, cs).ratio()
        return total_score / (len(job_skills) * len(candidate_skills))
