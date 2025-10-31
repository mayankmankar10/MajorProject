# backend/routes/employer_routes.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.agents.employer_agent import EmployerConnectorAgent
import datetime

router = APIRouter()
agent = EmployerConnectorAgent()

class EmployerCreate(BaseModel):
    name: str
    email: str
    profile: str = ""

class JobCreate(BaseModel):
    employer_id: int
    title: str
    description: str
    location: str | None = None
    skills: list | None = None

class FindPayload(BaseModel):
    job_id: int | None = None
    job_text: str | None = None
    k: int = 5

class SchedulePayload(BaseModel):
    application_id: int
    scheduled_at: str
    location: str | None = None

@router.post("/register")
def register_employer(payload: EmployerCreate):
    return agent.register_employer(payload.name, payload.email, payload.profile)

@router.post("/post_job")
def post_job(payload: JobCreate):
    return agent.post_job(payload.employer_id, payload.title, payload.description, payload.location, payload.skills)

@router.post("/find_candidates")
def find_candidates(payload: FindPayload):
    text = payload.job_text
    if not text and payload.job_id:
        from backend.db.sql_db import SessionLocal
        from backend.db.models import Job
        db = SessionLocal()
        job = db.query(Job).filter(Job.id == payload.job_id).first()
        db.close()
        if job:
            text = job.title + "\n\n" + job.description
    if not text:
        raise HTTPException(status_code=400, detail="provide job_text or job_id")
    return agent.find_candidates(text, k=payload.k)

@router.post("/schedule_interview")
def schedule_interview(payload: SchedulePayload):
    scheduled_at = datetime.datetime.fromisoformat(payload.scheduled_at)
    return agent.schedule_interview(payload.application_id, scheduled_at, payload.location)

@router.post("/confirm_hire")
def confirm_hire(payload: dict):
    application_id = payload.get("application_id")
    if not application_id:
        raise HTTPException(status_code=400, detail="application_id required")
    return agent.confirm_hire(application_id)
