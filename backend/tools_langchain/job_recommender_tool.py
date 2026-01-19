# backend/tools_langchain/job_recommender_tool.py
from langchain.tools import BaseTool
from typing import Type, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from backend.db.sql_db import get_db
from backend.db.models import Employee, Job, Application, Employer
import json
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class JobRecommenderInput(BaseModel):
    """Input schema for JobRecommenderTool."""
    employee_id: int = Field(description="Employee ID to get recommendations for")
    limit: int = Field(default=10, description="Maximum number of recommendations to return")

class JobRecommenderTool(BaseTool):
    """
    Recommends personalized jobs for an employee based on:
    - Skills match
    - Experience level
    - Role preferences  
    - Salary expectations
    - Location preferences
    - Excludes already-applied jobs
    """
    name: str = "JobRecommenderTool"
    description: str = """
    Get personalized job recommendations for an employee.
    
    Input:
    - employee_id (int): Employee ID
    - limit (int, optional): Max recommendations (default: 10)
    
    Output: JSON list of recommended jobs with match scores
    
    Rankings based on:
    - Skills match (40%)
    - Experience fit (20%)
    - Role match (20%)
    - Salary fit (10%)
    - Location fit (10%)
    """
    args_schema: Type[BaseModel] = JobRecommenderInput
    
    llm: Any = Field(default=None, exclude=True)
    
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    def calculate_match_score(
        self, 
        employee: Employee, 
        job: Job
    ) -> Dict[str, float]:
        """Calculate detailed match score breakdown"""
        scores = {
            "skills": 0.0,
            "experience": 0.0,
            "role": 0.0,
            "salary": 0.0,
            "location": 0.0
        }
        
        # 1. Skills match (40% weight)
        if employee.skills and job.description:
            employee_skills = [s.lower().strip() for s in employee.skills] if isinstance(employee.skills, list) else []
            job_desc = job.description.lower()
            
            if employee_skills:
                skill_matches = sum(1 for skill in employee_skills if skill in job_desc)
                scores["skills"] = (skill_matches / len(employee_skills)) * 0.40
        
        # 2. Experience match (20% weight)
        if employee.experience_years is not None and job.min_hospitality_experience is not None:
            if employee.experience_years >= job.min_hospitality_experience:
                # Perfect match or overqualified
                excess_years = employee.experience_years - job.min_hospitality_experience
                if excess_years <= 2:
                    scores["experience"] = 0.20  # Perfect match
                else:
                    scores["experience"] = 0.15  # Slight penalty for overqualification
            else:
                # Under-qualified
                deficit = job.min_hospitality_experience - employee.experience_years
                scores["experience"] = max(0, 0.20 - (deficit * 0.05))
        else:
            scores["experience"] = 0.10  # Neutral if no data
        
        # 3. Role match (20% weight)
        if employee.preferred_role and job.job_category:
            try:
                if employee.preferred_role.value == job.job_category.value:
                    scores["role"] = 0.20
                else:
                    scores["role"] = 0.05  # Small score for different but related roles
            except:
                scores["role"] = 0.05
        
        # 4. Salary match (10% weight)
        if employee.expected_salary_min and employee.expected_salary_max and job.salary_range:
            # Parse salary range (format: "₹60,000 - ₹90,000")
            try:
                parts = job.salary_range.replace("₹", "").replace(",", "").split("-")
                if len(parts) == 2:
                    job_min = int(parts[0].strip())
                    job_max = int(parts[1].strip())
                    
                    # Check if there's overlap
                    if (employee.expected_salary_min <= job_max and 
                        employee.expected_salary_max >= job_min):
                        scores["salary"] = 0.10
                    else:
                        scores["salary"] = 0.02
            except:
                scores["salary"] = 0.05
        else:
            scores["salary"] = 0.05
        
        # 5. Location match (10% weight)
        if employee.preferred_location and job.location:
            emp_loc = employee.preferred_location.lower().strip()
            job_loc = job.location.lower().strip()
            
            if emp_loc in job_loc or job_loc in emp_loc:
                scores["location"] = 0.10
            else:
                scores["location"] = 0.02
        else:
            scores["location"] = 0.05
        
        return scores
    
    def _run(
        self,
        employee_id: int,
        limit: int = 10
    ) -> str:
        """Get job recommendations"""
        try:
            db: Session = next(get_db())
            
            # 1. Get employee
            employee = db.query(Employee).filter(Employee.id == employee_id).first()
            if not employee:
                return json.dumps({"error": "Employee not found", "recommendations": []})
            
            # 2. Get jobs employee has already applied to
            applied_job_ids = [
                app.job_id for app in 
                db.query(Application).filter(Application.employee_id == employee_id).all()
            ]
            
            # 3. Get active jobs (excluding already applied)
            query = db.query(Job).filter(
                Job.is_active == True
            )
            
            if applied_job_ids:
                query = query.filter(~Job.id.in_(applied_job_ids))
            
            jobs = query.all()
            
            if not jobs:
                return json.dumps({
                    "employee_id": employee_id,
                    "recommendations": [],
                    "message": "No new jobs available"
                })
            
            # 4. Calculate scores for all jobs
            scored_jobs = []
            for job in jobs:
                score_breakdown = self.calculate_match_score(employee, job)
                total_score = sum(score_breakdown.values())
                
                # Get employer info
                employer = db.query(Employer).filter(Employer.id == job.employer_id).first()
                
                scored_jobs.append({
                    "job_id": job.id,
                    "title": job.title,
                    "company": employer.company_name if employer else "Unknown",
                    "location": job.location,
                    "salary_range": job.salary_range,
                    "job_type": job.job_type,
                    "job_category": job.job_category.value if job.job_category else None,
                    "match_score": round(total_score, 2),
                    "score_breakdown": {k: round(v, 2) for k, v in score_breakdown.items()},
                    "created_at": job.created_at.isoformat() if job.created_at else None,
                    "description_preview": job.description[:150] + "..." if job.description and len(job.description) > 150 else job.description
                })
            
            # 5. Sort by match score (descending)
            scored_jobs.sort(key=lambda x: x["match_score"], reverse=True)
            
            # 6. Return top N recommendations
            recommendations = scored_jobs[:limit]
            
            logger.info(f"Generated {len(recommendations)} job recommendations for employee {employee_id}")
            
            return json.dumps({
                "employee_id": employee_id,
                "total_available_jobs": len(jobs),
                "recommendations": recommendations,
                "already_applied_count": len(applied_job_ids)
            })
            
        except Exception as e:
            logger.error(f"Job recommendation error: {str(e)}")
            return json.dumps({"error": str(e), "recommendations": []})
