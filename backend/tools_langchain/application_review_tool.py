# backend/tools_langchain/application_review_tool.py
from langchain.tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from backend.db.sql_db import get_db
from backend.db.models import Application, Job, Employee, ApplicationStatus
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class ApplicationReviewInput(BaseModel):
    """Input schema for ApplicationReviewTool."""
    application_id: int = Field(description="ID of the application to review")

class ApplicationReviewTool(BaseTool):
    """
    Review a job application and automatically mark it as 'reviewed'.
    
    This tool:
    1. Fetches application details (candidate info, job info, match score)
    2. Provides comprehensive analysis
    3. Automatically updates application status to 'reviewed'
    4. Returns detailed review information for the employer
    
    Use this when an employer wants to review a specific application.
    """
    
    name: str = "ApplicationReviewTool"
    description: str = """
    Review a job application and get detailed candidate insights.
    Automatically marks the application as 'reviewed' in the system.
    
    Input:
    - application_id: The ID of the application to review
    
    Returns comprehensive review including:
    - Candidate name, experience, skills, certifications
    - Job details and match score
    - Analysis and recommendations
    - Application status (automatically updated to 'reviewed')
    """
    args_schema: Type[BaseModel] = ApplicationReviewInput
    
    def _run(self, application_id: int) -> str:
        """Review application and mark as reviewed."""
        try:
            db: Session = next(get_db())
            
            # Get application
            application = db.query(Application).filter(Application.id == application_id).first()
            if not application:
                return json.dumps({
                    "success": False,
                    "error": f"Application #{application_id} not found"
                })
            
            # Get related data
            employee = db.query(Employee).filter(Employee.id == application.employee_id).first()
            job = db.query(Job).filter(Job.id == application.job_id).first()
            
            if not employee:
                return json.dumps({
                    "success": False,
                    "error": "Candidate information not found"
                })
            
            if not job:
                return json.dumps({
                    "success": False,
                    "error": "Job information not found"
                })
            
            # Update status to REVIEWING only if not already in that state (idempotent)
            old_status = application.status.value if hasattr(application.status, 'value') else str(application.status)
            status_updated = False
            
            if application.status != ApplicationStatus.REVIEWING:
                application.status = ApplicationStatus.REVIEWING
                application.reviewed_at = datetime.utcnow()
                application.updated_at = datetime.utcnow()
                db.commit()
                status_updated = True
                logger.info(f"✅ Application #{application_id} marked as REVIEWING (was: {old_status})")
            else:
                logger.info(f"ℹ️  Application #{application_id} already in REVIEWING status, skipping update")

            
            # Build comprehensive review data
            review_data = {
                "success": True,
                "application_id": application.id,
                "status_updated": status_updated,
                "old_status": old_status,
                "new_status": "reviewing",
                "candidate": {
                    "name": employee.full_name,
                    "phone": employee.phone,
                    "location": employee.preferred_location,
                    "hospitality_years": employee.years_in_hospitality or 0,
                    "skills": employee.skills or [],
                    "soft_skills": employee.soft_skills or [],
                    "certifications": employee.certifications or [],
                    "preferred_role": employee.preferred_role.value if employee.preferred_role else None,
                    "preferred_shift": employee.preferred_shift,
                    "expected_salary": f"₹{employee.expected_salary_min:,} - ₹{employee.expected_salary_max:,}" if employee.expected_salary_min and employee.expected_salary_max else "Not specified",
                    "food_safety_certified": employee.food_safety_certified,
                    "servsafe_certified": employee.servsafe_certified,
                    "profile_summary": employee.profile_summary
                },
                "job": {
                    "title": job.title,
                    "location": job.location,
                    "job_type": job.job_type,
                    "salary_range": job.salary_range,
                    "description": job.description,
                    "requirements": job.requirements or {},
                    "min_experience": job.min_hospitality_experience or 0,
                    "requires_food_safety": job.requires_food_safety,
                    "cuisine_type": job.cuisine_type,
                    "shift_type": job.shift_type
                },
                "application_details": {
                    "applied_at": application.applied_at.isoformat() if application.applied_at else None,
                    "match_score": round(application.match_score * 100) if application.match_score else 0,
                    "cover_letter": application.cover_letter,
                    "notes": application.notes
                },
                "message": f"Application #{application_id} has been marked as 'reviewing' and is ready for detailed review."
            }
            
            return json.dumps(review_data, indent=2)
            
        except Exception as e:
            logger.error(f"Error reviewing application: {str(e)}")
            return json.dumps({
                "success": False,
                "error": f"Failed to review application: {str(e)}"
            })
    
    async def _arun(self, application_id: int) -> str:
        """Async implementation."""
        return self._run(application_id)
