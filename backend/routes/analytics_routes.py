# backend/routes/analytics_routes.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, cast, String
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
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get role-specific dashboard analytics."""
    try:
        user_id = current_user.get("user_id")
        role = current_user.get("role")
        
        logger.info(f"Dashboard request from user_id={user_id}, role={role}")
        
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            logger.error(f"User not found: user_id={user_id}")
            raise HTTPException(status_code=404, detail="User not found")
        
        if role == "employer" or user.role == UserRole.EMPLOYER:
            logger.info(f"Getting employer analytics for user {user_id}")
            return await get_employer_analytics(user, db)
        elif role == "employee" or user.role == UserRole.EMPLOYEE:
            logger.info(f"Getting employee analytics for user {user_id}")
            return await get_employee_analytics(user, db)
        else:
            logger.error(f"Invalid role: {role}")
            raise HTTPException(status_code=400, detail="Invalid user role")
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        logger.error(f"Analytics error: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

async def get_employer_analytics(user: User, db: Session):
    """Get analytics for employer dashboard."""
    from sqlalchemy import text
    
    employer = db.query(Employer).filter(Employer.user_id == user.id).first()
    if not employer:
        raise HTTPException(status_code=404, detail="Employer profile not found")
    
    # Total jobs (all jobs, not just active)
    total_jobs = db.query(Job).filter(Job.employer_id == employer.id).count()
    
    # Active jobs count
    active_jobs = db.query(Job).filter(
        Job.employer_id == employer.id,
        Job.is_active == True
    ).count()
    
    # Total applications
    total_applications = db.query(Application).join(Job).filter(
        Job.employer_id == employer.id
    ).count()
    
    # Total hires - count applications with 'hired' or 'OFFER_SENT' status using raw SQL
    hires_query = text("""
        SELECT COUNT(a.id)
        FROM applications a
        JOIN jobs j ON a.job_id = j.id
        WHERE j.employer_id = :employer_id
        AND (a.status = 'hired' OR a.status = 'OFFER_SENT')
    """)
    total_hires = db.execute(hires_query, {"employer_id": employer.id}).scalar() or 0
    
    # Applications by status - use raw SQL to avoid enum conversion issues
    applications_by_status = db.query(
        cast(Application.status, String).label('status'),
        func.count(Application.id).label('count')
    ).join(Job).filter(
        Job.employer_id == employer.id
    ).group_by(cast(Application.status, String)).all()
    
    status_breakdown = {status: count for status, count in applications_by_status}
    
    # Interviews scheduled (upcoming interviews)
    interviews_scheduled = db.query(Interview).join(Application).join(Job).filter(
        Job.employer_id == employer.id,
        Interview.scheduled_at >= datetime.now(),
        Interview.status == InterviewStatus.SCHEDULED
    ).count()
    
    # Average time to hire (in days) - calculate from applied_at to hire date
    avg_time_query = text("""
        SELECT AVG(JULIANDAY(o.responded_at) - JULIANDAY(a.applied_at)) as avg_days
        FROM applications a
        JOIN jobs j ON a.job_id = j.id
        JOIN offers o ON o.application_id = a.id
        WHERE j.employer_id = :employer_id
        AND o.status = 'accepted'
        AND a.applied_at IS NOT NULL
        AND o.responded_at IS NOT NULL
    """)
    avg_time_result = db.execute(avg_time_query, {"employer_id": employer.id}).scalar()
    avg_time_to_hire = int(avg_time_result) if avg_time_result else 0
    
    # Recent applications (last 7 days)
    week_ago = datetime.now() - timedelta(days=7)
    recent_applications = db.query(Application).join(Job).filter(
        Job.employer_id == employer.id,
        Application.applied_at >= week_ago
    ).count()
    
    return {
        "role": "employer",
        "total_jobs": total_jobs,
        "active_jobs": active_jobs,
        "total_applications": total_applications,
        "hires_made": total_hires,
        "interviews_scheduled": interviews_scheduled,
        "avg_time_to_hire": avg_time_to_hire,
        "applications_by_status": status_breakdown,
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
    
    # Applications by status - use raw SQL to avoid enum conversion issues
    applications_by_status = db.query(
        cast(Application.status, String).label('status'),
        func.count(Application.id).label('count')
    ).filter(
        Application.employee_id == employee.id
    ).group_by(cast(Application.status, String)).all()
    
    status_breakdown = {status: count for status, count in applications_by_status}
    
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
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get performance metrics for a specific job."""
    user_id = current_user.get("user_id")
    
    # Verify job belongs to employer
    job = db.query(Job).join(Employer).filter(
        Job.id == job_id,
        Employer.user_id == user_id
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
