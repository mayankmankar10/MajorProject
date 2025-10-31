# backend/routes/analytics_routes.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.db.sql_db import get_db
from backend.db.models import (
    User, Job, Application, Interview, Employee, Employer,
    ApplicationStatus, InterviewStatus, UserRole
)
from backend.utils.auth import get_current_user
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/api/analytics/dashboard")
async def get_dashboard_analytics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get role-specific dashboard analytics."""
    try:
        if current_user.role == UserRole.EMPLOYER:
            return await get_employer_analytics(current_user, db)
        elif current_user.role == UserRole.EMPLOYEE:
            return await get_employee_analytics(current_user, db)
        else:
            raise HTTPException(status_code=400, detail="Invalid user role")
    except Exception as e:
        logger.error(f"Analytics error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def get_employer_analytics(user: User, db: Session):
    """Get analytics for employer dashboard."""
    employer = db.query(Employer).filter(Employer.user_id == user.id).first()
    if not employer:
        raise HTTPException(status_code=404, detail="Employer profile not found")
    
    # Active jobs count
    active_jobs = db.query(Job).filter(
        Job.employer_id == employer.id,
        Job.is_active == True
    ).count()
    
    # Total applications
    total_applications = db.query(Application).join(Job).filter(
        Job.employer_id == employer.id
    ).count()
    
    # Applications by status
    applications_by_status = db.query(
        Application.status,
        func.count(Application.id)
    ).join(Job).filter(
        Job.employer_id == employer.id
    ).group_by(Application.status).all()
    
    status_breakdown = {status.value: count for status, count in applications_by_status}
    
    # Upcoming interviews
    upcoming_interviews = db.query(Interview).join(Application).join(Job).filter(
        Job.employer_id == employer.id,
        Interview.scheduled_at >= datetime.now(),
        Interview.status == InterviewStatus.SCHEDULED
    ).count()
    
    # Recent applications (last 7 days)
    week_ago = datetime.now() - timedelta(days=7)
    recent_applications = db.query(Application).join(Job).filter(
        Job.employer_id == employer.id,
        Application.applied_at >= week_ago
    ).count()
    
    return {
        "role": "employer",
        "active_jobs": active_jobs,
        "total_applications": total_applications,
        "applications_by_status": status_breakdown,
        "upcoming_interviews": upcoming_interviews,
        "recent_applications_7d": recent_applications,
        "company_name": employer.company_name
    }

async def get_employee_analytics(user: User, db: Session):
    """Get analytics for employee dashboard."""
    employee = db.query(Employee).filter(Employee.user_id == user.id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee profile not found")
    
    # Total applications
    total_applications = db.query(Application).filter(
        Application.employee_id == employee.id
    ).count()
    
    # Applications by status
    applications_by_status = db.query(
        Application.status,
        func.count(Application.id)
    ).filter(
        Application.employee_id == employee.id
    ).group_by(Application.status).all()
    
    status_breakdown = {status.value: count for status, count in applications_by_status}
    
    # Upcoming interviews
    upcoming_interviews = db.query(Interview).join(Application).filter(
        Application.employee_id == employee.id,
        Interview.scheduled_at >= datetime.now(),
        Interview.status.in_([InterviewStatus.SCHEDULED, InterviewStatus.CONFIRMED])
    ).count()
    
    # Active jobs available
    active_jobs = db.query(Job).filter(Job.is_active == True).count()
    
    # Average match score
    avg_match_score = db.query(func.avg(Application.match_score)).filter(
        Application.employee_id == employee.id,
        Application.match_score.isnot(None)
    ).scalar() or 0.0
    
    return {
        "role": "employee",
        "total_applications": total_applications,
        "applications_by_status": status_breakdown,
        "upcoming_interviews": upcoming_interviews,
        "active_jobs_available": active_jobs,
        "average_match_score": round(avg_match_score, 2),
        "profile_completeness": calculate_profile_completeness(employee)
    }

def calculate_profile_completeness(employee: Employee) -> int:
    """Calculate profile completeness percentage."""
    fields = [
        employee.full_name,
        employee.phone,
        employee.resume_text,
        employee.skills,
        employee.experience_years,
        employee.education,
        employee.preferred_location
    ]
    completed = sum(1 for field in fields if field)
    return int((completed / len(fields)) * 100)

@router.get("/api/analytics/jobs/performance/{job_id}")
async def get_job_performance(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get performance metrics for a specific job."""
    # Verify job belongs to employer
    job = db.query(Job).join(Employer).filter(
        Job.id == job_id,
        Employer.user_id == current_user.id
    ).first()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Get metrics
    total_applications = db.query(Application).filter(Application.job_id == job_id).count()
    avg_match_score = db.query(func.avg(Application.match_score)).filter(
        Application.job_id == job_id
    ).scalar() or 0.0
    
    interviews_scheduled = db.query(Interview).join(Application).filter(
        Application.job_id == job_id
    ).count()
    
    return {
        "job_id": job_id,
        "job_title": job.title,
        "total_applications": total_applications,
        "average_match_score": round(avg_match_score, 2),
        "interviews_scheduled": interviews_scheduled,
        "created_at": job.created_at.isoformat()
    }
