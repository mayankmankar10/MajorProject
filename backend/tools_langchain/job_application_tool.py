# backend/tools_langchain/job_application_tool.py
from langchain.tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from backend.db.sql_db import get_db
from backend.db.models import Application, Job, Employee, ApplicationStatus
from backend.cache.tool_cache import tool_cache
import json
import logging
import datetime

logger = logging.getLogger(__name__)

class JobApplicationToolInput(BaseModel):
    """Input schema for JobApplicationTool."""
    user_id: int = Field(description="ID of the user (employee) applying")
    job_id: int = Field(default=0, description="ID of the job to apply to (use either this OR job_index)")
    cover_letter: str = Field(default="", description="Optional cover letter text")
    match_score: float = Field(default=0.0, description="Optional pre-calculated match score from JobFinderTool (0-100). If provided, will be used instead of recalculating.")
    job_index: int = Field(default=None, description="The 1-based index of the job from the last search results (e.g., 1 for the first job). Use this when user says 'first job' or 'apply to #2'.")

class JobApplicationTool(BaseTool):
    """
    Creates a job application for an employee.
    Automatically calculates match score and creates application record.
    """
    name: str = "JobApplicationTool"
    description: str = """
    Creates a job application for an employee to a specific job.
    
    Input:
    - user_id (int): The user's ID (not employee ID)
    - job_id (int, optional): The EXACT database Job ID (e.g., 46, 207, 403). Use ONLY if you know the specific database ID.
    - job_index (int, optional): The position number from search results (1 for first, 2 for second, etc.). Use when user says "first job", "apply to #2", etc.
    - cover_letter (string, optional): Cover letter text
    - match_score (float, optional): Pre-calculated match score from search results (0-100)
    
    Output: JSON with application details including match score
    
    CRITICAL DECISION LOGIC:
    - If user says "first job", "second job", "job #3" → Use job_index (1, 2, 3)
    - If user provides exact Job ID like "Job 46" or you see it in search results → Use job_id
    - When in doubt, use job_index for ordinal references ("first", "second", "third")
    
    IMPORTANT: If applying from search results (JobFinderTool), ALWAYS pass the match_score 
    from the search result to maintain consistency. Extract it from the job data shown to user.
    
    Use this when:
    - Employee wants to apply to a job
    - Employee says "I want to apply", "submit my application", "apply for the first job"
    - After showing job listings and employee selects one
    """
    args_schema: Type[BaseModel] = JobApplicationToolInput
    
    def _calculate_match_score(self, employee: Employee, job: Job) -> float:
        """Calculate match score between employee and job."""
        score = 0.0
