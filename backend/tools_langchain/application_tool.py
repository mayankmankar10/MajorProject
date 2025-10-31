# backend/tools_langchain/application_tool.py
from langchain.tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from backend.db.sql_db import get_db
from backend.db.models import Application, ApplicationStatus, Job, Employee
import json
import logging

logger = logging.getLogger(__name__)

class ApplicationToolInput(BaseModel):
    """Input schema for ApplicationTool."""
    job_id: int = Field(description="Job ID to apply for")
    employee_id: int = Field(description="Employee/Candidate ID")
    cover_letter: str = Field(default="", description="Optional cover letter text")
    match_score: float = Field(default=0.0, description="Optional match score (0-1)")

class ApplicationTool(BaseTool):
    """
    Submits job applications for candidates.
    """
    name: str = "ApplicationTool"
    description: str = """
    Submits a job application on behalf of a candidate.
    
    Input:
    - job_id (int): The job to apply for
    - employee_id (int): The candidate's employee ID
    - cover_letter (string, optional): Cover letter text
    - match_score (float, optional): Semantic match score (0-1)
    
    Output: JSON with application_id and status
    
    Use this when a candidate wants to apply for a job.
    """
    args_schema: Type[BaseModel] = ApplicationToolInput
    
    def _run(
        self,
        job_id: int,
        employee_id: int,
        cover_letter: str = "",
        match_score: float = 0.0
    ) -> str:
        """Submit application."""
        try:
            db: Session = next(get_db())
            
            # Check if job exists
            job = db.query(Job).filter(Job.id == job_id).first()
            if not job:
                return json.dumps({"error": f"Job {job_id} not found", "success": False})
            
            # Check if employee exists
            employee = db.query(Employee).filter(Employee.id == employee_id).first()
            if not employee:
                return json.dumps({"error": f"Employee {employee_id} not found", "success": False})
            
            # Check for duplicate application
            existing = db.query(Application).filter(
                Application.job_id == job_id,
                Application.employee_id == employee_id
            ).first()
            
            if existing:
                return json.dumps({
                    "application_id": existing.id,
                    "status": existing.status.value,
                    "message": "Application already exists",
                    "success": True
                })
            
            # Create application
            application = Application(
                job_id=job_id,
                employee_id=employee_id,
                cover_letter=cover_letter,
                match_score=match_score,
                status=ApplicationStatus.APPLIED
            )
            
            db.add(application)
            db.commit()
            db.refresh(application)
            
            result = {
                "application_id": application.id,
                "job_id": job_id,
                "job_title": job.title,
                "company": job.employer.company_name if job.employer else "Unknown",
                "employee_id": employee_id,
                "status": "applied",
                "match_score": match_score,
                "applied_at": application.applied_at.isoformat(),
                "message": "Application submitted successfully",
                "success": True
            }
            
            logger.info(f"✅ Application {application.id} submitted: Job {job_id} by Employee {employee_id}")
            return json.dumps(result)
            
        except Exception as e:
            logger.error(f"❌ Application submission error: {str(e)}")
            return json.dumps({"error": str(e), "success": False})
    
    async def _arun(
        self,
        job_id: int,
        employee_id: int,
        cover_letter: str = "",
        match_score: float = 0.0
    ) -> str:
        """Async implementation."""
        return self._run(job_id, employee_id, cover_letter, match_score)
