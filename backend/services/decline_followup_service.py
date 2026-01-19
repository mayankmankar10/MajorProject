# backend/services/decline_followup_service.py
"""
Service for handling offer decline follow-up actions:
1. Re-opening position slots
2. Suggesting next-best candidates
3. Auto-sending offers to next candidate (if enabled)
"""

from sqlalchemy.orm import Session
from sqlalchemy import and_
from backend.db.models import (
    Job, Application, ApplicationStatus, Offer, Employee, 
    Employer, Notification, User
)
from datetime import datetime
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


def reopen_position_slot(db: Session, job_id: int) -> Dict:
    """
    Decrement quantity_filled and re-open job if needed.
    
    Returns:
        Dict with 'reopened' status and updated counts
    """
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        return {"success": False, "error": "Job not found"}
    
    previous_filled = job.quantity_filled
    was_active = job.is_active
    
    # Decrement filled count (never go below 0)
    if job.quantity_filled > 0:
        job.quantity_filled -= 1
    
    # Re-open job if there are now unfilled positions
    reopened = False
    if not job.is_active and job.quantity_filled < job.quantity_needed:
        job.is_active = True
        reopened = True
        logger.info(f"📋 Job {job_id} re-opened: {job.quantity_filled}/{job.quantity_needed} positions filled")
    
    return {
        "success": True,
        "job_id": job_id,
        "previous_filled": previous_filled,
        "current_filled": job.quantity_filled,
        "quantity_needed": job.quantity_needed,
        "positions_available": job.quantity_needed - job.quantity_filled,
        "job_reopened": reopened,
        "is_active": job.is_active
    }


