# backend/tools_langchain/job_finder_tool.py
from langchain.tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from backend.db.sql_db import get_db
from backend.db.models import Job
import json
import logging

logger = logging.getLogger(__name__)

class JobFinderToolInput(BaseModel):
    """Input schema for JobFinderTool."""
    search_query: str = Field(description="Natural language job search query (e.g., 'Python developer remote')")
    location: str = Field(default="", description="Optional location filter")
    job_type: str = Field(default="", description="Optional job type (full_time, part_time, contract)")
    limit: int = Field(default=10, description="Number of jobs to return")

class JobFinderTool(BaseTool):
    """
    Searches for jobs based on natural language queries.
    """
    name: str = "JobFinderTool"
    description: str = """
    Searches for jobs using natural language queries with optional filters.
    
    Input:
    - search_query (string): Job search query (e.g., "Python developer", "marketing manager")
    - location (string, optional): Location filter
    - job_type (string, optional): Job type filter
    - limit (int, optional): Number of results (default 10)
    
    Output: JSON array of matching jobs with details
    
    Use this when a candidate is searching for jobs.
    """
    args_schema: Type[BaseModel] = JobFinderToolInput
    
    def _run(
        self,
        search_query: str,
        location: str = "",
        job_type: str = "",
        limit: int = 10
    ) -> str:
        """Search for jobs."""
        try:
            db: Session = next(get_db())
            
            # Build query
            query = db.query(Job).filter(Job.is_active == True)
            
            # Apply filters
            if location:
                query = query.filter(Job.location.ilike(f"%{location}%"))
            
            if job_type:
                query = query.filter(Job.job_type == job_type)
            
            # Search in title and description
            if search_query:
                search_filter = (
                    Job.title.ilike(f"%{search_query}%") |
                    Job.description.ilike(f"%{search_query}%")
                )
                query = query.filter(search_filter)
            
            # Execute query
            jobs = query.limit(limit).all()
            
            # Format results
            results = []
            for job in jobs:
                results.append({
                    "job_id": job.id,
                    "title": job.title,
                    "company": job.employer.company_name if job.employer else "Unknown",
                    "location": job.location,
                    "job_type": job.job_type,
                    "salary_range": job.salary_range,
                    "description": job.description[:200] + "..." if len(job.description) > 200 else job.description,
                    "posted_date": job.created_at.isoformat()
                })
            
            result = {
                "jobs": results,
                "total": len(results),
                "query": search_query,
                "success": True
            }
            
            logger.info(f"✅ Found {len(results)} jobs for query: '{search_query}'")
            return json.dumps(result)
            
        except Exception as e:
            logger.error(f"❌ Job search error: {str(e)}")
            return json.dumps({"error": str(e), "jobs": [], "success": False})
    
    async def _arun(
        self,
        search_query: str,
        location: str = "",
        job_type: str = "",
        limit: int = 10
    ) -> str:
        """Async implementation."""
        return self._run(search_query, location, job_type, limit)
