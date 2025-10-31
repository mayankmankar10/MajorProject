# app/routers/scheduler.py
from fastapi import APIRouter
from datetime import datetime

router = APIRouter(prefix="/api/scheduler", tags=["Scheduler"])

@router.get("/run")
async def run_scheduler():
    # Example task
    return {"status": "Scheduler triggered successfully", "timestamp": datetime.now().isoformat()}