# ... (intermediate code unchanged)
    def _run(
        self,
        user_id: int,
        job_id: int = 0, # Default to 0 if using index
        cover_letter: str = "",
        match_score: float = 0.0,
        job_index: int = None # New argument
    ) -> str:
        """Create job application."""
        try:
            # Check context for index-based lookup
            if job_index is not None and job_index > 0:
                from backend.context import get_session_data
                last_results = get_session_data("last_job_search_results")
                
                if last_results and len(last_results) >= job_index:
                    # Index is 1-based, list is 0-based
                    target_job = last_results[job_index - 1]
                    job_id = target_job["job_id"]
                    # Use cached match score if not provided
                    if match_score == 0:
                        match_score = target_job.get("match_score", 0)
                    
                    logger.info(f"📍 Mapped Job Index #{job_index} → Job ID {job_id} (Score: {match_score})")
                else:
                    msg = f"Could not find job result #{job_index}. Please search for jobs again."
                    if not last_results:
                        msg += " (No search history found)"
                    return json.dumps({"success": False, "error": msg})
            
            # Validation
            if not job_id:
                return json.dumps({"success": False, "error": "Job ID or valid Job Index is required."})

            db: Session = next(get_db())
            
            # Get employee by USER ID
            employee = db.query(Employee).filter(Employee.user_id == user_id).first()
            if not employee:
                return json.dumps({
                    "success": False,
                    "error": f"Employee profile not found for User ID {user_id}"
                })
            
            employee_id = employee.id
            
            # Get job
            job = db.query(Job).filter(Job.id == job_id).first()
            
            # SMART FALLBACK: If job not found and ID is small (<20), assume it's an index
            if not job and job_id > 0 and job_id < 20:
                logger.info(f"🤔 Job {job_id} not found, checking if it's an index...")
                from backend.context import get_session_data
                last_results = get_session_data("last_job_search_results")
                
                if last_results and len(last_results) >= job_id:
                    target_job = last_results[job_id - 1] # 1-based index
                    real_job_id = target_job["job_id"]
                    
                    # Use cached match score if not provided
                    if match_score == 0:
                        match_score = target_job.get("match_score", 0)
                        
                    logger.info(f"💡 Smart Fallback: Treated ID {job_id} as Index #{job_id} → Found Job {real_job_id}")
                    # Retry query with real ID
                    job = db.query(Job).filter(Job.id == real_job_id).first()
                    job_id = real_job_id # Update for application record

            if not job:
                return json.dumps({
                    "success": False,
                    "error": f"Job {job_id} not found"
                })
            
            if not job.is_active:
                return json.dumps({
                    "success": False,
                    "error": "This job is no longer accepting applications"
                })
            
            # Check if already applied
            existing = db.query(Application).filter(
                Application.employee_id == employee_id,
                Application.job_id == job_id
            ).first()
            
            if existing:
                return json.dumps({
                    "success": False,
                    "error": "You have already applied to this job",
                    "application_id": existing.id,
                    "status": existing.status
                })
            
            # Use provided match score or calculate if not provided
            if match_score > 0:
                # Pre-calculated score from JobFinderTool (already 0-1 scale)
                final_match_score = match_score / 100.0 if match_score > 1 else match_score
                logger.info(f"✅ Using provided match score: {match_score}% → {final_match_score}")
            else:
                # Fallback: calculate score using legacy algorithm
                final_match_score = self._calculate_match_score(employee, job)
                logger.info(f"ℹ️  Calculated match score: {final_match_score}")
            
            # Create application
            application = Application(
                job_id=job_id,
                employee_id=employee_id,
                status=ApplicationStatus.APPLIED,
                match_score=final_match_score,
                cover_letter=cover_letter if cover_letter else None,
                applied_at=datetime.datetime.utcnow()
            )
            
            db.add(application)
            db.commit()
            db.refresh(application)
            
            # NEW: Notify employer about the application
            try:
                from backend.db.models import Notification, Employer
                from backend.notifications.connection_manager import manager
                from backend.utils.notification_helpers import add_credentials_to_notification_metadata
                import asyncio
                
                # Get employer information
                employer = db.query(Employer).filter(Employer.id == job.employer_id).first()
                
                if employer and employer.user_id:
                    # Prepare notification metadata with login credentials
                    notification_metadata = add_credentials_to_notification_metadata(
                        db=db,
                        recipient_id=employer.user_id,  # Employer receiving notification
                        sender_id=employee.user_id,      # Employee who applied
                        existing_metadata={
                            "application_id": application.id,
                            "employee_name": employee.full_name,
                            "job_title": job.title,
                            "match_score": match_score
                        }
                    )
                    
                    # Create notification in database
                    employer_notification = Notification(
                        recipient_id=employer.user_id,
                        title="New Application Received! 📋",
                        message=f"{employee.full_name} applied for {job.title}. Match score: {int(final_match_score*100)}%",
                        notification_type="application",
                        action_url=f"/employer/applications/{application.id}",
                        meta_data=notification_metadata  # Include credentials
                    )
                    db.add(employer_notification)
                    db.commit()
                    db.refresh(employer_notification)
                    
                    # Database notification created successfully
                    # Real-time WebSocket notification will be sent by the notification system
                    logger.info(f"✅ Employer {employer.user_id} notified about application {application.id} (DB notification created)")
                        
            except Exception as notif_error:
                logger.warning(f"⚠️  Failed to notify employer: {notif_error}")
                # Non-critical - don't fail the application
            
            result = {
                "success": True,
                "application_id": application.id,
                "job_title": job.title,
                "company": job.employer.company_name if job.employer else "Unknown",
                "match_score": final_match_score,
                "match_percentage": f"{int(final_match_score * 100)}%",
                "status": application.status,
                "applied_at": application.applied_at.isoformat(),
                "message": f"✅ Application submitted successfully! You're a {int(final_match_score * 100)}% match for this position."
            }
            
            logger.info(f"✅ Application created: Employee {employee_id} → Job {job_id} (Match: {final_match_score})")
            return json.dumps(result)
            
        except Exception as e:
            logger.error(f"❌ Application creation error: {str(e)}")
            return json.dumps({
                "success": False,
                "error": f"Failed to create application: {str(e)}"
            })
    
    async def _arun(
        self,
        user_id: int,
        job_id: int = 0,
        cover_letter: str = "",
        match_score: float = 0.0,
        job_index: int = None
    ) -> str:
        """Async implementation."""
        return self._run(user_id, job_id, cover_letter, match_score, job_index)
