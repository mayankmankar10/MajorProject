# backend/agents/employer_agent.py
import logging
from backend.db.sql_db import SessionLocal
from backend.db.models import Employer, Job, Application, Interview, Employee
from backend.db.vector_db import get_vector_store

logger = logging.getLogger(__name__)


class EmployerConnectorAgent:
    """
    The EmployerConnectorAgent handles job postings and related information
    persisted in the SQL DB and optionally indexed in the vector store.
    """

    def __init__(self):
        logger.info("🏢 EmployerConnectorAgent initialized successfully.")

    def register_employer(self, name: str, email: str, profile: str = ""):
        db = SessionLocal()
        try:
            e = Employer(name=name, email=email, profile=profile)
            db.add(e)
            db.commit()
            db.refresh(e)
            return {"id": e.id, "name": e.name, "email": e.email}
        finally:
            db.close()

    def post_job(self, employer_id: int, title: str, description: str, location: str = None, skills: list | None = None):
        db = SessionLocal()
        try:
            job = Job(employer_id=employer_id, title=title, description=description, location=location)
            db.add(job)
            db.commit()
            db.refresh(job)

            # Try indexing job text in vector store for candidate-finding
            try:
                vs = get_vector_store()
                vs.add_documents([{
                    "page_content": f"{title}\n\n{description}",
                    "metadata": {"job_id": job.id, "employer_id": employer_id}
                }])
            except Exception:
                logger.info("Vector store not available, skipping job indexing.")

            return {"id": job.id, "title": job.title}
        finally:
            db.close()

    def get_active_job_posts(self):
        db = SessionLocal()
        try:
            rows = db.query(Job).filter(Job.is_active == True).all()
            jobs = []
            for j in rows:
                jobs.append({"id": j.id, "title": j.title, "description": j.description, "location": j.location})
            logger.info(f"📋 Found {len(jobs)} active job postings.")
            return jobs
        finally:
            db.close()

    def find_candidates(self, text: str, k: int = 5):
        # prefer vector store search for employees
        try:
            vs = get_vector_store()
            results = vs.similarity_search_with_score(text, k=k)
            out = []
            for doc, score in results:
                if doc.metadata.get("employee_id"):
                    out.append({"employee_id": doc.metadata.get("employee_id"), "score": score, "text": doc.page_content})
            return out
        except Exception:
            pass

        # fallback: simple DB similarity
        db = SessionLocal()
        try:
            employees = db.query(Employee).all()
            scored = []
            for emp in employees:
                text_emp = emp.resume_text or ""
                from difflib import SequenceMatcher

                score = SequenceMatcher(None, text_emp, text).ratio()
                scored.append((emp, score))
            scored.sort(key=lambda x: x[1], reverse=True)
            return [{"employee_id": e.id, "name": e.name, "score": round(s, 2)} for e, s in scored[:k]]
        finally:
            db.close()

    def schedule_interview(self, application_id: int, scheduled_at, location: str | None = None):
        db = SessionLocal()
        try:
            inv = Interview(application_id=application_id, scheduled_at=scheduled_at, location=location)
            db.add(inv)
            db.commit()
            db.refresh(inv)
            return {"interview_id": inv.id, "scheduled_at": inv.scheduled_at.isoformat()}
        finally:
            db.close()

    def confirm_hire(self, application_id: int):
        db = SessionLocal()
        try:
            app = db.query(Application).filter(Application.id == application_id).first()
            if not app:
                return {"error": "application not found"}
            app.status = "hired"
            db.add(app)
            db.commit()
            return {"application_id": app.id, "status": app.status}
        finally:
            db.close()
