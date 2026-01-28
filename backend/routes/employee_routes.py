# backend/routes/employee_routes.py
from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel, Field
from typing import List, Optional
from backend.db.sql_db import SessionLocal
from backend.db.models import Employee, Job, Application, OnboardingProgress, Employer, Interview
from backend.db.vector_db import get_vector_store
from difflib import SequenceMatcher
import logging
import datetime

logger = logging.getLogger(__name__)

router = APIRouter()

class EmployeeCreate(BaseModel):
    name: str
    email: str
    resume_text: str

class DiscoverQuery(BaseModel):
    query: str
    k: int = 5

class ApplyPayload(BaseModel):
    employee_id: int
    job_id: int

@router.post("/register")
def register(payload: EmployeeCreate):
    """Register a new employee."""
    db = SessionLocal()
    try:
        employee = Employee(
            name=payload.name,
            email=payload.email,
            resume_text=payload.resume_text
        )
        db.add(employee)
        db.commit()
        db.refresh(employee)
        
        # Try to index in vector store
        try:
            vs = get_vector_store()
            vs.add_documents([{
                "page_content": payload.resume_text,
                "metadata": {"employee_id": employee.id, "email": payload.email}
            }])
        except Exception as e:
            logger.warning(f"Vector store indexing failed: {str(e)}")
        
        return {"id": employee.id, "name": employee.name, "email": employee.email}
    except Exception as e:
        db.rollback()
        logger.error(f"Employee registration error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")
    finally:
        db.close()

@router.post("/discover")
def discover(payload: DiscoverQuery):
    """Discover jobs matching the query."""
    # Try vector store search
    try:
        vs = get_vector_store()
        results = vs.similarity_search_with_score(payload.query, k=payload.k)
        jobs = []
        for doc, score in results:
            if doc.metadata.get("job_id"):
                jobs.append({
                    "job_id": doc.metadata.get("job_id"),
                    "score": float(1 - score),  # Convert distance to similarity
                    "text": doc.page_content
                })
        if jobs:
            return jobs
    except Exception as e:
        logger.warning(f"Vector search failed: {str(e)}")
    
    # Fallback: DB search with text similarity
    db = SessionLocal()
    try:
        rows = db.query(Job).filter(Job.is_active == True).all()
        scored = []
        for job in rows:
            text = f"{job.title or ''}\n{job.description or ''}"
            score = SequenceMatcher(None, text, payload.query).ratio()
            scored.append({
                "job_id": job.id,
                "title": job.title,
                "score": round(score, 2)
            })
        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:payload.k]
    finally:
        db.close()

class ApplicationPayload(BaseModel):
    job_id: int
    user_id: int  # Added to pass user ID from frontend
    cover_letter: Optional[str] = None
    match_score: Optional[float] = 0.0  # Pre-calculated from job search

