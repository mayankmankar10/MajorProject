# backend/tools_langchain/interview_scheduler_tool.py
from langchain.tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from backend.db.sql_db import get_db
from backend.db.models import Interview, Application, InterviewStatus
import logging
import json

logger = logging.getLogger(__name__)

class InterviewSchedulerInput(BaseModel):
    """Input schema for InterviewSchedulerTool."""
    application_id: int = Field(description="The ID of the application to schedule interview for")
    scheduled_at: str = Field(description="Scheduled datetime in ISO format (e.g., '2024-01-15T14:00:00')")
    duration_minutes: int = Field(default=60, description="Duration of interview in minutes")
    location: str = Field(default="", description="Physical location or 'Virtual'")
    meeting_link: str = Field(default="", description="Video call link (e.g., Zoom, Meet)")

class InterviewSchedulerTool(BaseTool):
    """
    Tool for scheduling interviews between employers and candidates.
    Creates interview records with meeting details and calendar integration.
    """
    name: str = "InterviewSchedulerTool"
    description: str = """
    Schedules an interview for a job application. Creates interview record with meeting details.
    
    Input:
    - application_id (int): The application ID
    - scheduled_at (string): ISO datetime (e.g., "2024-01-15T14:00:00")
    - duration_minutes (int, optional): Interview duration (default 60)
    - location (string, optional): Physical location or "Virtual"
    - meeting_link (string, optional): Video call URL
    
    Output: JSON with interview details including ID, time, location, and meeting link
    
    Use this when employer wants to schedule an interview with a candidate.
    """
    args_schema: Type[BaseModel] = InterviewSchedulerInput
    
    def _run(
        self,
        application_id: int,
        scheduled_at: str,
        duration_minutes: int = 60,
        location: str = "",
        meeting_link: str = ""
    ) -> str:
        """Schedule an interview."""
        try:
            db: Session = next(get_db())
            
            # Parse datetime
            try:
                scheduled_datetime = datetime.fromisoformat(scheduled_at.replace('Z', '+00:00'))
            except:
                scheduled_datetime = datetime.now() + timedelta(days=2)
            
            # Check if interview already exists
            existing = db.query(Interview).filter(Interview.application_id == application_id).first()
            if existing:
                # Update existing
                existing.scheduled_at = scheduled_datetime
                existing.duration_minutes = duration_minutes
                existing.location = location or existing.location
                existing.meeting_link = meeting_link or existing.meeting_link
                existing.status = InterviewStatus.SCHEDULED
                db.commit()
                
                result = {
                    "interview_id": existing.id,
                    "application_id": application_id,
                    "scheduled_at": scheduled_datetime.isoformat(),
                    "duration_minutes": duration_minutes,
                    "location": existing.location,
                    "meeting_link": existing.meeting_link,
                    "status": "scheduled",
                    "message": "Interview rescheduled successfully"
                }
                logger.info(f"✅ Interview {existing.id} rescheduled")
                return json.dumps(result)
            
            # Create new interview
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
            
            result = {
                "interview_id": interview.id,
                "application_id": application_id,
                "scheduled_at": scheduled_datetime.isoformat(),
                "duration_minutes": duration_minutes,
                "location": interview.location,
                "meeting_link": interview.meeting_link,
                "status": "scheduled",
                "message": "Interview scheduled successfully"
            }
            
            logger.info(f"✅ Interview {interview.id} scheduled for application {application_id}")
            return json.dumps(result)
            
        except Exception as e:
            logger.error(f"❌ Interview scheduling error: {str(e)}")
            return json.dumps({"error": str(e), "success": False})
    
    async def _arun(
        self,
        application_id: int,
        scheduled_at: str,
        duration_minutes: int = 60,
        location: str = "",
        meeting_link: str = ""
    ) -> str:
        """Async implementation."""
        return self._run(application_id, scheduled_at, duration_minutes, location, meeting_link)
