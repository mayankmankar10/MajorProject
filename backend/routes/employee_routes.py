# backend/routes/employee_routes.py
from fastapi import APIRouter
from pydantic import BaseModel
from backend.agents.employee_agent import EmployeeConnectorAgent

router = APIRouter()
agent = EmployeeConnectorAgent()

class EmployeeCreate(BaseModel):
    name: str
    email: str
    resume_text: str

class DiscoverQuery(BaseModel):
    query: str
    k: int = 5

class ApplyPayload(BaseModel):
    employee_id: int
    job_id: int

@router.post("/register")
def register(payload: EmployeeCreate):
    return agent.register_employee(payload.name, payload.email, payload.resume_text)

@router.post("/discover")
def discover(payload: DiscoverQuery):
    return agent.discover_jobs(payload.query, k=payload.k)

@router.post("/apply")
def apply(payload: ApplyPayload):
    return agent.apply_to_job(payload.employee_id, payload.job_id)
