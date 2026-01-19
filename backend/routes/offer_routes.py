# backend/routes/offer_routes.py
"""
API routes for job offer management.
Supports the autonomous hiring pipeline where AI sends offers and employees accept/decline.
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import and_
from backend.db.sql_db import get_db
from backend.db.models import (
    Offer, Application, ApplicationStatus, Job, Employee, Employer, 
    User, Notification, OnboardingTask, OnboardingTaskType, OnboardingTaskStatus
)
from backend.utils.auth import get_current_user
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/offers", tags=["Offers"])


class OfferResponse(BaseModel):
    """Response model for offer data."""
    id: int
    application_id: int
    job_id: int
    job_title: str
    company_name: str
    location: Optional[str]
    salary_offered: Optional[str]
    start_date: Optional[str]
    status: str
    offer_letter_preview: Optional[str]  # First 500 chars
    nda_preview: Optional[str]  # First 500 chars
    sent_at: str
    expires_at: Optional[str]
    offer_signed: bool
    nda_signed: bool
    match_score: Optional[float]
    
    class Config:
        from_attributes = True


class AcceptOfferRequest(BaseModel):
    """Request model for accepting an offer."""
    sign_offer: bool = True
    sign_nda: bool = True
    confirm_start_date: bool = True


class DeclineOfferRequest(BaseModel):
    """Request model for declining an offer."""
    reason: Optional[str] = None


@router.get("")
def get_employee_offers(
    status: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> List[dict]:
    """
    Get all offers for the current employee.
    Optionally filter by status: pending, accepted, declined, expired
    """
    from sqlalchemy import text
    try:
        user_id = current_user.get("user_id")
        role = current_user.get("role")
        
        if role != "employee":
            raise HTTPException(status_code=403, detail="Only employees can view offers")
        
        # Get employee
        employee = db.query(Employee).filter(Employee.user_id == user_id).first()
        if not employee:
            return []
        
        # Use raw SQL to get offers and avoid enum validation issues
        query_sql = """
            SELECT 
                o.id, o.application_id, o.salary_offered, o.start_date,
                o.status, o.offer_letter_content, o.nda_content,
                o.sent_at, o.expires_at, o.offer_signed, o.nda_signed,
                a.job_id, a.match_score,
                j.title as job_title, j.location,
                e.company_name
            FROM offers o
            LEFT JOIN applications a ON o.application_id = a.id
            LEFT JOIN jobs j ON a.job_id = j.id
            LEFT JOIN employers e ON j.employer_id = e.id
            WHERE a.employee_id = :employee_id
        """
        
        params = {"employee_id": employee.id}
        
        if status:
            query_sql += " AND o.status = :status"
            params["status"] = status
        
        query_sql += " ORDER BY o.sent_at DESC"
        
        result_raw = db.execute(text(query_sql), params)
        
        result = []
        for row in result_raw.fetchall():
            (offer_id, app_id, salary, start_date, status_val, offer_letter, nda,
             sent_at, expires_at, offer_signed, nda_signed, job_id, match_score,
             job_title, location, company_name) = row
            
            # Handle datetime serialization
            result.append({
                "id": offer_id,
                "application_id": app_id,
                "job_id": job_id,
                "job_title": job_title or "Unknown",
                "company_name": company_name or "Unknown",
                "location": location,
                "salary_offered": salary,
                "start_date": start_date.isoformat() if hasattr(start_date, 'isoformat') and start_date else (str(start_date) if start_date else None),
                "status": status_val,
                "offer_letter_preview": offer_letter[:500] if offer_letter else None,
                "nda_preview": nda[:500] if nda else None,
                "sent_at": sent_at.isoformat() if hasattr(sent_at, 'isoformat') and sent_at else (str(sent_at) if sent_at else None),
                "expires_at": expires_at.isoformat() if hasattr(expires_at, 'isoformat') and expires_at else (str(expires_at) if expires_at else None),
                "offer_signed": bool(offer_signed),
                "nda_signed": bool(nda_signed),
                "match_score": match_score
            })
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching offers: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{offer_id}")
def get_offer_details(
    offer_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> dict:
    """Get detailed offer information including full document content."""
    from sqlalchemy import text
    try:
        user_id = current_user.get("user_id")
        role = current_user.get("role")
        
        # Use raw SQL to avoid enum validation issues
        query_sql = """
            SELECT 
                o.id, o.application_id, o.salary_offered, o.start_date,
                o.status, o.offer_letter_content, o.nda_content,
                o.sent_at, o.expires_at, o.responded_at,
                o.offer_signed, o.nda_signed, o.signed_at, o.additional_terms,
                a.job_id, a.employee_id, a.match_score,
                j.id as job_id_j, j.title, j.description, j.location, j.job_type, j.shift_type, j.employer_id,
                e.id as emp_id, e.full_name,
                emp.id as employer_id, emp.company_name, emp.industry
            FROM offers o
            LEFT JOIN applications a ON o.application_id = a.id
            LEFT JOIN jobs j ON a.job_id = j.id
            LEFT JOIN employees e ON a.employee_id = e.id
            LEFT JOIN employers emp ON j.employer_id = emp.id
            WHERE o.id = :offer_id
        """
        
        result = db.execute(text(query_sql), {"offer_id": offer_id}).fetchone()
        
        if not result:
            raise HTTPException(status_code=404, detail="Offer not found")
        
        # Unpack the result
        (offer_id_val, app_id, salary, start_date, status_val, offer_letter, nda,
         sent_at, expires_at, responded_at, offer_signed, nda_signed, signed_at, additional_terms,
         job_id, employee_id, match_score,
         job_id_j, job_title, job_desc, job_location, job_type, shift_type, employer_id_j,
         emp_id, emp_name,
         employer_id_emp, company_name, industry) = result
        
        # Verify access
        if role == "employee":
            employee = db.query(Employee).filter(Employee.user_id == user_id).first()
            if not employee or employee_id != employee.id:
                raise HTTPException(status_code=403, detail="Not authorized to view this offer")
        elif role == "employer":
            employer = db.query(Employer).filter(Employer.user_id == user_id).first()
            if not employer or employer_id_j != employer.id:
                raise HTTPException(status_code=403, detail="Not authorized to view this offer")
        
        return {
            "id": offer_id_val,
            "application_id": app_id,
            "job": {
                "id": job_id_j,
                "title": job_title or "Unknown",
                "description": job_desc,
                "location": job_location,
                "job_type": job_type,
                "shift_type": shift_type
            },
            "employer": {
                "company_name": company_name or "Unknown",
                "industry": industry
            },
            "employee": {
                "id": emp_id,
                "name": emp_name or "Unknown"
            },
            "offer_details": {
                "salary_offered": salary,
                "start_date": start_date.isoformat() if hasattr(start_date, 'isoformat') and start_date else (str(start_date) if start_date else None),
                "additional_terms": additional_terms
            },
            "documents": {
                "offer_letter": offer_letter,
                "nda": nda
            },
            "status": status_val,
            "signing": {
                "offer_signed": bool(offer_signed),
                "nda_signed": bool(nda_signed),
                "signed_at": signed_at.isoformat() if hasattr(signed_at, 'isoformat') and signed_at else (str(signed_at) if signed_at else None)
            },
            "timestamps": {
                "sent_at": sent_at.isoformat() if hasattr(sent_at, 'isoformat') and sent_at else (str(sent_at) if sent_at else None),
                "expires_at": expires_at.isoformat() if hasattr(expires_at, 'isoformat') and expires_at else (str(expires_at) if expires_at else None),
                "responded_at": responded_at.isoformat() if hasattr(responded_at, 'isoformat') and responded_at else (str(responded_at) if responded_at else None)
            },
            "match_score": match_score
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching offer details: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{offer_id}/accept")
def accept_offer(
    offer_id: int,
    request: AcceptOfferRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> dict:
    """
    Accept a job offer.
    
    This will:
    1. Update offer status to 'accepted'
    2. Mark documents as signed
    3. Update application status to OFFER_ACCEPTED then HIRED
    4. Create onboarding tasks
    5. Notify the employer
    """
    from sqlalchemy import text
    try:
        user_id = current_user.get("user_id")
        role = current_user.get("role")
        
        if role != "employee":
            raise HTTPException(status_code=403, detail="Only employees can accept offers")
        
        # Use raw SQL to get offer details and verify ownership
        query_sql = """
            SELECT 
                o.id, o.application_id, o.status,
                a.employee_id, a.job_id,
                j.title, j.employer_id,
                e.full_name,
                emp.company_name
            FROM offers o
            LEFT JOIN applications a ON o.application_id = a.id
            LEFT JOIN jobs j ON a.job_id = j.id
            LEFT JOIN employees e ON a.employee_id = e.id
            LEFT JOIN employers emp ON j.employer_id = emp.id
            WHERE o.id = :offer_id
        """
        
        result = db.execute(text(query_sql), {"offer_id": offer_id}).fetchone()
        
        if not result:
            raise HTTPException(status_code=404, detail="Offer not found")
        
        (offer_id_val, app_id, offer_status, 
         employee_id, job_id, 
         job_title, employer_id,
         employee_name, company_name) = result
        
        if offer_status != "pending":
            raise HTTPException(status_code=400, detail=f"Offer is already {offer_status}")
        
        # Verify this offer belongs to this employee
        employee = db.query(Employee).filter(Employee.user_id == user_id).first()
        if not employee or employee_id != employee.id:
            raise HTTPException(status_code=403, detail="Not authorized to accept this offer")
        
        now = datetime.utcnow()
        
        # 1. Update offer using direct SQL to avoid enum validation
        update_offer_sql = """
            UPDATE offers 
            SET status = 'accepted',
                responded_at = :now,
                offer_signed = :offer_signed,
                nda_signed = :nda_signed,
                signed_at = :signed_at
            WHERE id = :offer_id
        """
        
        db.execute(text(update_offer_sql), {
            "offer_id": offer_id,
            "now": now,
            "offer_signed": request.sign_offer,
            "nda_signed": request.sign_nda,
            "signed_at": now if (request.sign_offer or request.sign_nda) else None
        })
        
        # 2. Update application status using direct SQL
        update_app_sql = """
            UPDATE applications 
            SET status = :status,
                updated_at = :now
            WHERE id = :app_id
        """
        
        db.execute(text(update_app_sql), {
            "app_id": app_id,
            "status": ApplicationStatus.HIRED.value,  # Use .value to get the string
            "now": now
        })
        
        # 3. Update Job Position Count
        # Increment quantity_filled and deactivate job if full
        update_job_sql = """
            UPDATE jobs 
            SET quantity_filled = quantity_filled + 1,
                is_active = CASE 
                    WHEN quantity_filled + 1 >= quantity_needed THEN 0 
                    ELSE is_active 
                END,
                updated_at = :now
            WHERE id = :job_id
        """
        
        db.execute(text(update_job_sql), {
            "job_id": job_id,
            "now": now
        })
        
        # 3. Create onboarding tasks
        onboarding_tasks = [
            OnboardingTask(
                employee_id=employee.id,
                job_id=job_id,
                task_type=OnboardingTaskType.CHECKLIST,
                title="Complete First Day Orientation",
                description="Review company policies and complete orientation checklist",
                status=OnboardingTaskStatus.PENDING
            ),
            OnboardingTask(
                employee_id=employee.id,
                job_id=job_id,
                task_type=OnboardingTaskType.DOCUMENT_UPLOAD,
                title="Upload Required Documents",
                description="Upload ID proof and any required certifications",
                status=OnboardingTaskStatus.PENDING
            )
        ]
        
        for task in onboarding_tasks:
            db.add(task)
        
        # 4. Notify employer
        if employer_id:
            employer_user_sql = """
                SELECT u.id 
                FROM users u
                JOIN employers emp ON emp.user_id = u.id
                WHERE emp.id = :employer_id
            """
            employer_user_result = db.execute(text(employer_user_sql), {"employer_id": employer_id}).fetchone()
            
            if employer_user_result:
                employer_user_id = employer_user_result[0]
                notification = Notification(
                    recipient_id=employer_user_id,
                    title="🎉 Offer Accepted!",
                    message=f"{employee_name} has accepted the {job_title if job_title else 'position'} offer!",
                    notification_type="offer_accepted",
                    action_url="/employer/candidates",
                    meta_data={
                        "offer_id": offer_id,
                        "employee_id": employee.id,
                        "job_id": job_id
                    }
                )
                db.add(notification)
        
        db.commit()
        
        logger.info(f"✅ Offer {offer_id} accepted by employee {employee.id}")
        
        return {
            "success": True,
            "message": "Congratulations! You have successfully accepted the offer.",
            "offer_id": offer_id,
            "new_status": "accepted",
            "application_status": "hired",
            "next_steps": [
                "Complete your onboarding tasks",
                "Review your start date and location",
                "Contact your new employer if you have questions"
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error accepting offer: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{offer_id}/decline")
def decline_offer(
    offer_id: int,
    request: DeclineOfferRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> dict:
    """
    Decline a job offer.
    
    This will:
    1. Update offer status to 'declined'
    2. Update application status to OFFER_DECLINED
    3. Notify the employer
    """
    from sqlalchemy import text
    try:
        user_id = current_user.get("user_id")
        role = current_user.get("role")
        
        if role != "employee":
            raise HTTPException(status_code=403, detail="Only employees can decline offers")
        
        # Use raw SQL to get offer details and verify ownership
        query_sql = """
            SELECT 
                o.id, o.application_id, o.status,
                a.employee_id, a.job_id,
                j.title, j.employer_id,
                e.full_name,
                emp.company_name
            FROM offers o
            LEFT JOIN applications a ON o.application_id = a.id
            LEFT JOIN jobs j ON a.job_id = j.id
            LEFT JOIN employees e ON a.employee_id = e.id
            LEFT JOIN employers emp ON j.employer_id = emp.id
            WHERE o.id = :offer_id
        """
        
        result = db.execute(text(query_sql), {"offer_id": offer_id}).fetchone()
        
        if not result:
            raise HTTPException(status_code=404, detail="Offer not found")
        
        (offer_id_val, app_id, offer_status, 
         employee_id, job_id, 
         job_title, employer_id,
         employee_name, company_name) = result
        
        if offer_status != "pending":
            raise HTTPException(status_code=400, detail=f"Offer is already {offer_status}")
        
        # Verify ownership
        employee = db.query(Employee).filter(Employee.user_id == user_id).first()
        if not employee or employee_id != employee.id:
            raise HTTPException(status_code=403, detail="Not authorized to decline this offer")
        
        now = datetime.utcnow()
        
        # 1. Update offer status using direct SQL
        update_offer_sql = """
            UPDATE offers 
            SET status = 'declined',
                responded_at = :now
            WHERE id = :offer_id
        """
        
        db.execute(text(update_offer_sql), {
            "offer_id": offer_id,
            "now": now
        })
        
        # 2. Update application status using direct SQL
        update_app_sql = """
            UPDATE applications 
            SET status = :status,
                updated_at = :now
            WHERE id = :app_id
        """
        
        db.execute(text(update_app_sql), {
            "app_id": app_id,
            "status": ApplicationStatus.OFFER_DECLINED.value,
            "now": now
        })
        
        # 3. Re-open position slot and handle follow-up
        from backend.services.decline_followup_service import (
            reopen_position_slot, get_next_best_candidates, auto_send_next_offer
        )
        
        reopen_result = reopen_position_slot(db, job_id)
        next_candidates = get_next_best_candidates(db, job_id, exclude_employee_id=employee.id, limit=3)
        
        # Get job for auto-fill check
        job = db.query(Job).filter(Job.id == job_id).first()
        auto_fill_result = None
        
        # 4. Notify employer with suggestions
        if employer_id:
            employer_user_sql = """
                SELECT u.id 
                FROM users u
                JOIN employers emp ON emp.user_id = u.id
                WHERE emp.id = :employer_id
            """
            employer_user_result = db.execute(text(employer_user_sql), {"employer_id": employer_id}).fetchone()
            
            if employer_user_result:
                employer_user_id = employer_user_result[0]
                
                # Build enhanced message with suggestions
                message = f"{employee_name} has declined the {job_title if job_title else 'position'} offer."
                if next_candidates:
                    message += f" We've identified {len(next_candidates)} alternative candidate(s)."
                if reopen_result.get("job_reopened"):
                    message += " Position is now open again."
                
                notification = Notification(
                    recipient_id=employer_user_id,
                    title="Offer Declined",
                    message=message,
                    notification_type="offer_declined",
                    action_url="/employer/candidates",
                    meta_data={
                        "offer_id": offer_id,
                        "employee_id": employee.id,
                        "job_id": job_id,
                        "reason": request.reason,
                        "next_candidates": next_candidates,
                        "positions_available": reopen_result.get("positions_available", 0),
                        "job_reopened": reopen_result.get("job_reopened", False)
                    }
                )
                db.add(notification)
        
        # 5. Auto-fill if enabled
        if job and job.auto_fill_on_decline and next_candidates:
            auto_fill_result = auto_send_next_offer(db, job, next_candidates[0], employer_id)
            if auto_fill_result.get("success"):
                logger.info(f"🔄 Auto-filled position with {next_candidates[0]['name']}")
        
        db.commit()
        
        logger.info(f"❌ Offer {offer_id} declined by employee {employee.id}")
        
        response = {
            "success": True,
            "message": "Offer has been declined.",
            "offer_id": offer_id,
            "new_status": "declined",
            "position_reopened": reopen_result.get("job_reopened", False),
            "positions_available": reopen_result.get("positions_available", 0)
        }
        
        if auto_fill_result and auto_fill_result.get("success"):
            response["auto_filled"] = {
                "new_candidate": auto_fill_result["employee_name"],
                "offer_id": auto_fill_result["offer_id"]
            }
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error declining offer: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/employer/sent")
def get_employer_offers(
    status: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> List[dict]:
    """Get all offers sent by the employer."""
    try:
        user_id = current_user.get("user_id")
        role = current_user.get("role")
        
        if role != "employer":
            raise HTTPException(status_code=403, detail="Only employers can view sent offers")
        
        employer = db.query(Employer).filter(Employer.user_id == user_id).first()
        if not employer:
            return []
        
        # Get jobs for this employer
        job_ids = [job.id for job in db.query(Job).filter(Job.employer_id == employer.id).all()]
        
        # Get offers for these jobs
        query = db.query(Offer).join(Application).filter(
            Application.job_id.in_(job_ids)
        )
        
        if status:
            query = query.filter(Offer.status == status)
        
        offers = query.order_by(Offer.sent_at.desc()).all()
        
        result = []
        for offer in offers:
            app = offer.application
            job = db.query(Job).filter(Job.id == app.job_id).first()
            employee = db.query(Employee).filter(Employee.id == app.employee_id).first()
            
            result.append({
                "id": offer.id,
                "application_id": offer.application_id,
                "job_id": app.job_id,
                "job_title": job.title if job else "Unknown",
                "employee_name": employee.full_name if employee else "Unknown",
                "employee_id": employee.id if employee else None,
                "salary_offered": offer.salary_offered,
                "status": offer.status,
                "sent_at": offer.sent_at.isoformat() if offer.sent_at else None,
                "responded_at": offer.responded_at.isoformat() if offer.responded_at else None,
                "match_score": app.match_score
            })
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching employer offers: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
