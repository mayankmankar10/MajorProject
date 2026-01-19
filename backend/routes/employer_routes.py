# backend/routes/employer_routes.py
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from backend.db.sql_db import SessionLocal
from backend.db.models import Employer, Job, Application, Interview, Employee, Offer
from backend.utils.auth import get_current_user
import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class EmployerCreate(BaseModel):
    name: str
    email: str
    profile: str = ""


class JobCreate(BaseModel):
    employer_id: int
    title: str
    description: str
    location: str | None = None
    skills: list | None = None


class JobCreateRequest(BaseModel):
    """Request schema for creating a new job posting from the UI form."""
    title: str
    skills: list[str]
    location: str
    job_type: str  # full_time, part_time, contract
    salary_min: int
    salary_max: int
    shift_type: str  # morning, afternoon, evening, night
    min_hospitality_experience: int
    job_category: str  # waiter, cook, chef, etc.
    cuisine_type: str | None = None  # Only for cook/chef
    quantity_needed: int = 1


class FindPayload(BaseModel):
    job_id: int | None = None
    job_text: str | None = None
    k: int = 5


class SchedulePayload(BaseModel):
    application_id: int
    scheduled_at: str
    location: str | None = None


@router.post("/register")
def register_employer(payload: EmployerCreate, db: Session = Depends(get_db)):
    """Register a new employer - placeholder for direct agent call."""
    # Note: This is a simplified version. Full registration should go through /api/auth/register
    try:
        employer = Employer(
            company_name=payload.name,
            company_profile=payload.profile
        )
        db.add(employer)
        db.commit()
        db.refresh(employer)
        return {"id": employer.id, "name": employer.company_name, "status": "registered"}
    except Exception as e:
        db.rollback()
        logger.error(f"Employer registration error: {e}")
        raise HTTPException(status_code=500, detail="Registration failed")


