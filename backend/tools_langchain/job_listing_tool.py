# backend/tools_langchain/job_listing_tool.py
"""
JobListingTool - Fetch and summarize employer's job postings
Allows employers to query their active and inactive jobs via chat.
"""

from langchain.tools import BaseTool
from typing import Type, Optional
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy.orm import Session
from backend.db.sql_db import SessionLocal
from backend.db.models import Job, Employer
import json
import logging

logger = logging.getLogger(__name__)

class JobListingInput(BaseModel):
    """Input schema for JobListingTool."""
    employer_id: int = Field(description="Employer ID to fetch jobs for")
    status: str = Field(
        default="all",
        description="Filter by status: 'active', 'inactive', or 'all' (default)"
    )
    limit: int = Field(
        default=0,
        description="Maximum number of jobs to return (0 = no limit)"
    )
    
    model_config = ConfigDict(extra='forbid')


class JobListingTool(BaseTool):
    """
    Retrieves and summarizes all job postings for an employer.
    
    Use this when employer asks:
    - "What jobs am I offering?"
    - "List all my job postings"
    - "Show me my active jobs"
    - "Summarize my open positions"
    
    Returns JSON with job details including:
    - Job title, location, category
    - Current applications count
    - Positions filled vs needed
    - Salary range
    - Status (active/inactive)
    """
    
    name: str = "JobListingTool"
    description: str = """
    Fetches all job postings for a specific employer.
    
    Parameters:
    - employer_id (int): The employer ID
    - status (string): Filter - 'active', 'inactive', or 'all' (default: all)
    - limit (int): Max jobs to return (default: 0 = all jobs)
    
    Returns: JSON with list of jobs and summary statistics
    
    Example: "Show me all my active job postings"
    """
    args_schema: Type[BaseModel] = JobListingInput
    
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    def __init__(self):
        super().__init__()
    
    def _run(
        self,
        employer_id: int,
        status: str = "all",
        limit: int = 0
    ) -> str:
        """Fetch and summarize employer's job postings."""
        db = SessionLocal()
        
        try:
            # Verify employer exists
            employer = db.query(Employer).filter(Employer.id == employer_id).first()
            if not employer:
                return json.dumps({
                    "success": False,
                    "error": f"Employer ID {employer_id} not found"
                })
            
            # Build query
            query = db.query(Job).filter(Job.employer_id == employer_id)
            
            # Apply status filter
            if status.lower() == "active":
                query = query.filter(Job.is_active == True)
            elif status.lower() == "inactive":
                query = query.filter(Job.is_active == False)
            # else: "all" - no filter
            
            # Apply limit
            if limit > 0:
                query = query.limit(limit)
            
            # Order by most recent first
            query = query.order_by(Job.created_at.desc())
            
            jobs = query.all()
            
            if not jobs:
                return json.dumps({
                    "success": True,
                    "total_jobs": 0,
                    "message": f"No {status} jobs found for this employer",
                    "jobs": []
                })
            
            # Format job details
            jobs_list = []
            total_applications = 0
            total_positions_needed = 0
            total_positions_filled = 0
            
            for job in jobs:
                # Count applications for this job using raw SQL to avoid enum validation issues
                from sqlalchemy import text
                applications_count = db.execute(
                    text(f"SELECT COUNT(*) FROM applications WHERE job_id = {job.id}")
                ).scalar() or 0
                total_applications += applications_count
                
                # Track positions
                total_positions_needed += job.quantity_needed or 1
                total_positions_filled += job.quantity_filled or 0
                
                job_data = {
                    "job_id": job.id,
                    "title": job.title,
                    "location": job.location,
                    "job_category": job.job_category.value if job.job_category else "Other",
                    "job_type": job.job_type,
                    "salary_range": job.salary_range or "Competitive",
                    "applications_count": applications_count,
                    "positions_needed": job.quantity_needed or 1,
                    "positions_filled": job.quantity_filled or 0,
                    "status": "Active" if job.is_active else "Inactive",
                    "shift_type": job.shift_type or "Flexible",
                    "cuisine_type": job.cuisine_type,
                    "requires_food_safety": job.requires_food_safety,
                    "requires_alcohol_cert": job.requires_alcohol_cert,
                    "min_experience": job.min_hospitality_experience or 0,
                    "posted_date": job.created_at.strftime("%Y-%m-%d") if job.created_at else None,
                    "description_preview": job.description[:150] + "..." if len(job.description) > 150 else job.description
                }
                jobs_list.append(job_data)
            
            # Summary statistics
            summary = {
                "total_jobs": len(jobs),
                "active_jobs": sum(1 for j in jobs if j.is_active),
                "inactive_jobs": sum(1 for j in jobs if not j.is_active),
                "total_applications": total_applications,
                "total_positions_needed": total_positions_needed,
                "total_positions_filled": total_positions_filled,
                "unfilled_positions": total_positions_needed - total_positions_filled,
                "company_name": employer.company_name
            }
            
            result = {
                "success": True,
                "summary": summary,
                "jobs": jobs_list
            }
            
            logger.info(f"✅ Retrieved {len(jobs)} jobs for employer {employer_id} ({employer.company_name})")
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            logger.error(f"❌ Error fetching jobs for employer {employer_id}: {str(e)}")
            return json.dumps({
                "success": False,
                "error": str(e)
            })
        finally:
            db.close()
    
    async def _arun(
        self,
        employer_id: int,
        status: str = "all",
        limit: int = 0
    ) -> str:
        """Async implementation."""
        return self._run(employer_id, status, limit)
