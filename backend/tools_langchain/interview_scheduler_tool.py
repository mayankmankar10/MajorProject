# backend/tools_langchain/interview_scheduler_tool.py
from langchain.tools import BaseTool
from typing import Type, Any
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from backend.db.sql_db import get_db
from backend.db.models import Interview, Application, InterviewStatus, Employee, Job, ApplicationStatus
from backend.tools_langchain.notification_tool import NotificationTool
import logging
import json

logger = logging.getLogger(__name__)

class InterviewSchedulerInput(BaseModel):
    """Input schema for InterviewSchedulerTool."""
    action: str = Field(description="Action: schedule, reschedule, cancel, get_details, complete, add_feedback, list_upcoming")
    application_id: int = Field(default=0, description="Application ID (for schedule)")
    interview_id: int = Field(default=0, description="Interview ID (for reschedule, cancel, get_details, complete, add_feedback)")
    employee_id: int = Field(default=0, description="Employee ID (for list_upcoming)")
    scheduled_at: str = Field(default="", description="ISO datetime (e.g., '2024-01-15T14:00:00')")
    duration_minutes: int = Field(default=60, description="Interview duration in minutes")
    location: str = Field(default="", description="Physical location or 'Virtual'")
    meeting_link: str = Field(default="", description="Video call link")
    feedback: str = Field(default="", description="Interviewer feedback (for add_feedback, complete)")

