# backend/agents/tools/job_posting_tool.py
from backend.db.sql_db import SessionLocal
from backend.db.models import Job
from backend.db.vector_db import get_vector_store
from langchain.docstore.document import Document

vs = get_vector_store()

def create_job(employer_id: int, title: str, description: str, location: str = None):
    db = SessionLocal()
    job = Job(employer_id=employer_id, title=title, description=description, location=location)
    db.add(job)
    db.commit()
    db.refresh(job)
    # index
    meta = {"job_id": str(job.id), "employer_id": str(employer_id), "title": title}
    doc = Document(page_content=(title + "\n\n" + description), metadata=meta)
    vs.add_documents([doc])
    vs.persist()
    db.close()
    return job
