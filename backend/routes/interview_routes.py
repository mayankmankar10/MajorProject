from fastapi import APIRouter
from backend.agents.scheduler_agent import SchedulerAgent

router = APIRouter(prefix="/api/interviews", tags=["Interviews"])
scheduler = SchedulerAgent()

@router.post("/schedule")
def schedule_interview(employer: str, candidate: str):
    result = scheduler.schedule_interview(employer, candidate)
    return {"status": "success", "data": result}