class InterviewSchedulerTool(BaseTool):
    """
    Complete interview lifecycle management tool.
    """
    name: str = "InterviewSchedulerTool"
    description: str = """
    Manage complete interview lifecycle with multiple actions.
    
    Actions:
    - schedule: Schedule new interview (requires application_id, scheduled_at)
    - reschedule: Change interview date/time (requires interview_id, scheduled_at)
    - cancel: Cancel interview (requires interview_id)
    - get_details: Get interview information (requires interview_id)
    - complete: Mark interview as completed (requires interview_id, optional feedback)
    - add_feedback: Add interviewer notes (requires interview_id, feedback)
    - list_upcoming: List upcoming interviews (requires employee_id)
    
    Use this for all interview management tasks.
    """
    args_schema: Type[BaseModel] = InterviewSchedulerInput
    
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    def _schedule(self, db: Session, application_id: int, scheduled_at: str, 
                  duration_minutes: int, location: str, meeting_link: str) -> dict:
        """Schedule new interview."""
        try:
            scheduled_datetime = datetime.fromisoformat(scheduled_at.replace('Z', '+00:00'))
        except:
            return {"error": "Invalid datetime format. Use ISO format (e.g., '2024-01-15T14:00:00')", "success": False}
        
        # Check if interview already exists
        existing = db.query(Interview).filter(Interview.application_id == application_id).first()
        if existing:
            return {"error": f"Interview already exists (ID: {existing.id}). Use 'reschedule' to change it.", "success": False}
        
        # Get application details
        app = db.query(Application).filter(Application.id == application_id).first()
        if not app:
            return {"error": f"Application {application_id} not found", "success": False}
        
        # Create interview
        interview = Interview(
            application_id=application_id,
            scheduled_at=scheduled_datetime,
            duration_minutes=duration_minutes,
            location=location or "Virtual",
            meeting_link=meeting_link or "TBD",
            status=InterviewStatus.SCHEDULED
        )
        
        db.add(interview)
        db.commit()
        db.refresh(interview)
        
        # Update application status to INTERVIEW_SCHEDULED
        app.status = ApplicationStatus.INTERVIEW_SCHEDULED
        app.updated_at = datetime.utcnow()
        db.commit()
        logger.info(f"✅ Application #{application_id} status updated to INTERVIEW_SCHEDULED")
        
        # Send notification to employee
        try:
            job = db.query(Job).filter(Job.id == app.job_id).first()
            employee = db.query(Employee).filter(Employee.id == app.employee_id).first()
            
            # Get company name from employer
            company_name = "Company"
            if job and job.employer:
                company_name = job.employer.company_name
            
            # Format rich notification message
            notification_message = f"""Your interview has been scheduled!

📍 Company: {company_name}
💼 Position: {job.title if job else 'Position'}
📅 Date & Time: {scheduled_datetime.strftime('%B %d, %Y at %I:%M %p')}
📌 Location: {interview.location}
🔗 Meeting Link: {interview.meeting_link}

Good luck with your interview!"""
            
            notification_tool = NotificationTool()
            notification_tool._run(
                user_id=employee.user_id if employee else app.employee_id,
                title="Interview Scheduled",
                message=notification_message,
                notification_type="interview_scheduled",
                action_url="/employee/interviews"
            )
        except Exception as e:
            logger.warning(f"⚠️ Failed to send notification: {str(e)}")
        
        logger.info(f"✅ Interview {interview.id} scheduled for application {application_id}")
        
        return {
            "interview_id": interview.id,
            "application_id": application_id,
            "scheduled_at": scheduled_datetime.isoformat(),
            "duration_minutes": duration_minutes,
            "location": interview.location,
            "meeting_link": interview.meeting_link,
            "status": "scheduled",
            "success": True,
            "message": "Interview scheduled successfully"
        }
    
    def _reschedule(self, db: Session, interview_id: int, scheduled_at: str) -> dict:
        """Reschedule existing interview."""
        interview = db.query(Interview).filter(Interview.id == interview_id).first()
        if not interview:
            return {"error": f"Interview {interview_id} not found", "success": False}
        
        try:
            new_datetime = datetime.fromisoformat(scheduled_at.replace('Z', '+00:00'))
        except:
            return {"error": "Invalid datetime format", "success": False}
        
        old_datetime = interview.scheduled_at
        interview.scheduled_at = new_datetime
        db.commit()
        
        # Send notification
        try:
            app = db.query(Application).filter(Application.id == interview.application_id).first()
            if app:
                notification_tool = NotificationTool()
                notification_tool._run(
                    user_id=app.employee_id,
                    title="Interview Rescheduled",
                    message=f"Interview rescheduled to {new_datetime.strftime('%b %d, %Y at %I:%M %p')}",
                    notification_type="interview_scheduled"
                )
        except Exception as e:
            logger.warning(f"⚠️ Failed to send notification: {str(e)}")
        
        logger.info(f"✅ Interview {interview_id} rescheduled: {old_datetime} → {new_datetime}")
        
        return {
            "interview_id": interview_id,
            "old_time": old_datetime.isoformat(),
            "new_time": new_datetime.isoformat(),
            "success": True,
            "message": "Interview rescheduled successfully"
        }
    
    def _cancel(self, db: Session, interview_id: int) -> dict:
        """Cancel interview."""
        interview = db.query(Interview).filter(Interview.id == interview_id).first()
        if not interview:
            return {"error": f"Interview {interview_id} not found", "success": False}
        
        interview.status = InterviewStatus.CANCELLED
        db.commit()
        
        # Send notification
        try:
            app = db.query(Application).filter(Application.id == interview.application_id).first()
            if app:
                notification_tool = NotificationTool()
                notification_tool._run(
                    user_id=app.employee_id,
                    title="Interview Cancelled",
                    message="Your interview has been cancelled. You will be contacted for rescheduling.",
                    notification_type="application_update"
                )
        except Exception as e:
            logger.warning(f"⚠️ Failed to send notification: {str(e)}")
        
        logger.info(f"✅ Interview {interview_id} cancelled")
        
        return {
            "interview_id": interview_id,
            "status": "cancelled",
            "success": True,
            "message": "Interview cancelled successfully"
        }
    
    def _get_details(self, db: Session, interview_id: int) -> dict:
        """Get interview details."""
        interview = db.query(Interview).filter(Interview.id == interview_id).first()
        if not interview:
            return {"error": f"Interview {interview_id} not found", "success": False}
        
        app = db.query(Application).filter(Application.id == interview.application_id).first()
        employee = db.query(Employee).filter(Employee.id == app.employee_id).first() if app else None
        job = db.query(Job).filter(Job.id == app.job_id).first() if app else None
        
        return {
            "interview_id": interview.id,
            "application_id": interview.application_id,
            "job_title": job.title if job else "Unknown",
            "candidate_name": employee.full_name if employee else "Unknown",
            "candidate_email": employee.user.email if (employee and employee.user) else "Unknown",
            "scheduled_at": interview.scheduled_at.isoformat(),
            "duration_minutes": interview.duration_minutes,
            "location": interview.location,
            "meeting_link": interview.meeting_link,
            "status": interview.status.value if hasattr(interview.status, 'value') else str(interview.status),
            "feedback": interview.feedback or "",
            "success": True
        }
    
    def _complete(self, db: Session, interview_id: int, feedback: str = "") -> dict:
        """Mark interview as completed."""
        interview = db.query(Interview).filter(Interview.id == interview_id).first()
        if not interview:
            return {"error": f"Interview {interview_id} not found", "success": False}
        
        interview.status = InterviewStatus.COMPLETED
        if feedback:
            interview.feedback = feedback
        db.commit()
        
        logger.info(f"✅ Interview {interview_id} marked as completed")
        
        return {
            "interview_id": interview_id,
            "status": "completed",
            "feedback": interview.feedback or "",
            "success": True,
            "message": "Interview marked as completed"
        }
    
    def _add_feedback(self, db: Session, interview_id: int, feedback: str) -> dict:
        """Add interviewer feedback."""
        interview = db.query(Interview).filter(Interview.id == interview_id).first()
        if not interview:
            return {"error": f"Interview {interview_id} not found", "success": False}
        
        interview.feedback = feedback
        db.commit()
        
        logger.info(f"✅ Feedback added to interview {interview_id}")
        
        return {
            "interview_id": interview_id,
            "feedback": feedback,
            "success": True,
            "message": "Feedback added successfully"
        }
    
    def _list_upcoming(self, db: Session, employee_id: int) -> dict:
        """List upcoming interviews for employee."""
        apps = db.query(Application).filter(Application.employee_id == employee_id).all()
        app_ids = [app.id for app in apps]
        
        interviews = db.query(Interview).filter(
            Interview.application_id.in_(app_ids),
            Interview.status == InterviewStatus.SCHEDULED,
            Interview.scheduled_at >= datetime.utcnow()
        ).order_by(Interview.scheduled_at).all()
        
        results = []
        for interview in interviews:
            app = db.query(Application).filter(Application.id == interview.application_id).first()
            job = db.query(Job).filter(Job.id == app.job_id).first() if app else None
            
            results.append({
                "interview_id": interview.id,
                "job_title": job.title if job else "Unknown",
                "company": job.employer.company_name if job and job.employer else "Unknown",
                "scheduled_at": interview.scheduled_at.isoformat(),
                "duration_minutes": interview.duration_minutes,
                "location": interview.location,
                "meeting_link": interview.meeting_link
            })
        
        return {
            "employee_id": employee_id,
            "total_interviews": len(results),
            "interviews": results,
            "success": True
        }
    
    def _run(
        self,
        action: str,
        application_id: int = 0,
        interview_id: int = 0,
        employee_id: int = 0,
        scheduled_at: str = "",
        duration_minutes: int = 60,
        location: str = "",
        meeting_link: str = "",
        feedback: str = ""
    ) -> str:
        """Execute the requested action."""
        try:
            db: Session = next(get_db())
            
            if action == "schedule":
                if not application_id or not scheduled_at:
                    return json.dumps({"error": "application_id and scheduled_at required", "success": False})
                result = self._schedule(db, application_id, scheduled_at, duration_minutes, location, meeting_link)
                
            elif action == "reschedule":
                if not interview_id or not scheduled_at:
                    return json.dumps({"error": "interview_id and scheduled_at required", "success": False})
                result = self._reschedule(db, interview_id, scheduled_at)
                
            elif action == "cancel":
                if not interview_id:
                    return json.dumps({"error": "interview_id required", "success": False})
                result = self._cancel(db, interview_id)
                
            elif action == "get_details":
                if not interview_id:
                    return json.dumps({"error": "interview_id required", "success": False})
                result = self._get_details(db, interview_id)
                
            elif action == "complete":
                if not interview_id:
                    return json.dumps({"error": "interview_id required", "success": False})
                result = self._complete(db, interview_id, feedback)
                
            elif action == "add_feedback":
                if not interview_id or not feedback:
                    return json.dumps({"error": "interview_id and feedback required", "success": False})
                result = self._add_feedback(db, interview_id, feedback)
                
            elif action == "list_upcoming":
                if not employee_id:
                    return json.dumps({"error": "employee_id required", "success": False})
                result = self._list_upcoming(db, employee_id)
                
            else:
                return json.dumps({
                    "error": f"Invalid action '{action}'. Valid: schedule, reschedule, cancel, get_details, complete, add_feedback, list_upcoming",
                    "success": False
                })
            
            return json.dumps(result)
            
        except Exception as e:
            logger.error(f"❌ InterviewSchedulerTool error: {str(e)}")
            return json.dumps({"error": str(e), "success": False})
    
    async def _arun(
        self,
        action: str,
        application_id: int = 0,
        interview_id: int = 0,
        employee_id: int = 0,
        scheduled_at: str = "",
        duration_minutes: int = 60,
        location: str = "",
        meeting_link: str = "",
        feedback: str = ""
    ) -> str:
        """Async implementation."""
        return self._run(action, application_id, interview_id, employee_id, scheduled_at, 
                        duration_minutes, location, meeting_link, feedback)
