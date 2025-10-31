# backend/routes/onboarding_routes.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.agents.tools.digital_onboarding_tool import start_onboarding

router = APIRouter()

class OnboardPayload(BaseModel):
    application_id: int
    data: dict | None = None

@router.post("/start")
def start(payload: OnboardPayload):
    return start_onboarding(payload.application_id, payload.data)
