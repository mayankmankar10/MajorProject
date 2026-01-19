# backend/routes/onboarding_routes.py
from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import FileResponse
from pydantic import BaseModel
from backend.tools_langchain.onboarding_tool import OnboardingTool
from backend.db.sql_db import SessionLocal
from backend.db.models import Application, Employee, OnboardingProgress
import json
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

router = APIRouter()

class OnboardPayload(BaseModel):
    application_id: int
    data: dict | None = None

@router.post("/start")
def start(payload: OnboardPayload):
    """
    Start onboarding process for an application.
    Migrated to use LangChain OnboardingTool.
    """
    try:
        # Get application details
        db = SessionLocal()
        try:
            app = db.query(Application).filter(Application.id == payload.application_id).first()
            if not app:
                raise HTTPException(status_code=404, detail="Application not found")
            
            # Prepare context data
            context_data = payload.data or {}
            context_data.update({
                "application_id": payload.application_id,
                "employee_id": app.employee_id,
                "job_id": app.job_id
            })
            
            # Use OnboardingTool to generate offer letter
            tool = OnboardingTool()
            result = tool._run(
                employee_id=app.employee_id,
                job_id=app.job_id,
                document_type="offer_letter",
                context_data=json.dumps(context_data)
            )
            
            return json.loads(result)
            
        finally:
            db.close()
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Onboarding error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Onboarding failed: {str(e)}")

