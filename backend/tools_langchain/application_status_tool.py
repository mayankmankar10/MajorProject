# backend/tools_langchain/application_status_tool.py
from langchain.tools import BaseTool
from typing import Type, Any
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy.orm import Session
from backend.db.sql_db import get_db
from backend.db.models import Application, ApplicationStatus, Job, Employee
from backend.tools_langchain.notification_tool import NotificationTool
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class ApplicationStatusInput(BaseModel):
    """Input schema for ApplicationStatusTool."""
    action: str = Field(description="Action: get_status, update_status, list_my_applications, get_latest_application, list_job_applications")
    application_id: int = Field(default=0, description="Application ID (for get_status, update_status)")
    user_id: int = Field(default=0, description="User ID (will be resolved to employee_id for list_my_applications)")
    candidate_name: str = Field(default="", description="Candidate Name (for find_application_by_candidate)")
    job_id: int = Field(default=0, description="Job ID (for list_job_applications)")
    new_status: str = Field(default="", description="New status (for update_status): applied, reviewed, reviewing, shortlisted, interview_scheduled, offer_sent, offer_accepted, offer_declined, selected, hired, rejected")

class ApplicationStatusTool(BaseTool):
    """
    Track and manage application statuses for both employers and employees.
    """
    name: str = "ApplicationStatusTool"
    description: str = """
    Track and update application statuses.
    
    Actions:
    - get_status: Get current status of an application (requires application_id)
    - update_status: Change application status (requires application_id, new_status)
    - find_application_by_candidate: Find applications by candidate name (requires candidate_name). Useful for employers to find the ID before updating status.
    - list_my_applications: FOR CANDIDATES ONLY. List all applications for a user (requires user_id)
    - get_latest_application: Get the most recent application for a user (requires user_id)
    - list_job_applications: List all applications for a job (requires job_id)
    
    Valid statuses: applied, reviewed, reviewing, shortlisted, interview_scheduled, offer_sent, offer_accepted, offer_declined, selected, hired, rejected
    """
    args_schema: Type[BaseModel] = ApplicationStatusInput
    
    model_config = ConfigDict(arbitrary_types_allowed=True)

    def _find_application_by_candidate(self, db: Session, candidate_name: str) -> dict:
        """Find applications matching a candidate's name."""
        from sqlalchemy import text
        
        # Find employees matching the name
        employees = db.query(Employee).filter(Employee.full_name.ilike(f"%{candidate_name}%")).all()
        
        if not employees:
            return {
                "error": f"No candidates found matching '{candidate_name}'",
                "success": False
            }
        
        employee_ids = [e.id for e in employees]
        
        # Use raw SQL to avoid enum validation issues
        # This way we can read applications even if they have invalid status values
        try:
            placeholders = ','.join([':id' + str(i) for i in range(len(employee_ids))])
            params = {f'id{i}': emp_id for i, emp_id in enumerate(employee_ids)}
            
            result = db.execute(
                text(f"""
                    SELECT a.id, a.employee_id, a.job_id, a.status, a.match_score, a.applied_at
                    FROM applications a
                    WHERE a.employee_id IN ({placeholders})
                """),
                params
            )
            apps_raw = result.fetchall()
            
            if not apps_raw:
                return {
                    "error": f"No applications found for candidate '{candidate_name}'",
                    "success": False
                }
                
            results = []
            for app_id, employee_id, job_id, status, match_score, applied_at in apps_raw:
                job = db.query(Job).filter(Job.id == job_id).first()
                emp = next((e for e in employees if e.id == employee_id), None)
                
                # Handle datetime serialization properly
                applied_at_str = None
                if applied_at:
                    if hasattr(applied_at, 'isoformat'):
                        applied_at_str = applied_at.isoformat()
                    else:
                        applied_at_str = str(applied_at)
                
                results.append({
                    "application_id": app_id,
                    "candidate_name": emp.full_name if emp else "Unknown",
                    "job_title": job.title if job else "Unknown",
                    "status": status,  # Already a string from raw SQL
                    "match_score": match_score,
                    "applied_at": applied_at_str
                })
                
            return {
                "query": candidate_name,
                "count": len(results),
                "applications": results,
                "success": True,
                "message": f"Found {len(results)} applications for '{candidate_name}'. Use application_id to update status."
            }
        except Exception as e:
            logger.error(f"❌ Error querying applications: {str(e)}")
            return {
                "error": f"Failed to query applications: {str(e)}",
                "success": False
            }
    
    def _get_status(self, db: Session, application_id: int) -> dict:
        """Get status of a specific application."""
        app = db.query(Application).filter(Application.id == application_id).first()
        
        if not app:
            return {"error": f"Application {application_id} not found", "success": False}
        
        job = db.query(Job).filter(Job.id == app.job_id).first()
        employee = db.query(Employee).filter(Employee.id == app.employee_id).first()
        
        return {
            "application_id": app.id,
            "job_id": app.job_id,
            "job_title": job.title if job else "Unknown",
            "company": job.employer.company_name if job and job.employer else "Unknown",
            "employee_id": app.employee_id,
            "employee_name": employee.full_name if employee else "Unknown",
            "status": app.status.value if hasattr(app.status, 'value') else str(app.status),
            "match_score": app.match_score,
            "applied_at": app.applied_at.isoformat() if app.applied_at else None,
            "updated_at": app.updated_at.isoformat() if app.updated_at else None,
            "success": True
        }
    
    def _update_status(self, db: Session, application_id: int, new_status: str) -> dict:
        """Update application status and send notification."""
        from sqlalchemy import text
        
        # Use raw SQL to avoid enum validation issues when loading the application
        result = db.execute(
            text("SELECT id, job_id, employee_id, status FROM applications WHERE id = :app_id"),
            {"app_id": application_id}
        )
        app_data = result.fetchone()
        
        if not app_data:
            return {"error": f"Application {application_id} not found", "success": False}
        
        app_id, job_id, employee_id, old_status = app_data
        
        # Normalize and validate status
        # Map common variations to the correct enum member names
        status_mapping = {
            "applied": "APPLIED",
            "reviewed": "REVIEWING",  # Map reviewed to REVIEWING
            "reviewing": "REVIEWING",
            "shortlisted": "SHORTLISTED",
            "interview_scheduled": "INTERVIEW_SCHEDULED",
            "offer_extended": "OFFER_SENT",  # Map offer_extended to OFFER_SENT
            "offer_sent": "OFFER_SENT",
            "offer_accepted": "OFFER_ACCEPTED",
            "offer_declined": "OFFER_DECLINED",
            "selected": "SELECTED",
            "hired": "HIRED",
            "rejected": "REJECTED"
        }
        
        # Normalize input
        normalized_status = new_status.lower().strip()
        
        # Get the enum member name
        enum_member_name = status_mapping.get(normalized_status, new_status.upper())
        
        # Validate that the enum member exists
        if enum_member_name not in ApplicationStatus.__members__:
            valid_values = list(status_mapping.keys())
            return {
                "error": f"Invalid status '{new_status}'. Valid options: {', '.join(valid_values)}",
                "success": False
            }
        
        # Get the enum value (lowercase string) to store in the database
        new_status_value = ApplicationStatus[enum_member_name].value
        
        # Update status using raw SQL to avoid enum validation issues
        try:
            db.execute(
                text("UPDATE applications SET status = :new_status, updated_at = :updated_at WHERE id = :app_id"),
                {
                    "new_status": new_status_value,
                    "updated_at": datetime.utcnow(),
                    "app_id": application_id
                }
            )
            db.commit()
        except KeyError as e:
            logger.error(f"❌ Failed to set status to {enum_member_name}: {str(e)}")
            return {
                "error": f"Failed to update status: {str(e)}",
                "success": False
            }
        
        # AUTOMATICALLY CREATE OFFER if status is 'selected' or 'offer_sent'
        # This ensures the application appears in the 'Offers' page
        if new_status_value in ["selected", "offer_sent"]:
            from backend.db.models import Offer
            
            # Check if offer already exists
            existing_offer = db.query(Offer).filter(Offer.application_id == application_id).first()
            
            if not existing_offer:
                try:
                    new_offer = Offer(
                        application_id=application_id,
                        status="pending",  # Initial status
                        sent_at=datetime.utcnow()
                    )
                    db.add(new_offer)
                    db.commit()
                    logger.info(f"✅ Created new Offer record because status changed to {new_status_value}")
                except Exception as e:
                    logger.error(f"❌ Failed to auto-create offer: {str(e)}")
            else:
                logger.info(f"ℹ️  Offer already exists for application {application_id}, skipping creation")
        job = db.query(Job).filter(Job.id == job_id).first()
        employee = db.query(Employee).filter(Employee.id == employee_id).first()
        
        # Send notification to employee (using user_id, not employee_id)
        if employee and employee.user_id:
            try:
                notification_tool = NotificationTool()
                notification_tool._run(
                    user_id=employee.user_id,  # FIXED: Use user_id for notifications
                    title="Application Status Update",
                    message=f"Your application for {job.title if job else 'the job'} has been updated to: {new_status_value}",
                    notification_type="application_update"
                )
                logger.info(f"✅ Notification sent to user {employee.user_id} (employee {employee_id})")
            except Exception as e:
                logger.warning(f"⚠️ Failed to send notification: {str(e)}")
        
        logger.info(f"✅ Application {application_id} status: {old_status} → {new_status_value}")
        
        return {
            "application_id": application_id,
            "employee_id": employee_id,  # ADD: So agent can use this for OnboardingTool
            "job_id": job_id,              # ADD: So agent can use this for OnboardingTool
            "job_title": job.title if job else "Unknown",
            "old_status": old_status,
            "new_status": new_status_value,
            "updated_at": datetime.utcnow().isoformat(),
            "notification_sent": True,
            "success": True,
            "message": f"Status updated from '{old_status}' to '{new_status_value}'"
        }
    
    def _list_my_applications(self, db: Session, employee_id: int) -> dict:
        """List all applications for an employee using raw SQL to avoid enum issues."""
        from sqlalchemy import text
        
        try:
            # Use raw SQL to avoid enum validation issues
            result = db.execute(
                text("""
                    SELECT a.id, a.job_id, a.status, a.match_score, a.applied_at, a.updated_at,
                           j.title, e.company_name, j.location
                    FROM applications a
                    LEFT JOIN jobs j ON a.job_id = j.id
                    LEFT JOIN employers e ON j.employer_id = e.id
                    WHERE a.employee_id = :emp_id
                    ORDER BY a.applied_at DESC
                """),
                {"emp_id": employee_id}
            )
            apps_raw = result.fetchall()
            
            results = []
            for app_id, job_id, status, match_score, applied_at, updated_at, job_title, company_name, location in apps_raw:
                # Handle datetime serialization
                applied_at_str = applied_at.isoformat() if hasattr(applied_at, 'isoformat') else str(applied_at) if applied_at else None
                updated_at_str = updated_at.isoformat() if hasattr(updated_at, 'isoformat') else str(updated_at) if updated_at else None
                
                results.append({
                    "application_id": app_id,
                    "job_id": job_id,
                    "job_title": job_title or "Unknown",
                    "company": company_name or "Unknown",
                    "location": location or "Unknown",
                    "status": status,  # Already a string from raw SQL
                    "match_score": match_score,
                    "applied_at": applied_at_str,
                    "updated_at": updated_at_str
                })
            
            return {
                "employee_id": employee_id,
                "total_applications": len(results),
                "applications": results,
                "success": True
            }
        except Exception as e:
            logger.error(f"❌ Error listing applications: {str(e)}")
            return {
                "error": f"Failed to list applications: {str(e)}",
                "success": False
            }
    
    
    def _get_latest_application(self, db: Session, user_id: int) -> dict:
        """Get the most recent application for a user.
        
        Note: user_id can be either:
        - Actual user_id (for direct API calls)
        - Employee_id (when called by orchestrator with [Employee ID: X])
        """
        from sqlalchemy import text
        
        # Try to resolve user_id to employee_id
        # First check if it's already an employee_id
        employee = db.query(Employee).filter(Employee.id == user_id).first()
        
        if not employee:
            # If not found by employee_id, try user_id
            employee = db.query(Employee).filter(Employee.user_id == user_id).first()
        
        if not employee:
            return {
                "error": f"No employee profile found for ID {user_id}",
                "success": False
            }
        
        # Use raw SQL to avoid enum validation issues (e.g., 'hired' vs 'HIRED')
        try:
            result = db.execute(
                text("""
                    SELECT a.id, a.job_id, a.status, a.match_score, a.applied_at, a.updated_at,
                           j.title, e.company_name, j.location
                    FROM applications a
                    LEFT JOIN jobs j ON a.job_id = j.id
                    LEFT JOIN employers e ON j.employer_id = e.id
                    WHERE a.employee_id = :emp_id
                    ORDER BY a.applied_at DESC
                    LIMIT 1
                """),
                {"emp_id": employee.id}
            )
            row = result.fetchone()
            
            if not row:
                return {
                    "error": "No applications found",
                    "success": False
                }
            
            app_id, job_id, status, match_score, applied_at, updated_at, job_title, company_name, location = row
            
            # Handle datetime serialization
            applied_at_str = applied_at.isoformat() if hasattr(applied_at, 'isoformat') else str(applied_at) if applied_at else None
            updated_at_str = updated_at.isoformat() if hasattr(updated_at, 'isoformat') else str(updated_at) if updated_at else None
            
            return {
                "application_id": app_id,
                "job_id": job_id,
                "job_title": job_title or "Unknown",
                "company": company_name or "Unknown",
                "location": location or "Unknown",
                "status": status,  # Raw string from database
                "match_score": match_score,
                "applied_at": applied_at_str,
                "updated_at": updated_at_str,
                "message": "This is your most recent application",
                "success": True
            }
        except Exception as e:
            logger.error(f"❌ Error getting latest application: {str(e)}")
            return {
                "error": f"Failed to get latest application: {str(e)}",
                "success": False
            }
    
    def _list_job_applications(self, db: Session, job_id: int) -> dict:
        """List all applications for a job using raw SQL to avoid enum issues."""
        from sqlalchemy import text
        
        try:
            result = db.execute(
                text("""
                    SELECT a.id, a.employee_id, a.status, a.match_score, a.applied_at, a.updated_at,
                           emp.full_name, u.email
                    FROM applications a
                    LEFT JOIN employees emp ON a.employee_id = emp.id
                    LEFT JOIN users u ON emp.user_id = u.id
                    WHERE a.job_id = :job_id
                    ORDER BY a.match_score DESC
                """),
                {"job_id": job_id}
            )
            rows = result.fetchall()
            
            results = []
            for app_id, employee_id, status, match_score, applied_at, updated_at, full_name, email in rows:
                applied_at_str = applied_at.isoformat() if hasattr(applied_at, 'isoformat') else str(applied_at) if applied_at else None
                updated_at_str = updated_at.isoformat() if hasattr(updated_at, 'isoformat') else str(updated_at) if updated_at else None
                
                results.append({
                    "application_id": app_id,
                    "employee_id": employee_id,
                    "employee_name": full_name or "Unknown",
                    "employee_email": email or "Unknown",
                    "status": status,  # Raw string from database
                    "match_score": match_score,
                    "applied_at": applied_at_str,
                    "updated_at": updated_at_str
                })
            
            return {
                "job_id": job_id,
                "total_applications": len(results),
                "applications": results,
                "success": True
            }
        except Exception as e:
            logger.error(f"❌ Error listing job applications: {str(e)}")
            return {
                "error": f"Failed to list job applications: {str(e)}",
                "success": False
            }
    
    def _run(
        self,
        action: str,
        application_id: int = 0,
        user_id: int = 0,
        job_id: int = 0,
        new_status: str = "",
        candidate_name: str = ""
    ) -> str:
        """Execute the requested action."""
        try:
            db: Session = next(get_db())
            
            if action == "get_status":
                if not application_id:
                    return json.dumps({"error": "application_id required", "success": False})
                result = self._get_status(db, application_id)
                
            elif action == "update_status":
                if not application_id or not new_status:
                    return json.dumps({"error": "application_id and new_status required", "success": False})
                result = self._update_status(db, application_id, new_status)
                
            elif action == "list_my_applications":
                if not user_id:
                    return json.dumps({"error": "user_id required", "success": False})
                
                # Try to resolve user_id to employee_id
                # First check if it's already an employee_id (from orchestrator)
                employee = db.query(Employee).filter(Employee.id == user_id).first()
                
                if not employee:
                    # If not found by employee_id, try user_id (from direct API)
                    employee = db.query(Employee).filter(Employee.user_id == user_id).first()
                
                if not employee:
                    return json.dumps({
                        "error": f"No employee profile found for ID {user_id}",
                        "success": False
                    })
                
                result = self._list_my_applications(db, employee.id)
                
            elif action == "get_latest_application":
                if not user_id:
                    return json.dumps({"error": "user_id required", "success": False})
                result = self._get_latest_application(db, user_id)
                
            elif action == "list_job_applications":
                if not job_id:
                    return json.dumps({"error": "job_id required", "success": False})
                result = self._list_job_applications(db, job_id)

            elif action == "find_application_by_candidate":
                if not candidate_name:
                    return json.dumps({"error": "candidate_name required", "success": False})
                result = self._find_application_by_candidate(db, candidate_name)
                
            else:
                return json.dumps({
                    "error": f"Invalid action '{action}'. Valid: get_status, update_status, list_my_applications, get_latest_application, list_job_applications, find_application_by_candidate",
                    "success": False
                })
            
            return json.dumps(result)
            
        except Exception as e:
            logger.error(f"❌ ApplicationStatusTool error: {str(e)}")
            return json.dumps({"error": str(e), "success": False})
    
    async def _arun(
        self,
        action: str,
        application_id: int = 0,
        user_id: int = 0,
        job_id: int = 0,
        new_status: str = "",
        candidate_name: str = ""
    ) -> str:
        """Async implementation."""
        return self._run(action, application_id, user_id, job_id, new_status, candidate_name)