@router.post("/applications")
def create_application(payload: ApplicationPayload):
    """
    Submit a job application.
    Uses JobApplicationTool to handle application creation with match score calculation.
    """
    try:
        from backend.tools_langchain.job_application_tool import JobApplicationTool
        import json
        
        # Use JobApplicationTool to create application
        app_tool = JobApplicationTool()
        result_json = app_tool._run(
            user_id=payload.user_id,
            job_id=payload.job_id,
            cover_letter=payload.cover_letter or "",
            match_score=payload.match_score or 0.0  # Use pre-calculated score from UI
        )
        
        result = json.loads(result_json)
        
        if not result.get("success"):
            error_msg = result.get("error", "Failed to create application")
            logger.warning(f"Application failed: {error_msg}")
            raise HTTPException(status_code=400, detail=error_msg)
        
        return {
            "success": True,
            "message": "Application submitted successfully! 🎉",
            "application": result.get("application")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Application creation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/apply")
def apply(payload: ApplyPayload):
    """Apply to a job."""
    db = SessionLocal()
    try:
        # Verify employee and job exist
        employee = db.query(Employee).filter(Employee.id == payload.employee_id).first()
        if not employee:
            raise HTTPException(status_code=404, detail="Employee not found")
        
        job = db.query(Job).filter(Job.id == payload.job_id).first()
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Check for duplicate application
        existing = db.query(Application).filter(
            Application.employee_id == payload.employee_id,
            Application.job_id == payload.job_id
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"You have already applied to this job (Application #{existing.id})"
            )
        
        # Create application
        application = Application(
            job_id=payload.job_id,
            employee_id=payload.employee_id
        )
        db.add(application)
        db.commit()
        db.refresh(application)
        return {"application_id": application.id, "status": application.status}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Application error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Application failed: {str(e)}")
    finally:
        db.close()


@router.post("/quick-apply/{job_id}")
def quick_apply(job_id: int, employee_id: int):
    """
    Quick Apply - One-click job application with automatic match scoring.
    
    Features:
    - Duplicate application prevention
    - Automatic match score calculation
    - Instant notification to employee
    - Returns application details
    """
    db = SessionLocal()
    try:
        # 1. Verify employee exists
        employee = db.query(Employee).filter(Employee.id == employee_id).first()
        if not employee:
            raise HTTPException(status_code=404, detail="Employee not found")
        
        # 2. Verify job exists and is active
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        if not job.is_active:
            raise HTTPException(status_code=400, detail="This job is no longer accepting applications")
        
        # 3. Check for duplicate application
        existing = db.query(Application).filter(
            Application.job_id == job_id,
            Application.employee_id == employee_id
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=400, 
                detail=f"You have already applied to this job (Application #{existing.id})"
            )
        
        # 4. Calculate match score using existing matching logic
        match_score = 0.70  # Default score
        
        try:
            # Simple skill-based matching
            if employee.skills and job.description:
                employee_skills = [s.lower() for s in employee.skills] if isinstance(employee.skills, list) else []
                job_desc_lower = job.description.lower()
                
                skill_matches = sum(1 for skill in employee_skills if skill in job_desc_lower)
                total_skills = len(employee_skills) if employee_skills else 1
                match_score = min(0.50 + (skill_matches / total_skills * 0.40), 0.95)
                
                # Boost for experience match
                if employee.experience_years and job.min_hospitality_experience:
                    if employee.experience_years >= job.min_hospitality_experience:
                        match_score += 0.05
                
                # Boost for role match
                if employee.preferred_role and job.job_category:
                    if employee.preferred_role.value == job.job_category.value:
                        match_score += 0.10
                
                match_score = min(round(match_score, 2), 0.98)
        except Exception as e:
            logger.warning(f"Match score calculation failed, using default: {e}")
        
        # 5. Create application
        application = Application(
            job_id=job_id,
            employee_id=employee_id,
            match_score=match_score,
            applied_at=datetime.datetime.utcnow()
        )
        
        db.add(application)
        db.commit()
        db.refresh(application)
        
        # 6. Send notification to employee
        try:
            from backend.db.models import Notification
            from backend.notifications.connection_manager import manager
            from backend.utils.notification_helpers import add_credentials_to_notification_metadata
            import json
            import asyncio
            
            # Get employer name for notification
            from backend.db.models import Employer
            employer = db.query(Employer).filter(Employer.id == job.employer_id).first()
            employer_name = employer.company_name if employer else "the employer"
            
            # Prepare metadata with credentials
            employee_metadata = add_credentials_to_notification_metadata(
                db=db,
                recipient_id=employee.user_id,  # Employee receiving notification
                sender_id=employer.user_id if employer else None,  # Employer (system notification)
                existing_metadata={
                    "application_id": application.id,
                    "job_id": job_id,
                    "job_title": job.title,
                    "match_score": match_score
                }
            )
            
            # Create notification
            notification = Notification(
                recipient_id=employee.user_id,
                title="Application Submitted! 🎉",
                message=f"Your application for {job.title} at {employer_name} has been  submitted successfully. Match score: {int(match_score*100)}%",
                notification_type="application",
                action_url=f"/employee/applications/{application.id}",
                meta_data=employee_metadata
            )
            db.add(notification)
            db.commit()
            
            #  Send WebSocket notification (best effort)
            try:
                loop = asyncio.new_event_loop()
                notification_data = {
                    "id": notification.id,
                    "title": notification.title,
                    "message": notification.message,
                    "type": "application",
                    "action_url": notification.action_url
                }
                loop.run_until_complete(manager.send_personal_message(
                    json.dumps(notification_data),
                    employee.user_id
                ))
            except:
                pass  # WebSocket failure is non-critical
                
        except Exception as e:
            logger.warning(f"Failed to send application notification: {e}")
        
        # NEW: Notify employer about new application
        try:
            # Prepare metadata with credentials
            employer_metadata = add_credentials_to_notification_metadata(
                db=db,
                recipient_id=employer.user_id,      # Employer receiving notification
                sender_id=employee.user_id,          # Employee who applied
                existing_metadata={
                    "application_id": application.id,
                    "employee_name": employee.full_name,
                    "job_title": job.title,
                    "match_score": match_score
                }
            )
            
            employer_notification = Notification(
                recipient_id=employer.user_id,
                title="New Application Received! 📋",
                message=f"{employee.full_name} applied for {job.title}. Match score: {int(match_score*100)}%",
                notification_type="application",
                action_url=f"/employer/applications/{application.id}",
                meta_data=employer_metadata
            )
            db.add(employer_notification)
            db.commit()
            db.refresh(employer_notification)
            
            # Send WebSocket notification to employer (best effort)
            try:
                employer_notification_data = {
                    "id": employer_notification.id,
                    "title": employer_notification.title,
                    "message": employer_notification.message,
                    "type": "application",
                    "action_url": employer_notification.action_url,
                    "application_id": application.id,
                    "employee_name": employee.full_name,
                    "job_title": job.title,
                    "match_score": match_score
                }
                loop = asyncio.new_event_loop()
                loop.run_until_complete(manager.send_personal_message(
                    json.dumps(employer_notification_data),
                    employer.user_id
                ))
                loop.close()
                logger.info(f"✅ Employer {employer.user_id} notified about application {application.id}")
            except Exception as ws_error:
                logger.warning(f"⚠️  WebSocket to employer failed: {ws_error}")
                # Non-critical
                
        except Exception as e:
            logger.warning(f"⚠️  Failed to notify employer: {e}")
            # Non-critical, don't fail the application
        
        # 7. Return success response
        logger.info(f"✅ Quick Apply: Employee {employee_id} applied to Job {job_id} (Score: {match_score})")
        
        return {
            "success": True,
            "application_id": application.id,
            "job_title": job.title,
            "match_score": match_score,
            "status": application.status.value,
            "message": f"Successfully applied! Your profile has a {int(match_score*100)}% match with this position."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Quick Apply error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Application failed: {str(e)}")
    finally:
        db.close()

@router.get("/employees/{employee_id}/onboarding-progress")
def get_onboarding_progress(employee_id: int):
    """
    Get onboarding progress for an employee.
    Creates initial progress record if it doesn't exist.
    """
    db = SessionLocal()
    try:
        # Check if employee exists
        employee = db.query(Employee).filter(Employee.id == employee_id).first()
        if not employee:
            raise HTTPException(status_code=404, detail="Employee not found")
        
        # Get or create progress record
        progress = db.query(OnboardingProgress).filter(
            OnboardingProgress.employee_id == employee_id
        ).first()
        
        if not progress:
            # Create initial progress record
            progress = OnboardingProgress(employee_id=employee_id)
            db.add(progress)
            db.commit()
            db.refresh(progress)
            logger.info(f"Created onboarding progress for employee {employee_id}")
        
        # Calculate completion percentage
        steps_completed = sum([
            progress.profile_completed,
            progress.skills_completed,
            progress.preferences_completed,
            progress.certifications_completed,
            progress.documents_completed
        ])
        total_steps = 5
        completion_pct = int((steps_completed / total_steps) * 100)
        
        # Update completion percentage if changed
        if progress.completion_percentage != completion_pct:
            progress.completion_percentage = completion_pct
            progress.is_complete = (completion_pct == 100)
            if progress.is_complete and not progress.completed_at:
                import datetime
                progress.completed_at = datetime.datetime.utcnow()
            db.commit()
        
        return {
            "employee_id": employee_id,
            "current_step": progress.current_step,
            "is_complete": progress.is_complete,
            "completion_percentage": completion_pct,
            "steps": {
                "profile": progress.profile_completed,
                "skills": progress.skills_completed,
                "preferences": progress.preferences_completed,
                "certifications": progress.certifications_completed,
                "documents": progress.documents_completed
            },
            "started_at": progress.started_at.isoformat() if progress.started_at else None,
            "completed_at": progress.completed_at.isoformat() if progress.completed_at else None,
            "last_updated": progress.last_updated.isoformat() if progress.last_updated else None
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching onboarding progress: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch onboarding progress: {str(e)}")
    finally:
        db.close()

# Onboarding Update Endpoints
class ProfileUpdateSchema(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
class SkillsSchema(BaseModel):
    skills: List[str]  # Technical skills
    soft_skills: Optional[List[str]] = []  # NEW: Soft skills
    experience_years: Optional[int] = None
    years_in_hospitality: Optional[int] = None

class PreferencesSchema(BaseModel):
    preferred_role: Optional[str] = None
    preferred_location: Optional[str] = None
    preferred_shift: Optional[str] = None
    expected_salary_min: Optional[int] = None
    expected_salary_max: Optional[int] = None

class CertificationsSchema(BaseModel):
    certifications: List[str]

class WorkHistoryEntry(BaseModel):
    """Schema for a single work experience entry."""
    employer: str = Field(..., description="Company/Restaurant name")
    position: str = Field(..., description="Job title/role")
    location: Optional[str] = Field(None, description="Work location")
    start_date: str = Field(..., description="Start date in YYYY-MM format")
    end_date: Optional[str] = Field(None, description="End date in YYYY-MM format (null if current)")
    is_current: bool = Field(False, description="Currently working here")
    achievements: List[str] = Field(default_factory=list, description="Key achievements and responsibilities")

class WorkHistorySchema(BaseModel):
    """Schema for updating work history."""
    work_history: List[WorkHistoryEntry]

def update_onboarding_step(db, employee_id: int, step_name: str):
    """Helper function to mark an onboarding step as complete."""
    progress = db.query(OnboardingProgress).filter(
        OnboardingProgress.employee_id == employee_id
    ).first()
    
    if not progress:
        progress = OnboardingProgress(employee_id=employee_id)
        db.add(progress)
    
    # Mark step as complete
    if step_name == "profile":
        progress.profile_completed = True
        progress.current_step = "skills"
    elif step_name == "skills":
        progress.skills_completed = True
        progress.current_step = "preferences"
    elif step_name == "preferences":
        progress.preferences_completed = True
        progress.current_step = "certifications"
    elif step_name == "certifications":
        progress.certifications_completed = True
        progress.current_step = "documents"
    elif step_name == "documents":
        progress.documents_completed = True
        progress.current_step = "complete"
    
    # Calculate completion percentage
    steps_completed = sum([
        progress.profile_completed,
        progress.skills_completed,
        progress.preferences_completed,
        progress.certifications_completed,
        progress.documents_completed
    ])
    progress.completion_percentage = int((steps_completed / 5) * 100)
    progress.is_complete = (progress.completion_percentage == 100)
    
    if progress.is_complete and not progress.completed_at:
        progress.completed_at = datetime.datetime.utcnow()
    
    db.commit()
    return progress

@router.put("/employees/{employee_id}/profile")
def update_employee_profile(employee_id: int, profile_data: ProfileUpdateSchema):
    """
    Update employee profile information.
    Marks 'profile' onboarding step as complete.
    """
    db = SessionLocal()
    try:
        employee = db.query(Employee).filter(Employee.id == employee_id).first()
        if not employee:
            raise HTTPException(status_code=404, detail="Employee not found")
        
        # Update profile fields
        if profile_data.full_name:
            employee.full_name = profile_data.full_name
        if profile_data.phone:
            employee.phone = profile_data.phone
        if profile_data.location:
            employee.preferred_location = profile_data.location        
        employee.updated_at = datetime.datetime.utcnow()
        
        # Mark onboarding step as complete
        progress = update_onboarding_step(db, employee_id, "profile")
        
        db.commit()
        
        # Trigger automatic profile analysis (background task)
        from backend.utils.background_tasks import schedule_background_task
        from backend.tools_langchain.bulk_profile_processor_tool import analyze_single_employee
        schedule_background_task(analyze_single_employee(employee_id, db))
        logger.info(f"📊 Profile analysis scheduled for employee {employee_id} after profile update")
        
        return {
            "success": True,
            "message": "Profile updated successfully",
            "employee_id": employee_id,
            "onboarding_progress": progress.completion_percentage
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Profile update error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Profile update failed: {str(e)}")
    finally:
        db.close()

@router.post("/employees/{employee_id}/skills")
def add_employee_skills(employee_id: int, skills_data: SkillsSchema):
    """
    Add skills and experience to employee profile.
    Marks 'skills' onboarding step as complete.
    """
    db = SessionLocal()
    try:
        employee = db.query(Employee).filter(Employee.id == employee_id).first()
        if not employee:
            raise HTTPException(status_code=404, detail="Employee not found")
        
        # Update skills
        employee.skills = skills_data.skills
        if skills_data.soft_skills:
            employee.soft_skills = skills_data.soft_skills  # NEW: Store soft skills
        if skills_data.experience_years is not None:
            employee.experience_years = skills_data.experience_years
        if skills_data.years_in_hospitality is not None:
            employee.years_in_hospitality = skills_data.years_in_hospitality
        
        employee.updated_at = datetime.datetime.utcnow()
        
        # Mark onboarding step as complete
        progress = update_onboarding_step(db, employee_id, "skills")
        
        db.commit()
        
        # Trigger automatic profile analysis (background task)
        from backend.utils.background_tasks import schedule_background_task
        from backend.tools_langchain.bulk_profile_processor_tool import analyze_single_employee
        schedule_background_task(analyze_single_employee(employee_id, db))
        logger.info(f"📊 Profile analysis scheduled for employee {employee_id} after skills update")
        
        return {
            "success": True,
            "message": "Skills added successfully",
            "employee_id": employee_id,
            "skills_count": len(skills_data.skills),
            "onboarding_progress": progress.completion_percentage
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Skills update error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Skills update failed: {str(e)}")
    finally:
        db.close()

@router.put("/employees/{employee_id}/preferences")
def update_job_preferences(employee_id: int, preferences: PreferencesSchema):
    """
    Update job preferences for employee.
    Marks 'preferences' onboarding step as complete.
    """
    db = SessionLocal()
    try:
        employee = db.query(Employee).filter(Employee.id == employee_id).first()
        if not employee:
            raise HTTPException(status_code=404, detail="Employee not found")
        
        # Update preferences
        if preferences.preferred_role:
            employee.preferred_role = preferences.preferred_role
        if preferences.preferred_location:
            employee.preferred_location = preferences.preferred_location
        if preferences.preferred_shift:
            employee.preferred_shift = preferences.preferred_shift
        if preferences.expected_salary_min is not None:
            employee.expected_salary_min = preferences.expected_salary_min
        if preferences.expected_salary_max is not None:
            employee.expected_salary_max = preferences.expected_salary_max
        
        employee.updated_at = datetime.datetime.utcnow()
        
        # Mark onboarding step as complete
        progress = update_onboarding_step(db, employee_id, "preferences")
        
        db.commit()
        
        return {
            "success": True,
            "message": "Preferences updated successfully",
            "employee_id": employee_id,
            "onboarding_progress": progress.completion_percentage
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Preferences update error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Preferences update failed: {str(e)}")
    finally:
        db.close()

@router.post("/employees/{employee_id}/certifications")
def add_certifications(employee_id: int, certs: CertificationsSchema):
    """
    Add certifications to employee profile.
    Marks 'certifications' onboarding step as complete.
    """
    db = SessionLocal()
    try:
        employee = db.query(Employee).filter(Employee.id == employee_id).first()
        if not employee:
            raise HTTPException(status_code=404, detail="Employee not found")
        
        # Update certifications
        employee.certifications = certs.certifications
        employee.updated_at = datetime.datetime.utcnow()
        
        # Mark onboarding step as complete
        progress = update_onboarding_step(db, employee_id, "certifications")
        
        db.commit()
        
        return {
            "success": True,
            "message": "Certifications added successfully",
            "employee_id": employee_id,
            "certifications_count": len(certs.certifications),
            "onboarding_progress": progress.completion_percentage
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Certifications update error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Certifications update failed: {str(e)}")
    finally:
        db.close()

@router.post("/employees/{employee_id}/resume/upload")
async def upload_resume(employee_id: int, file: UploadFile = File(...)):
    """
    Upload resume file for employee.
    Marks 'documents' onboarding step as complete.
    """
    db = SessionLocal()
    try:
        employee = db.query(Employee).filter(Employee.id == employee_id).first()
        if not employee:
            raise HTTPException(status_code=404, detail="Employee not found")
        
        # Validate file type
        allowed_types = ["application/pdf", "application/msword", 
                        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        "text/plain"]
        if file.content_type not in allowed_types:
            raise HTTPException(status_code=400, detail="Invalid file type. Please upload PDF, DOC, DOCX, or TXT")
        
        # Read file content
        content = await file.read()
        
        # For now, store as text (TODO: implement proper file storage)
        if file.content_type == "text/plain":
            resume_text = content.decode('utf-8')
        else:
            # TODO: Extract text from PDF/DOC files
            resume_text = f"Resume uploaded: {file.filename}"
        
        employee.resume_text = resume_text
        employee.updated_at = datetime.datetime.utcnow()
        
        # Mark onboarding step as complete
        progress = update_onboarding_step(db, employee_id, "documents")
        
        db.commit()
        
        # Trigger automatic profile analysis (background task)
        from backend.utils.background_tasks import schedule_background_task
        from backend.tools_langchain.bulk_profile_processor_tool import analyze_single_employee
        schedule_background_task(analyze_single_employee(employee_id, db))
        logger.info(f"📊 Profile analysis scheduled for employee {employee_id} after resume upload")
        
        return {
            "success": True,
            "message": "Resume uploaded successfully",
            "employee_id": employee_id,
            "filename": file.filename,
            "file_size": len(content),
            "onboarding_progress": progress.completion_percentage,
            "onboarding_complete": progress.is_complete
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Resume upload error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Resume upload failed: {str(e)}")
    finally:
        db.close()

# Resume Generation Endpoints
class ResumeGeneratePayload(BaseModel):
    regenerate: bool = False
    format: str = "text"  # text, markdown, or pdf

@router.get("/employees/{employee_id}/resume")
def get_resume(employee_id: int):
    """
    Get generated resume for an employee.
    Returns cached resume if available.
    """
    db = SessionLocal()
    try:
        employee = db.query(Employee).filter(Employee.id == employee_id).first()
        if not employee:
            raise HTTPException(status_code=404, detail="Employee not found")
        
        if not employee.resume_text:
            return {
                "employee_id": employee_id,
                "has_resume": False,
                "message": "No resume generated yet. Use POST /resume/generate to create one."
            }
        
        return {
            "employee_id": employee_id,
            "employee_name": employee.full_name,
            "has_resume": True,
            "resume_content": employee.resume_text,
            "generated_at": employee.last_profile_analysis.isoformat() if employee.last_profile_analysis else None,
            "word_count": len(employee.resume_text.split()) if employee.resume_text else 0
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching resume: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch resume: {str(e)}")
    finally:
        db.close()

@router.post("/employees/{employee_id}/resume/generate")
def generate_resume(employee_id: int, payload: ResumeGeneratePayload = ResumeGeneratePayload()):
    """
    Generate or regenerate resume for an employee using AI.
    Uses ResumeGeneratorTool with GPT-4o-mini.
    Marks 'documents' onboarding step as complete.
    """
    db = SessionLocal()
    try:
        from backend.tools_langchain.resume_generator_tool import ResumeGeneratorTool
        
        tool = ResumeGeneratorTool()
        result_json = tool._run(
            employee_id=employee_id,
            format=payload.format,
            regenerate=payload.regenerate
        )
        
        import json
        result = json.loads(result_json)
        
        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error", "Resume generation failed"))
        
        # Mark onboarding step as complete
        progress = update_onboarding_step(db, employee_id, "documents")
        db.commit()
        
        # Add onboarding progress to result
        result["onboarding_progress"] = progress.completion_percentage
        result["onboarding_complete"] = progress.is_complete
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Resume generation error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Resume generation failed: {str(e)}")
    finally:
        db.close()


@router.get("/employees/{employee_id}/resume/download")
def download_resume_pdf(employee_id: int):
    """
    Download resume as PDF in A4 format.
    """
    from fastapi.responses import StreamingResponse
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    from io import BytesIO
    
    db = SessionLocal()
    try:
        employee = db.query(Employee).filter(Employee.id == employee_id).first()
        if not employee:
            raise HTTPException(status_code=404, detail="Employee not found")
        
        if not employee.resume_text:
            raise HTTPException(status_code=404, detail="No resume available. Generate one first.")
        
        # Create PDF in memory
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4,
                              rightMargin=0.75*inch, leftMargin=0.75*inch,
                              topMargin=0.75*inch, bottomMargin=0.75*inch)
        
        # Container for PDF elements
        story = []
        
        # Styles
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            textColor='#1a1a1a',
            spaceAfter=12,
            alignment=TA_CENTER
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=12,
            textColor='#2563eb',
            spaceAfter=6,
            spaceBefore=12
        )
        
        body_style = ParagraphStyle(
            'CustomBody',
            parent=styles['BodyText'],
            fontSize=10,
            textColor='#374151',
            spaceAfter=6,
            alignment=TA_LEFT
        )
        
        # Parse resume text and add to PDF
        resume_lines = employee.resume_text.split('\n')
        
        for line in resume_lines:
            line = line.strip()
            if not line:
                story.append(Spacer(1, 0.1*inch))
                continue
            
            # Detect section headers (all caps or specific patterns)
            if line.isupper() and len(line) > 3:
                story.append(Paragraph(line, heading_style))
            elif line.startswith('•') or line.startswith('-'):
                # Bullet points
                story.append(Paragraph(line, body_style))
            else:
                # Regular text
                story.append(Paragraph(line, body_style))
        
        # Build PDF
        doc.build(story)
        
        # Get PDF data
        buffer.seek(0)
        
        # Generate filename
        filename = f"resume_{employee.full_name.replace(' ', '_')}_{employee_id}.pdf"
        
        return StreamingResponse(
            buffer,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"PDF generation error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")
    finally:
        db.close()


# Profile Analysis Endpoint
@router.post("/employees/{employee_id}/analyze-profile")
async def analyze_employee_profile(employee_id: int):
    """
    Manually trigger profile analysis for an employee.
    
    This endpoint allows on-demand profile processing without waiting for
    automatic triggers or backend restart.
    
    Features:
    - Uses HybridProfileAnalyzer (Gemini 2.0 Flash + GPT-4o-mini)
    - Updates ProfileCache with professional summary and recommendations
    - Runs asynchronously (non-blocking)
    
    Returns:
        {
            "success": bool,
            "message": str,
            "employee_id": int,
            "professional_summary": str (if successful)
        }
    """
    db = SessionLocal()
    try:
        # Verify employee exists
        employee = db.query(Employee).filter(Employee.id == employee_id).first()
        if not employee:
            raise HTTPException(status_code=404, detail="Employee not found")
        
        # Import analysis function
        from backend.tools_langchain.bulk_profile_processor_tool import analyze_single_employee
        
        # Run analysis
        logger.info(f"🔍 Manual profile analysis triggered for employee {employee_id}")
        result = await analyze_single_employee(employee_id, db)
        
        if not result.get("success"):
            raise HTTPException(
                status_code=500, 
                detail=result.get("error", "Profile analysis failed")
            )
        
        return {
            "success": True,
            "message": "Profile analysis completed successfully",
            "employee_id": employee_id,
            "professional_summary": result.get("professional_summary", "")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Manual profile analysis error: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Profile analysis failed: {str(e)}"
        )
    finally:
        db.close()


# Job Recommendations Endpoint
@router.get("/recommendations/{employee_id}")
def get_job_recommendations(employee_id: int, limit: int = 10):
    """
    Get personalized job recommendations for an employee.
    Uses JobRecommenderTool with intelligent ranking.
    """
    try:
        from backend.tools_langchain.job_recommender_tool import JobRecommenderTool
        import json
        
        tool = JobRecommenderTool()
        result_json = tool._run(employee_id=employee_id, limit=limit)
        result = json.loads(result_json)
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Recommendations error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch recommendations: {str(e)}")


@router.get("/employees/{employee_id}/recommended-jobs")
def get_recommended_jobs_for_employee(
    employee_id: int,
    search: Optional[str] = None,
    location: Optional[str] = None,
    job_type: Optional[str] = None,
    min_salary: Optional[int] = None,
    max_salary: Optional[int] = None,
    experience_level: Optional[str] = None,
    top_k: int = 20
):
    """
    Get personalized job recommendations for an employee based on their profile.
    Uses MatchingTool with semantic search for intelligent job matching.
    
    Query Parameters:
    - search: Keyword search (job title, skills, etc.)
    - location: Filter by location
    - job_type: Filter by job type (full_time, part_time, contract)
    - min_salary: Minimum salary filter
    - max_salary: Maximum salary filter
    - experience_level: Filter by experience level
    - top_k: Number of results to return (default 20)
    
    Returns:
    - List of jobs with match scores, sorted by relevance
    - Each job includes posting date (created_at)
    - Already applied status
    """
    db = SessionLocal()
    try:
        # 1. Fetch employee profile
        employee = db.query(Employee).filter(Employee.id == employee_id).first()
        if not employee:
            raise HTTPException(status_code=404, detail="Employee not found")
        
        # 2. Build query string from employee profile
        query_parts = []
        
        # Add role preference
        if employee.preferred_role:
            query_parts.append(f"Role: {employee.preferred_role.value if hasattr(employee.preferred_role, 'value') else employee.preferred_role}")
        
        # Add skills
        if employee.skills:
            skills_str = ", ".join(employee.skills) if isinstance(employee.skills, list) else str(employee.skills)
            query_parts.append(f"Skills: {skills_str}")
        
        # Add experience
        if employee.years_in_hospitality:
            query_parts.append(f"{employee.years_in_hospitality} years hospitality experience")
        
        # Add certifications
        if employee.food_safety_certified:
            query_parts.append("Food Safety Certified")
        if employee.alcohol_service_certified:
            query_parts.append("Alcohol Service Certified")
        
        # Add location preference
        if employee.preferred_location:
            query_parts.append(f"Location: {employee.preferred_location}")
        
        # Add search keyword if provided
        if search:
            query_parts.insert(0, search)  # Prioritize user search
        
        query_text = ". ".join(query_parts)
        logger.info(f"🔍 Job search query for employee {employee_id}: {query_text[:200]}")
        
        # 3. Use JobFinderTool for two-way intelligent matching (same as chat)
        from backend.tools_langchain.job_finder_tool import JobFinderTool
        import json
        
        job_finder = JobFinderTool()
        result_json = job_finder._run(
            search_query=query_text,
            location=location or "",
            job_type=job_type or "",
            limit=top_k,
            employee_id=employee_id  # Enable personalized two-way matching
        )
        
        result = json.loads(result_json)
        
        if not result.get("success") or not result.get("jobs"):
            return {
                "jobs": [],
                "total": 0,
                "message": result.get("message", "No matching jobs found. Try adjusting your search criteria.")
            }
        
        # 4. Enrich job data and apply filters
        job_ids = [job["job_id"] for job in result["jobs"]]
        jobs = db.query(Job).filter(Job.id.in_(job_ids), Job.is_active == True).all()
        
        # Create lookup dict for match scores (from JobFinderTool)
        match_scores = {job["job_id"]: job.get("match_score", 0) for job in result["jobs"]}
        
        # Get already applied job IDs
        applied_job_ids = set(
            db.query(Application.job_id)
            .filter(Application.employee_id == employee_id)
            .all()
        )
        applied_job_ids = {jid[0] for jid in applied_job_ids}
        
        enriched_jobs = []
        # Apply filters (already handled by JobFinderTool, but keeping for manual searches)
        for job in jobs:
            # Apply filters
            if location and location.lower() not in (job.location or "").lower():
                continue
            
            if job_type and job.job_type != job_type:
                continue
            
            # Salary filtering (basic, assumes salary_range format like "Rs. 20,000 - Rs. 30,000")
            if min_salary or max_salary:
                # Skip if salary range not available
                if not job.salary_range or "competitive" in job.salary_range.lower():
                    continue
            
            if experience_level:
                # Map experience level to years
                exp_map = {"entry": 0, "mid": 2, "senior": 5}
                required_years = exp_map.get(experience_level.lower(), 0)
                if job.min_hospitality_experience and job.min_hospitality_experience > required_years + 2:
                    continue
            
            # Get employer info
            employer = db.query(Employer).filter(Employer.id == job.employer_id).first()
            
            # Calculate relative posting time
            import datetime
            posted_at = job.created_at
            time_diff = datetime.datetime.utcnow() - posted_at if posted_at else None
            
            if time_diff:
                if time_diff.days == 0:
                    posted_time = "Today"
                elif time_diff.days == 1:
                    posted_time = "Yesterday"
                elif time_diff.days < 7:
                    posted_time = f"{time_diff.days} days ago"
                elif time_diff.days < 30:
                    weeks = time_diff.days // 7
                    posted_time = f"{weeks} week{'s' if weeks > 1 else ''} ago"
                else:
                    months = time_diff.days // 30
                    posted_time = f"{months} month{'s' if months > 1 else ''} ago"
            else:
                posted_time = "Recently"
            
            enriched_job = {
                "id": job.id,
                "employer_id": job.employer_id,
                "title": job.title,
                "description": job.description,
                "location": job.location,
                "job_type": job.job_type,
                "salary_range": job.salary_range,
                "requirements": job.requirements if hasattr(job, 'requirements') else None,
                "is_active": job.is_active,
                "created_at": job.created_at.isoformat() if job.created_at else None,
                "posted_time": posted_time,  # Human-readable time
                "updated_at": job.updated_at.isoformat() if job.updated_at else None,
                "match_score": match_scores.get(job.id, 0) / 100,  # Convert to 0-1 scale
                "already_applied": job.id in applied_job_ids,
                "company_name": employer.company_name if employer else "Unknown Company",
                "min_hospitality_experience": job.min_hospitality_experience,
                "job_category": job.job_category.value if job.job_category else None
            }
            
            enriched_jobs.append(enriched_job)
        
        # 5. Sort by match score (highest first)
        enriched_jobs.sort(key=lambda x: x["match_score"], reverse=True)
        
        # 6. Limit to top_k results
        enriched_jobs = enriched_jobs[:top_k]
        
        logger.info(f"✅ Returning {len(enriched_jobs)} personalized jobs for employee {employee_id}")
        
        return {
            "jobs": enriched_jobs,
            "total": len(enriched_jobs),
            "employee_id": employee_id,
            "search_query": query_text,
            "filters_applied": {
                "search": search,
                "location": location,
                "job_type": job_type,
                "min_salary": min_salary,
                "max_salary": max_salary,
                "experience_level": experience_level
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching recommended jobs: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to fetch job recommendations: {str(e)}")
    finally:
        db.close()


# Add this to the end of backend/routes/employee_routes.py

@router.get("/applications")
def get_employee_applications(user_id: Optional[int] = None):
    """
    Get all applications for an employee by user_id.
    Converts user_id to employee_id and fetches applications with job details.
    """
    from sqlalchemy import text
    db = SessionLocal()
    try:
        # If no user_id provided, return empty (in production, get from JWT)
        if not user_id:
            return []
        
        # Convert user_id to employee_id
        employee = db.query(Employee).filter(Employee.user_id == user_id).first()
        if not employee:
            logger.warning(f"No employee found for user_id {user_id}")
            return []
        
        # Use raw SQL to fetch applications to avoid enum validation issues
        result_raw = db.execute(
            text("""
                SELECT 
                    a.id, a.job_id, a.employee_id, a.status, a.match_score,
                    a.cover_letter, a.applied_at, a.updated_at, a.reviewed_at, a.notes,
                    j.title as job_title, j.description as job_description,
                    j.location as job_location, j.salary_range, j.job_type,
                    e.company_name as employer_name
                FROM applications a
                LEFT JOIN jobs j ON a.job_id = j.id
                LEFT JOIN employers e ON j.employer_id = e.id
                WHERE a.employee_id = :employee_id
                ORDER BY a.applied_at DESC
            """),
            {"employee_id": employee.id}
        )
        
        applications_data = result_raw.fetchall()
        
        # Format response
        result = []
        for row in applications_data:
            (app_id, job_id, employee_id, status, match_score, cover_letter,
             applied_at, updated_at, reviewed_at, notes, job_title, job_description,
             job_location, salary_range, job_type, employer_name) = row
            
            # Build job data if job exists
            job_data = None
            if job_id and job_title:
                job_data = {
                    "id": job_id,
                    "title": job_title,
                    "description": job_description,
                    "location": job_location,
                    "salary_range": salary_range,
                    "job_type": job_type,
                    "employer": {
                        "company_name": employer_name
                    }
                }
            
            # Handle datetime serialization
            applied_at_str = applied_at.isoformat() if hasattr(applied_at, 'isoformat') else str(applied_at) if applied_at else None
            updated_at_str = updated_at.isoformat() if hasattr(updated_at, 'isoformat') else str(updated_at) if updated_at else None
            reviewed_at_str = reviewed_at.isoformat() if hasattr(reviewed_at, 'isoformat') else str(reviewed_at) if reviewed_at else None
            
            result.append({
                "id": app_id,
                "job_id": job_id,
                "employee_id": employee_id,
                "status": status,
                "match_score": match_score or 0.0,
                "cover_letter": cover_letter,
                "applied_at": applied_at_str,
                "updated_at": updated_at_str,
                "reviewed_at": reviewed_at_str,
                "notes": notes,
                "job": job_data
            })
        
        return result
        
    except Exception as e:
        logger.error(f"Error fetching applications: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch applications: {str(e)}")
    finally:
        db.close()



@router.post("/employees/{employee_id}/work-history")
def update_work_history(employee_id: int, data: WorkHistorySchema):
    """
    Update work history for employee profile.
    Stores professional work experience including achievements.
    This enhances profile for better job matching and resume reviews.
    """
    db = SessionLocal()
    try:
        employee = db.query(Employee).filter(Employee.id == employee_id).first()
        if not employee:
            raise HTTPException(status_code=404, detail="Employee not found")
        
        # Convert Pydantic models to dict for JSON storage
        work_history_data = [entry.dict() for entry in data.work_history]
        
        # Update work history
        employee.work_history = work_history_data
        employee.updated_at = datetime.datetime.utcnow()
        
        # Optionally update skills step (work history is part of experience)
        progress = update_onboarding_step(db, employee_id, "skills")
        
        db.commit()
        
        return {
            "success": True,
            "message": "Work history updated successfully",
            "employee_id": employee_id,
            "entries_count": len(work_history_data),
            "onboarding_progress": progress.completion_percentage
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Work history update error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Work history update failed: {str(e)}")
    finally:
        db.close()


# Employee Interviews Endpoint
from backend.utils.auth import get_current_user
from fastapi import Depends

@router.get("/interviews")
def get_employee_interviews(
    current_user: dict = Depends(get_current_user)
):
    """Get all interviews for the logged-in employee."""
    from sqlalchemy import text
    db = SessionLocal()
    
    try:
        logger.info(f"Getting interviews for user {current_user.get('user_id')}")
        
        employee = db.query(Employee).filter(Employee.user_id == current_user["user_id"]).first()
        
        if not employee:
            raise HTTPException(status_code=404, detail="Employee profile not found")
        
        # Use raw SQL to get applications and avoid enum validation
        app_result = db.execute(
            text("SELECT id FROM applications WHERE employee_id = :employee_id"),
            {"employee_id": employee.id}
        )
        app_ids = [row[0] for row in app_result.fetchall()]
        
        if not app_ids:
            return []
        
        # Use raw SQL to fetch interviews with job details
        placeholders = ','.join([f':id{i}' for i in range(len(app_ids))])
        params = {f'id{i}': app_id for i, app_id in enumerate(app_ids)}
        
        interviews_result = db.execute(
            text(f"""
                SELECT 
                    i.id, i.application_id, i.scheduled_at, i.duration_minutes,
                    i.location, i.meeting_link, i.status, i.interviewer_notes,
                    i.feedback, i.created_at, i.updated_at,
                    j.title as job_title, e.company_name
                FROM interviews i
                LEFT JOIN applications a ON i.application_id = a.id
                LEFT JOIN jobs j ON a.job_id = j.id
                LEFT JOIN employers e ON j.employer_id = e.id
                WHERE i.application_id IN ({placeholders})
                ORDER BY i.scheduled_at DESC
            """),
            params
        )
        
        result = []
        for row in interviews_result.fetchall():
            (int_id, app_id, scheduled_at, duration_minutes, location, meeting_link,
             status, interviewer_notes, feedback, created_at, updated_at,
             job_title, company_name) = row
            
            # Handle datetime serialization
            scheduled_at_str = scheduled_at.isoformat() if hasattr(scheduled_at, 'isoformat') else str(scheduled_at)
            created_at_str = created_at.isoformat() if (created_at and hasattr(created_at, 'isoformat')) else (str(created_at) if created_at else None)
            updated_at_str = updated_at.isoformat() if (updated_at and hasattr(updated_at, 'isoformat')) else (str(updated_at) if updated_at else None)
            
            result.append({
                "id": int_id,
                "application_id": app_id,
                "job_title": job_title or "Unknown",
                "company_name": company_name or "Unknown",
                "scheduled_at": scheduled_at_str,
                "duration_minutes": duration_minutes,
                "location": location,
                "meeting_link": meeting_link,
                "status": status,
                "interviewer_notes": interviewer_notes,
                "feedback": feedback,
                "created_at": created_at_str,
                "updated_at": updated_at_str
            })
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching interviews: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch interviews: {str(e)}")
    finally:
        db.close()