@router.get("/progress/{employee_id}")
def get_onboarding_progress(employee_id: int):
    """
    Get detailed onboarding progress for an employee including all entered data.
    Returns step completion status and all profile information.
    """
    try:
        db = SessionLocal()
        try:
            # Get employee
            employee = db.query(Employee).filter(Employee.id == employee_id).first()
            if not employee:
                raise HTTPException(status_code=404, detail="Employee not found")
            
            # Get or create onboarding progress
            progress = db.query(OnboardingProgress).filter(
                OnboardingProgress.employee_id == employee_id
            ).first()
            
            if not progress:
                # Create initial progress record
                progress = OnboardingProgress(
                    employee_id=employee_id,
                    current_step="profile",
                    is_complete=False,
                    completion_percentage=0
                )
                db.add(progress)
                db.commit()
                db.refresh(progress)
            
            # Build detailed response with all onboarding data
            response = {
                "employee_id": employee_id,
                "current_step": progress.current_step,
                "is_complete": progress.is_complete,
                "completion_percentage": progress.completion_percentage,
                "steps": {
                    "profile": progress.profile_completed,
                    "skills": progress.skills_completed,
                    "preferences": progress.preferences_completed,
                    "certifications": progress.certifications_completed,
                    "documents": progress.documents_completed
                },
                "started_at": progress.started_at.isoformat() if progress.started_at else None,
                "completed_at": progress.completed_at.isoformat() if progress.completed_at else None,
                "last_updated": progress.last_updated.isoformat() if progress.last_updated else None,
                
                # Detailed data from each step
                "profile_data": {
                    "full_name": employee.full_name,
                    "phone": employee.phone,
                    "preferred_location": employee.preferred_location,
                    "availability": employee.availability
                } if progress.profile_completed else None,
                
                "skills_data": {
                    "skills": employee.skills or [],
                    "experience_years": employee.experience_years,
                    "years_in_hospitality": employee.years_in_hospitality,
                    "education": employee.education or []
                } if progress.skills_completed else None,
                
                "preferences_data": {
                    "preferred_role": employee.preferred_role.value if employee.preferred_role else None,
                    "cuisine_experience": employee.cuisine_experience or [],
                    "shift_preferences": employee.shift_preferences or [],
                    "preferred_shift": employee.preferred_shift,
                    "expected_salary_min": employee.expected_salary_min,
                    "expected_salary_max": employee.expected_salary_max
                } if progress.preferences_completed else None,
                
                "certifications_data": {
                    "food_safety_certified": employee.food_safety_certified,
                    "servsafe_certified": employee.servsafe_certified,
                    "alcohol_service_certified": employee.alcohol_service_certified,
                    "certifications": employee.certifications or []
                } if progress.certifications_completed else None,
                
                "documents_data": {
                    "resume_filename": employee.resume_filename,
                    "has_resume": bool(employee.resume_text or employee.resume_filename),
                    "resume_text_preview": employee.resume_text[:200] + "..." if employee.resume_text and len(employee.resume_text) > 200 else employee.resume_text
                } if progress.documents_completed else None
            }
            
            return response
            
        finally:
            db.close()
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching onboarding progress: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/resume/{employee_id}")
def download_resume(employee_id: int):
    """
    Download the employee's resume (either uploaded or generated).
    Returns the resume file if available.
    """
    try:
        db = SessionLocal()
        try:
            employee = db.query(Employee).filter(Employee.id == employee_id).first()
            if not employee:
                raise HTTPException(status_code=404, detail="Employee not found")
            
            # Check if resume file exists (uploaded PDF/file)
            if employee.resume_filename:
                # Look for resume in resumes directory
                resume_path = Path("resumes") / employee.resume_filename
                if resume_path.exists():
                    # Determine media type from file extension
                    media_type = "application/pdf" if resume_path.suffix.lower() == '.pdf' else "application/octet-stream"
                    return FileResponse(
                        path=str(resume_path),
                        filename=employee.resume_filename,
                        media_type=media_type
                    )
            
            # If no file but has resume text, return as text file
            if employee.resume_text:
                safe_filename = employee.full_name.replace(' ', '_').replace('/', '_')
                return Response(
                    content=employee.resume_text.encode('utf-8'),
                    media_type="text/plain; charset=utf-8",
                    headers={
                        "Content-Disposition": f"attachment; filename=\"{safe_filename}_Resume.txt\""
                    }
                )
            
            raise HTTPException(status_code=404, detail="No resume found for this employee")
            
        finally:
            db.close()
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading resume: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/data/{employee_id}")
def get_all_onboarding_data(employee_id: int):
    """
    Get ALL onboarding data for an employee in a comprehensive format.
    Useful for displaying complete profile on onboarding page.
    """
    try:
        db = SessionLocal()
        try:
            employee = db.query(Employee).filter(Employee.id == employee_id).first()
            if not employee:
                raise HTTPException(status_code=404, detail="Employee not found")
            
            progress = db.query(OnboardingProgress).filter(
                OnboardingProgress.employee_id == employee_id
            ).first()
            
            return {
                "employee_id": employee_id,
                "full_name": employee.full_name,
                "phone": employee.phone,
                "email": employee.user.email if employee.user else None,
                
                # All profile data
                "profile": {
                    "preferred_location": employee.preferred_location,
                    "availability": employee.availability,
                    "created_at": employee.created_at.isoformat() if employee.created_at else None
                },
                
                "skills": {
                    "skills_list": employee.skills or [],
                    "experience_years": employee.experience_years,
                    "years_in_hospitality": employee.years_in_hospitality,
                    "education": employee.education or [],
                    "profile_summary": employee.profile_summary
                },
                
                "preferences": {
                    "preferred_role": employee.preferred_role.value if employee.preferred_role else None,
                    "cuisine_experience": employee.cuisine_experience or [],
                    "shift_preferences": employee.shift_preferences or [],
                    "preferred_shift": employee.preferred_shift,
                    "expected_salary": {
                        "min": employee.expected_salary_min,
                        "max": employee.expected_salary_max
                    }
                },
                
                "certifications": {
                    "food_safety_certified": employee.food_safety_certified,
                    "servsafe_certified": employee.servsafe_certified,
                    "alcohol_service_certified": employee.alcohol_service_certified,
                    "other_certifications": employee.certifications or []
                },
                
                "documents": {
                    "resume_filename": employee.resume_filename,
                    "has_resume_text": bool(employee.resume_text),
                    "resume_length": len(employee.resume_text) if employee.resume_text else 0
                },
                
                "progress": {
                    "current_step": progress.current_step if progress else "profile",
                    "is_complete": progress.is_complete if progress else False,
                    "completion_percentage": progress.completion_percentage if progress else 0,
                    "steps_completed": {
                        "profile": progress.profile_completed if progress else False,
                        "skills": progress.skills_completed if progress else False,
                        "preferences": progress.preferences_completed if progress else False,
                        "certifications": progress.certifications_completed if progress else False,
                        "documents": progress.documents_completed if progress else False
                    }
                }
            }
            
        finally:
            db.close()
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching onboarding data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
