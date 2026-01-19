# backend/routes/interview_routes.py
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from backend.db.sql_db import get_db
from backend.db.models import Interview, Application, Job, Employee, Employer, User
from backend.utils.auth import get_current_user
from typing import List
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/interviews", tags=["Interviews"])


@router.get("")
def get_interviews(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get interviews for current user (employer or employee)."""
    try:
        user_id = current_user.get("user_id")
        role = current_user.get("role")
        
        if role == "employer":
            # Get employer's interviews
            employer = db.query(Employer).filter(Employer.user_id == user_id).first()
            if not employer:
                return []
            
            # Get all jobs for this employer
            job_ids = [job.id for job in db.query(Job).filter(Job.employer_id == employer.id).all()]
            
            # Get interviews for these jobs
            interviews = db.query(Interview).join(Application).filter(
                Application.job_id.in_(job_ids)
            ).all()
            
        elif role == "employee":
            # Get employee's interviews
            employee = db.query(Employee).filter(Employee.user_id == user_id).first()
            if not employee:
                return []
            
            # Get interviews for employee's applications
            interviews = db.query(Interview).join(Application).filter(
                Application.employee_id == employee.id
            ).all()
        else:
            return []
        
        # Format response
        result = []
        for interview in interviews:
            app = interview.application
            job = db.query(Job).filter(Job.id == app.job_id).first()
            employee = db.query(Employee).filter(Employee.id == app.employee_id).first()
            
            result.append({
                "id": interview.id,
                "application_id": interview.application_id,
                "job_id": app.job_id if app else None,
                "job_title": job.title if job else "Unknown",
                "employee_id": app.employee_id if app else None,
                "employee_name": employee.full_name if employee else "Unknown",
                "scheduled_at": interview.scheduled_at.isoformat() if interview.scheduled_at else None,
                "location": interview.location,
                "status": interview.status.value if hasattr(interview.status, 'value') else str(interview.status),
                "notes": interview.interviewer_notes,
                "created_at": interview.created_at.isoformat() if interview.created_at else None
            })
        
        return result
        
    except Exception as e:
        logger.error(f"Error fetching interviews: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