@router.post("/post_job")
def post_job(payload: JobCreate, db: Session = Depends(get_db)):
    """Post a new job listing."""
    try:
        job = Job(
            employer_id=payload.employer_id,
            title=payload.title,
            description=payload.description,
            location=payload.location,
            skills_required=payload.skills or [],
            status="active"
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        return {"id": job.id, "title": job.title, "status": "posted"}
    except Exception as e:
        db.rollback()
        logger.error(f"Job posting error: {e}")
        raise HTTPException(status_code=500, detail="Job posting failed")


@router.post("/find_candidates")
def find_candidates(payload: FindPayload, db: Session = Depends(get_db)):
    """Find matching candidates for a job."""
    text = payload.job_text
    if not text and payload.job_id:
        job = db.query(Job).filter(Job.id == payload.job_id).first()
        if job:
            text = job.title + "\n\n" + job.description
    if not text:
        raise HTTPException(status_code=400, detail="provide job_text or job_id")
    
    # Simple candidate retrieval - returns employees who have applied to similar jobs
    # For full semantic matching, use the MatchingTool through the chat interface
    try:
        employees = db.query(Employee).limit(payload.k).all()
        return {
            "candidates": [
                {
                    "id": emp.id,
                    "name": emp.full_name,
                    "skills": emp.skills,
                    "experience_years": emp.experience_years
                }
                for emp in employees
            ],
            "note": "For AI-powered semantic matching, use the chat assistant"
        }
    except Exception as e:
        logger.error(f"Find candidates error: {e}")
        raise HTTPException(status_code=500, detail="Failed to find candidates")


@router.post("/schedule_interview")
def schedule_interview(payload: SchedulePayload, db: Session = Depends(get_db)):
    """Schedule an interview for an application."""
    try:
        application = db.query(Application).filter(Application.id == payload.application_id).first()
        if not application:
            raise HTTPException(status_code=404, detail="Application not found")
        
        scheduled_at = datetime.datetime.fromisoformat(payload.scheduled_at)
        
        interview = Interview(
            application_id=payload.application_id,
            scheduled_at=scheduled_at,
            location=payload.location,
            status="scheduled"
        )
        db.add(interview)
        db.commit()
        db.refresh(interview)
        
        return {"id": interview.id, "scheduled_at": str(scheduled_at), "status": "scheduled"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Schedule interview error: {e}")
        raise HTTPException(status_code=500, detail="Failed to schedule interview")


@router.post("/confirm_hire")
def confirm_hire(payload: dict, db: Session = Depends(get_db)):
    """Confirm hiring for an application."""
    application_id = payload.get("application_id")
    if not application_id:
        raise HTTPException(status_code=400, detail="application_id required")
    
    try:
        application = db.query(Application).filter(Application.id == application_id).first()
        if not application:
            raise HTTPException(status_code=404, detail="Application not found")
        
        # Use raw SQL to update to avoid enum validation issues
        db.execute(
            "UPDATE applications SET status = 'hired' WHERE id = :id",
            {"id": application_id}
        )
        db.commit()
        
        return {"application_id": application_id, "status": "hired"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Confirm hire error: {e}")
        raise HTTPException(status_code=500, detail="Failed to confirm hire")


@router.post("/jobs")
async def create_job_posting(
    payload: JobCreateRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new job posting from the employer UI form.
    Auto-fills employer_id, generates AI descriptions, and sets defaults.
    """
    try:
        user_id = current_user.get("user_id")
        if not user_id:
            raise HTTPException(status_code=400, detail="user_id required")
        
        # Get employer from user_id
        employer = db.query(Employer).filter(Employer.user_id == user_id).first()
        if not employer:
            raise HTTPException(status_code=404, detail="Employer profile not found")
        
        # Create professional description using template
        # Build cuisine part if applicable
        cuisine_part = ""
        if payload.cuisine_type:
            cuisine_part = f", specializing in the rich and diverse flavors of {payload.cuisine_type.title()} cuisine"
        
        # Build shift part
        shift_part = f"{payload.shift_type.title()} shift"
        
        # Create the description using the template format
        description = f"Seeking a skilled and experienced {payload.title} to join our team in the {payload.job_category} category{cuisine_part}. This position offers {shift_part} availability. The ideal candidate will demonstrate expertise in {', '.join(payload.skills)}, contributing to an exceptional guest experience and maintaining the highest standards of hospitality service."
        
        # Format salary range for display
        salary_range = f"Rs. {payload.salary_min:,} - {payload.salary_max:,}"
        
        # Create requirements JSON
        requirements = {
            "skills": payload.skills,
            "experience": payload.min_hospitality_experience,
            "required_skills": payload.skills,
            "soft_skills": []
        }
        
        # Map job category string to enum
        from backend.db.models import JobCategory
        job_category_map = {
            "waiter": JobCategory.WAITER,
            "cook": JobCategory.COOK,
            "chef": JobCategory.CHEF,
            "bartender": JobCategory.BARTENDER,
            "host": JobCategory.HOST,
            "dishwasher": JobCategory.DISHWASHER,
            "other": JobCategory.OTHER
        }
        job_category_enum = job_category_map.get(payload.job_category.lower(), JobCategory.OTHER)
        
        # Create the job
        new_job = Job(
            employer_id=employer.id,
            title=payload.title,
            description=description,  # Professional template description
            enhanced_description=description,  # Same description for consistency
            requirements=requirements,
            location=payload.location,
            job_type=payload.job_type,
            salary_range=salary_range,
            shift_type=payload.shift_type,
            min_hospitality_experience=payload.min_hospitality_experience,
            job_category=job_category_enum,
            cuisine_type=payload.cuisine_type if payload.cuisine_type else None,
            quantity_needed=payload.quantity_needed,
            quantity_filled=0,
            match_score_threshold=0.5,  # Set to 0.5 as specified
            is_active=True,
            auto_fill_on_decline=False
        )
        
        db.add(new_job)
        db.commit()
        db.refresh(new_job)
        
        logger.info(f"Job created successfully: job_id={new_job.id}, employer_id={employer.id}, title={new_job.title}")
        
        return {
            "success": True,
            "job_id": new_job.id,
            "message": "Job posted successfully",
            "job": {
                "id": new_job.id,
                "title": new_job.title,
                "description": new_job.description,
                "location": new_job.location,
                "job_category": new_job.job_category.value if new_job.job_category else None,
                "salary_range": new_job.salary_range,
                "quantity_needed": new_job.quantity_needed,
                "is_active": new_job.is_active
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating job posting: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to create job posting: {str(e)}")


@router.get("/jobs")
def get_employer_jobs(user_id: int = None, db: Session = Depends(get_db)):
    """Get all jobs posted by an employer."""
    try:
        # user_id is required to filter by employer
        if not user_id:
            return []  # Return empty if no user specified (don't show all jobs)
        
        # Get employer from user_id
        employer = db.query(Employer).filter(Employer.user_id == user_id).first()
        if not employer:
            return []  # No employer found for this user
        
        # Get only jobs for this specific employer
        jobs = db.query(Job).filter(Job.employer_id == employer.id).order_by(Job.created_at.desc()).all()
        
        result = []
        for job in jobs:
            # Count applications for this job
            app_count = db.query(Application).filter(Application.job_id == job.id).count()
            
            # Count offers by status (using simple queries instead of case)
            try:
                # Count accepted offers
                offers_accepted = db.query(Offer).join(Application)\
                    .filter(Application.job_id == job.id, Offer.status == 'accepted').count()
                
                # Count pending offers
                offers_pending = db.query(Offer).join(Application)\
                    .filter(Application.job_id == job.id, Offer.status == 'pending').count()
            except Exception as e:
                logger.warning(f"Error calculating offer stats for job {job.id}: {e}")
                offers_accepted = 0
                offers_pending = 0
            
            available_positions = max(0, job.quantity_needed - job.quantity_filled)
            
            result.append({
                "id": job.id,
                "title": job.title,
                "description": job.description,
                "location": job.location,
                "is_active": job.is_active,
                "job_category": job.job_category.value if job.job_category else None,
                "shift_type": job.shift_type,
                "salary_range": job.salary_range,
                "quantity_needed": job.quantity_needed,
                "quantity_filled": job.quantity_filled,
                "offers_accepted": offers_accepted,
                "offers_pending": offers_pending,
                "positions_available": available_positions,
                "application_count": app_count,
                "created_at": job.created_at.isoformat() if job.created_at else None
            })
        
        return result
    except Exception as e:
        logger.error(f"Get employer jobs error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch jobs")


@router.get("/applications")
def get_employer_applications(
    user_id: int = None,
    status: str = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get all applications for jobs posted by an employer using raw SQL to avoid enum issues."""
    from sqlalchemy import text
    
    try:
        # user_id is required to filter by employer
        if not user_id:
            return []  # Return empty if no user specified
        
        # Get employer from user_id
        employer = db.query(Employer).filter(Employer.user_id == user_id).first()
        if not employer:
            return []  # No employer found
        
        # Use raw SQL to avoid enum validation issues
        status_filter = ""
        if status:
            status_filter = "AND a.status = :status"
        
        sql = text(f"""
            SELECT 
                a.id, a.job_id, a.employee_id, a.status, a.match_score,
                a.cover_letter, a.applied_at,
                j.title as job_title,
                e.full_name as employee_name, e.phone as employee_phone,
                u.email as employee_email
            FROM applications a
            JOIN jobs j ON a.job_id = j.id
            JOIN employees e ON a.employee_id = e.id
            LEFT JOIN users u ON e.user_id = u.id
            WHERE j.employer_id = :employer_id
            {status_filter}
            ORDER BY a.applied_at DESC
            LIMIT :limit
        """)
        
        params = {"employer_id": employer.id, "limit": limit}
        if status:
            params["status"] = status
        
        rows = db.execute(sql, params).fetchall()
        
        result = []
        for row in rows:
            result.append({
                "id": row.id,
                "job_id": row.job_id,
                "job_title": row.job_title or "Unknown",
                "employee_id": row.employee_id,
                "employee_name": row.employee_name or "Unknown",
                "employee_email": row.employee_email,
                "employee_phone": row.employee_phone,
                "status": row.status,  # Raw string from DB
                "match_score": row.match_score,
                "cover_letter": row.cover_letter,
                "applied_at": str(row.applied_at) if row.applied_at else None
            })
        
        return result
    except Exception as e:
        logger.error(f"Get employer applications error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch applications")


# ========== EMPLOYER ONBOARDING ENDPOINTS ==========

class EmployerProfileUpdate(BaseModel):
    company_profile: str | None = None
    industry: str | None = None
    location: str | None = None
    website: str | None = None


class HiringPreferenceItem(BaseModel):
    role: str
    positions: int
    location: str
    shift: str
    salary_min: int
    salary_max: int


class HiringPreferencesUpdate(BaseModel):
    preferences: list[HiringPreferenceItem]


@router.get("/onboarding-status")
def get_employer_onboarding_status(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get employer onboarding completion status."""
    try:
        user_id = current_user.get("user_id")
        if not user_id:
            raise HTTPException(status_code=400, detail="user_id required")
        
        employer = db.query(Employer).filter(Employer.user_id == user_id).first()
        if not employer:
            raise HTTPException(status_code=404, detail="Employer profile not found")
        
        # Check completion status for each step
        step1_complete = bool(
            employer.company_profile and 
            employer.industry and 
            employer.location
        )
        
        step2_complete = bool(
            employer.hiring_preferences and 
            len(employer.hiring_preferences) > 0
        )
        
        onboarding_complete = step1_complete and step2_complete
        
        return {
            "onboarding_complete": onboarding_complete,
            "steps": {
                "company_profile": step1_complete,
                "hiring_preferences": step2_complete
            },
            "profile": {
                "company_name": employer.company_name,
                "company_profile": employer.company_profile,
                "industry": employer.industry,
                "location": employer.location,
                "website": employer.website,
                "hiring_preferences": employer.hiring_preferences
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching onboarding status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/profile")
def update_employer_profile(
    profile_data: EmployerProfileUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update employer profile information for onboarding."""
    try:
        user_id = current_user.get("user_id")
        if not user_id:
            raise HTTPException(status_code=400, detail="user_id required")
        
        employer = db.query(Employer).filter(Employer.user_id == user_id).first()
        if not employer:
            raise HTTPException(status_code=404, detail="Employer profile not found")
        
        # Update fields
        if profile_data.company_profile is not None:
            employer.company_profile = profile_data.company_profile
        if profile_data.industry is not None:
            employer.industry = profile_data.industry
        if profile_data.location is not None:
            employer.location = profile_data.location
        if profile_data.website is not None:
            employer.website = profile_data.website
        
        db.commit()
        db.refresh(employer)
        
        logger.info(f"Employer profile updated for employer_id={employer.id}")
        
        return {
            "success": True,
            "message": "Profile updated successfully",
            "profile": {
                "company_name": employer.company_name,
                "company_profile": employer.company_profile,
                "industry": employer.industry,
                "location": employer.location,
                "website": employer.website
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating employer profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/hiring-preferences")
def set_hiring_preferences(
    preferences_data: HiringPreferencesUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Set or update employer's hiring preferences/templates."""
    try:
        user_id = current_user.get("user_id")
        if not user_id:
            raise HTTPException(status_code=400, detail="user_id required")
        
        employer = db.query(Employer).filter(Employer.user_id == user_id).first()
        if not employer:
            raise HTTPException(status_code=404, detail="Employer profile not found")
        
        # Convert Pydantic models to dict
        preferences_list = [pref.model_dump() for pref in preferences_data.preferences]
        
        # Validate at least one preference
        if not preferences_list:
            raise HTTPException(status_code=400, detail="At least one hiring preference required")
        
        # Validate salary ranges
        for pref in preferences_list:
            if pref['salary_max'] < pref['salary_min']:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Max salary must be >= min salary for {pref['role']}"
                )
        
        # Update hiring preferences
        employer.hiring_preferences = preferences_list
        db.commit()
        db.refresh(employer)
        
        logger.info(f"Hiring preferences updated for employer_id={employer.id}, count={len(preferences_list)}")
        
        return {
            "success": True,
            "message": f"Saved {len(preferences_list)} hiring preference(s)",
            "preferences": employer.hiring_preferences
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating hiring preferences: {e}")
        raise HTTPException(status_code=500, detail=str(e))