def get_candidates_from_matching(
    db: Session,
    job_id: int,
    exclude_employee_id: int = None,
    limit: int = 3
) -> List[Dict]:
    """
    Fallback: Use matching tool to find fresh candidates dynamically.
    
    This is called when no existing applications are found.
    """
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            logger.warning(f"Job {job_id} not found for matching")
            return []
        
        # Import matching tool
        from backend.tools_langchain.matching_tool import MatchingTool
        
        
        # Build job description for matching (same format as bulk hire)
        # Use enhanced_description if available, otherwise fall back to description
        job_description = job.enhanced_description or job.description or f"{job.title}"
        
        # Run matching
        matching_tool = MatchingTool()
        result_str = matching_tool._run(
            query_text=job_description,
            match_type="job_to_candidates",
            top_k=limit + 5,  # Get extra in case we need to filter
            job_id=job_id
        )
        
        import json
        result = json.loads(result_str)
        
        if not result.get("success") or not result.get("matches"):
            logger.info(f"No matches found from matching tool for job {job_id}")
            return []
        
        # Convert matches to candidate format
        candidates = []
        for match in result["matches"][:limit]:
            employee_id = match["metadata"].get("employee_id") or match["metadata"].get("id")
            
            # Skip excluded employee
            if exclude_employee_id and employee_id == exclude_employee_id:
                continue
            
            employee = db.query(Employee).filter(Employee.id == employee_id).first()
            if employee:
                candidates.append({
                    "employee_id": employee.id,
                    "name": employee.full_name,
                    "match_score": round(match["final_score"] * 100),
                    "application_id": None,  # No application exists yet
                    "status": "matched",  # Special status for dynamically matched
                    "from_matching": True  # Flag to indicate this came from matching tool
                })
            
            if len(candidates) >= limit:
                break
        
        logger.info(f"🔍 Found {len(candidates)} candidates from matching tool for job {job_id}")
        return candidates
        
    except Exception as e:
        logger.error(f"❌ Matching tool fallback failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return []


def get_next_best_candidates(
    db: Session, 
    job_id: int, 
    exclude_employee_id: int = None,
    limit: int = 3
) -> List[Dict]:
    """
    Get top candidates - tries existing applications first, falls back to matching tool.
    
    Args:
        db: Database session
        job_id: The job to find candidates for
        exclude_employee_id: Employee who just declined (exclude from suggestions)
        limit: Max number of candidates to return
        
    Returns:
        List of candidate dicts with id, name, match_score, status
    """
    # PHASE 1: Try existing applications first
    eligible_statuses = [
        ApplicationStatus.APPLIED,
        ApplicationStatus.REVIEWING,
        ApplicationStatus.SHORTLISTED,
        ApplicationStatus.INTERVIEW_SCHEDULED,
        ApplicationStatus.SELECTED
    ]
    
    query = db.query(Application).filter(
        Application.job_id == job_id,
        Application.status.in_(eligible_statuses)
    )
    
    if exclude_employee_id:
        query = query.filter(Application.employee_id != exclude_employee_id)
    
    # Order by match score descending
    applications = query.order_by(Application.match_score.desc()).limit(limit).all()
    
    candidates = []
    for app in applications:
        employee = db.query(Employee).filter(Employee.id == app.employee_id).first()
        if employee:
            candidates.append({
                "employee_id": employee.id,
                "name": employee.full_name,
                "match_score": round((app.match_score or 0) * 100),
                "application_id": app.id,
                "status": app.status.value if hasattr(app.status, 'value') else str(app.status),
                "from_matching": False
            })
    
    if len(candidates) > 0:
        logger.info(f"🎯 Found {len(candidates)} next-best candidates from existing applications for job {job_id}")
        return candidates
    
    # PHASE 2: Fallback to matching tool if no applications found
    logger.info(f"⚡ No existing applications found, using matching tool fallback for job {job_id}")
    return get_candidates_from_matching(db, job_id, exclude_employee_id, limit)


def auto_send_next_offer(
    db: Session,
    job: Job,
    next_candidate: Dict,
    employer_id: int
) -> Dict:
    """
    Automatically send an offer to the next best candidate.
    
    Args:
        db: Database session
        job: The Job object
        next_candidate: Candidate dict from get_next_best_candidates()
        employer_id: Employer ID for notifications
        
    Returns:
        Dict with success status and offer details
    """
    try:
        # Handle candidates from matching tool (no existing application)
        if next_candidate.get("from_matching"):
            # Create application for this candidate
            employee = db.query(Employee).filter(Employee.id == next_candidate["employee_id"]).first()
            if not employee:
                return {"success": False, "error": "Employee not found"}
            
            # Create new application
            now = datetime.utcnow()
            application = Application(
                employee_id=employee.id,
                job_id=job.id,
                status=ApplicationStatus.OFFER_SENT,
                match_score=next_candidate["match_score"] / 100.0,  # Convert back to 0-1 scale
                applied_at=now,
                updated_at=now
            )
            db.add(application)
            db.flush()  # Get application ID
            logger.info(f"📝 Created application {application.id} for employee {employee.id} (from matching)")
        else:
            # Existing application path
            application = db.query(Application).filter(
                Application.id == next_candidate["application_id"]
            ).first()
            
            if not application:
                return {"success": False, "error": "Application not found"}
        
        # Check if offer already exists for this application
        existing_offer = db.query(Offer).filter(
            Offer.application_id == application.id
        ).first()
        
        if existing_offer:
            return {"success": False, "error": "Offer already exists for this application"}
        
        employee = db.query(Employee).filter(Employee.id == application.employee_id).first()
        employer = db.query(Employer).filter(Employer.id == employer_id).first()
        
        if not employee or not employer:
            return {"success": False, "error": "Employee or employer not found"}
        
        now = datetime.utcnow()
        
        # Update application status
        application.status = ApplicationStatus.OFFER_SENT
        application.updated_at = now
        
        # Create new offer
        offer = Offer(
            application_id=application.id,
            salary_offered=job.salary_range or "Competitive",
            additional_terms={
                "auto_filled": True,
                "original_decline_date": now.isoformat(),
                "job_type": job.title
            },
            status="pending",
            sent_at=now
        )
        db.add(offer)
        db.flush()  # Get offer ID
        
        # Increment quantity_filled since we're sending a new offer
        job.quantity_filled += 1
        
        # Notify the employee
        notification = Notification(
            recipient_id=employee.user_id,
            title="🎉 Job Offer Received!",
            message=f"Great news! You've received an offer for the {job.title} position at {employer.company_name}. Review and respond now!",
            notification_type="offer_received",
            action_url="/employee/offers",
            meta_data={
                "offer_id": offer.id,
                "job_id": job.id,
                "auto_filled": True
            }
        )
        db.add(notification)
        
        
        # Generate offer documents (offer letter and NDA)
        try:
            from backend.tools_langchain.ollama_document_generator import OllamaDocumentGenerator
            doc_generator = OllamaDocumentGenerator()
            
            # Generate offer letter
            offer_letter = doc_generator._run(
                document_type="offer_letter",
                application_id=application.id
            )
            
            # Generate NDA
            nda = doc_generator._run(
                document_type="nda",
                application_id=application.id
            )
            
            logger.info(f"📄 Generated documents for auto-filled offer {offer.id}")
        except Exception as doc_error:
            logger.warning(f"⚠️ Document generation failed for auto-filled offer: {doc_error}")
            # Don't fail the whole auto-fill if document generation fails
        
        # Notify the employer
        employer_user = db.query(User).filter(User.id == employer.user_id).first()
        if employer_user:
            employer_notification = Notification(
                recipient_id=employer_user.id,
                title="📤 Auto-Sent Offer",
                message=f"An offer for {job.title} was automatically sent to {employee.full_name} (Match: {next_candidate['match_score']}%) after the previous candidate declined.",
                notification_type="auto_offer_sent",
                action_url="/employer/candidates",
                meta_data={
                    "offer_id": offer.id,
                    "employee_id": employee.id,
                    "job_id": job.id
                }
            )
            db.add(employer_notification)
        
        logger.info(f"📤 Auto-sent offer {offer.id} to employee {employee.id} for job {job.id}")
        
        return {
            "success": True,
            "offer_id": offer.id,
            "employee_id": employee.id,
            "employee_name": employee.full_name,
            "match_score": next_candidate["match_score"]
        }
        
    except Exception as e:
        logger.error(f"❌ Auto-send offer failed: {str(e)}")
        return {"success": False, "error": str(e)}
