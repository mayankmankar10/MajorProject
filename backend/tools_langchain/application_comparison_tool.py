# backend/tools_langchain/application_comparison_tool.py
from langchain.tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import desc
from backend.db.sql_db import get_db
from backend.db.models import Application, Job, Employee, Employer, ApplicationStatus
import json
import logging

logger = logging.getLogger(__name__)

class ApplicationComparisonInput(BaseModel):
    """Input schema for ApplicationComparisonTool."""
    user_id: int = Field(description="ID of the employer user")
    limit: int = Field(default=2, description="Number of recent applications to compare (default: 2)")
    job_id: int = Field(default=0, description="Optional: Filter by specific job ID")
    status: str = Field(default="reviewing", description="Filter by status (default: reviewing)")

class ApplicationComparisonTool(BaseTool):
    """
    Compare recently reviewed applications for employers.
    
    Helps employers make hiring decisions by comparing candidates side-by-side.
    Shows detailed comparison of qualifications, experience, skills, and recommendations.
    """
    
    name: str = "ApplicationComparisonTool"
    description: str = """
    Compare recent job applications to help with hiring decisions.
    
    Use this when an employer asks to compare candidates or applications.
    
    Input:
    - user_id: ID of the employer user
    - limit: How many applications to compare (default: 2)
    - job_id: Optional, filter by specific job
    - status: Filter by application status (default: reviewing)
    
    Returns side-by-side comparison of candidates with recommendations.
    """
    args_schema: Type[BaseModel] = ApplicationComparisonInput
    
    def _run(self, user_id: int, limit: int = 2, job_id: int = 0, status: str = "reviewing") -> str:
        """Compare recent applications."""
        try:
            db: Session = next(get_db())
            
            # Look up employer profile from user_id
            employer = db.query(Employer).filter(Employer.user_id == user_id).first()
            if not employer:
                return json.dumps({
                    "success": False,
                    "error": f"No employer profile found for user #{user_id}"
                })
            
            # Build query for applications
            query = db.query(Application).join(Job).filter(
                Job.employer_id == employer.id,  # Use employer.id from looked up profile
                Application.reviewed_at.isnot(None)  # Only show actually reviewed applications
            )
            
            # Filter by status if specified
            if status:
                try:
                    query = query.filter(Application.status == ApplicationStatus[status.upper()])
                except KeyError:
                    pass  # Invalid status, skip filter
            
            # Filter by job if specified
            if job_id > 0:
                query = query.filter(Application.job_id == job_id)
            
            # Get most recent applications
            applications = query.order_by(desc(Application.reviewed_at)).limit(limit).all()
            
            if not applications:
                return json.dumps({
                    "success": False,
                    "error": f"No {status} applications found for this employer"
                })
            
            # Build comparison data
            comparison = {
                "success": True,
                "total_compared": len(applications),
                "status_filter": status,
                "candidates": []
            }
            
            for app in applications:
                employee = db.query(Employee).filter(Employee.id == app.employee_id).first()
                job = db.query(Job).filter(Job.id == app.job_id).first()
                
                if not employee or not job:
                    continue
                
                candidate_data = {
                    "application_id": app.id,
                    "name": employee.full_name,
                    "job_title": job.title,
                    "match_score": round(app.match_score * 100) if app.match_score else 0,
                    "status": app.status.value if hasattr(app.status, 'value') else str(app.status),
                    "applied_at": app.applied_at.isoformat() if app.applied_at else None,
                    "reviewed_at": app.reviewed_at.isoformat() if app.reviewed_at else None,
                    
                    # Candidate details
                    "experience": {
                        "total_years": employee.experience_years or 0,
                        "hospitality_years": employee.years_in_hospitality or 0
                    },
                    "skills": {
                        "technical": employee.skills or [],
                        "soft": employee.soft_skills or []
                    },
                    "certifications": employee.certifications or [],
                    "preferred_role": employee.preferred_role.value if employee.preferred_role else None,
                    "preferred_shift": employee.preferred_shift,
                    "salary_expectation": f"₹{employee.expected_salary_min:,} - ₹{employee.expected_salary_max:,}" if employee.expected_salary_min and employee.expected_salary_max else "Not specified",
                    
                    # Job fit
                    "food_safety_certified": employee.food_safety_certified,
                    "servsafe_certified": employee.servsafe_certified,
                    "location": employee.preferred_location,
                    "phone": employee.phone,
                    
                    # Application specifics
                    "cover_letter": app.cover_letter,
                    "notes": app.notes,
                    "profile_summary": employee.profile_summary
                }
                
                comparison["candidates"].append(candidate_data)
            
            # Add comparison insights
            if len(comparison["candidates"]) >= 2:
                comparison["comparison_insights"] = self._generate_insights(comparison["candidates"])
            
            return json.dumps(comparison, indent=2)
            
        except Exception as e:
            logger.error(f"Error comparing applications: {str(e)}")
            return json.dumps({
                "success": False,
                "error": f"Failed to compare applications: {str(e)}"
            })
    
    def _generate_insights(self, candidates):
        """Generate comparison insights."""
        insights = {
            "highest_match": max(candidates, key=lambda c: c["match_score"])["name"],
            "most_experienced": max(candidates, key=lambda c: c["experience"]["hospitality_years"])["name"],
            "most_certified": max(candidates, key=lambda c: len(c["certifications"]))["name"]
        }
        
        # Check who has more skills
        skill_counts = [(c["name"], len(c["skills"]["technical"]) + len(c["skills"]["soft"])) for c in candidates]
        insights["most_skilled"] = max(skill_counts, key=lambda x: x[1])[0]
        
        return insights
    
    async def _arun(self, user_id: int, limit: int = 2, job_id: int = 0, status: str = "reviewing") -> str:
        """Async implementation."""
        return self._run(user_id, limit, job_id, status)
