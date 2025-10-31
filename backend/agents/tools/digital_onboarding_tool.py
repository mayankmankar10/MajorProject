# backend/agents/tools/digital_onboarding_tool.py
from backend.db.sql_db import SessionLocal
from backend.db.models import Application

def start_onboarding(application_id: int, onboarding_payload: dict = None):
    db = SessionLocal()
    app = db.query(Application).filter(Application.id == application_id).first()
    if not app:
        db.close()
        return {"error": "application_not_found"}
    # minimal: mark application as 'onboarding' and store any payload in profile (extend models for production)
    app.status = "onboarding"
    db.commit()
    db.refresh(app)
    db.close()
    return {"application_id": app.id, "status": app.status}
