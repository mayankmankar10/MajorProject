# backend/tools_langchain/offer_acceptance_tool.py
"""
Offer Acceptance Tool - Allows employees to accept or decline job offers via chat.
Part of the autonomous hiring pipeline.
"""

from langchain.tools import BaseTool
from typing import Type, Optional
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy.orm import Session
from backend.db.sql_db import SessionLocal
from backend.db.models import (
    Offer, Application, ApplicationStatus, Job, Employee, Employer, 
    User, Notification, OnboardingTask, OnboardingTaskType, OnboardingTaskStatus
)
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)


class OfferAcceptanceInput(BaseModel):
    """Input schema for OfferAcceptanceTool."""
    employee_id: int = Field(description="The employee's ID")
    action: str = Field(description="Action to take: 'list' (view offers), 'compare' (compare all offers), 'accept', or 'decline'")
    offer_id: Optional[int] = Field(
        default=None, 
        description="Specific offer ID. If not provided, acts on the most recent pending offer."
    )
    reason: Optional[str] = Field(
        default=None, 
        description="Optional reason for declining (only used when action='decline')"
    )



class OfferAcceptanceTool(BaseTool):
    """
    Tool for employees to accept or decline job offers through chat.
    
    Capabilities:
    - View pending offers
    - Accept an offer (auto-signs documents, transitions to HIRED)
    - Decline an offer (notifies employer)
    
    Use this when an employee wants to respond to a job offer they received.
    """
    name: str = "OfferAcceptanceTool"
    description: str = """
    View, review, compare, accept, or decline job offers that employers have sent you.
    
    Actions:
    - 'list': View comprehensive details of all pending offers with deep job insights
    - 'compare': Compare all offers side-by-side with recommendations
    - 'accept': Accept an offer (generates offer letter & NDA upon acceptance)
    - 'decline': Decline an offer
    
    Input:
    - employee_id: The employee's ID (required)
    - action: 'list', 'compare', 'accept', or 'decline'
    - offer_id: (optional) Specific offer ID for accept/decline, defaults to most recent
    - reason: (optional) Reason for declining
    
    IMPORTANT: Use this tool when employee asks about OFFERS that companies sent them.
    Do NOT use ApplicationStatusTool for reviewing offers - use this tool instead!
    
    Use when employee says things like:
    - "Review the offer from Nike" → action='list'
    - "Show my pending offers" → action='list'
    - "Compare my offers" / "Compare Nike vs Lebanese Bar" → action='compare'
    - "What offers do I have?" → action='list'
    - "Accept my offer" / "I accept the job" → action='accept'
    - "Decline the offer" / "Turn down the job" → action='decline'
    
    Returns comprehensive job details, insights, and next steps.
    """
    args_schema: Type[BaseModel] = OfferAcceptanceInput
    
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    def _run(self, employee_id: int, action: str, offer_id: int = None, reason: str = None) -> str:
        """Execute offer review, comparison, acceptance, or decline."""
        db = SessionLocal()
        
        try:
            # Get employee
            employee = db.query(Employee).filter(Employee.id == employee_id).first()
            if not employee:
                return json.dumps({
                    "success": False,
                    "error": f"Employee {employee_id} not found"
                })
            
            # Handle list action (deep review)
            if action.lower() == "list":
                return self._list_offers(db, employee)
            
            # Handle compare action
            if action.lower() == "compare":
                return self._compare_offers(db, employee)
            
            # For accept/decline actions, get the offer
            if offer_id:
                offer = db.query(Offer).filter(Offer.id == offer_id).first()
            else:
                # Get most recent pending offer
                offer = db.query(Offer).join(Application).filter(
                    Application.employee_id == employee_id,
                    Offer.status == "pending"
                ).order_by(Offer.sent_at.desc()).first()
            
            if not offer:
                return json.dumps({
                    "success": False,
                    "error": "No pending offer found",
                    "suggestion": "You can ask to see your pending offers or apply to new jobs."
                })
            
            # Verify ownership
            app = offer.application
            if app.employee_id != employee_id:
                return json.dumps({
                    "success": False,
                    "error": "This offer doesn't belong to you"
                })
            
            if offer.status != "pending":
                return json.dumps({
                    "success": False,
                    "error": f"This offer has already been {offer.status}"
                })
            
            # Get job and employer info
            job = db.query(Job).filter(Job.id == app.job_id).first()
            employer = db.query(Employer).filter(Employer.id == job.employer_id).first() if job else None
            
            now = datetime.utcnow()
            
            if action.lower() == "accept":
                return self._accept_offer(db, offer, app, employee, job, employer, now)
            elif action.lower() == "decline":
                return self._decline_offer(db, offer, app, employee, job, employer, now, reason)
            else:
                return json.dumps({
                    "success": False,
                    "error": f"Unknown action: {action}. Use 'list', 'compare', 'accept', or 'decline'"
                })
                
        except Exception as e:
            logger.error(f"OfferAcceptanceTool error: {str(e)}")
            db.rollback()
            return json.dumps({
                "success": False,
                "error": str(e)
            })
        finally:
            db.close()
    
    def _list_offers(self, db: Session, employee: Employee) -> str:
        """List all pending offers with comprehensive job details for deep review."""
        offers = db.query(Offer).join(Application).filter(
            Application.employee_id == employee.id,
            Offer.status == "pending"
        ).order_by(Offer.sent_at.desc()).all()
        
        if not offers:
            return json.dumps({
                "success": True,
                "message": "You have no pending job offers at the moment.",
                "pending_offers": 0,
                "suggestion": "Keep applying to jobs that match your skills!"
            })
        
        offer_list = []
        for offer in offers:
            app = offer.application
            job = db.query(Job).filter(Job.id == app.job_id).first()
            employer = db.query(Employer).filter(Employer.id == job.employer_id).first() if job else None
            
            # Build comprehensive offer details
            offer_details = {
                "offer_id": offer.id,
                "company_name": employer.company_name if employer else "Unknown",
                "company_industry": employer.industry if employer else None,
                "company_location": employer.location if employer else None,
                
                # Job details
                "job_title": job.title if job else "Unknown",
                "job_description": job.description if job else None,
                "job_location": job.location if job else None,
                "job_type": job.job_type if job else None,
                "shift_type": job.shift_type if job else None,
                "cuisine_type": job.cuisine_type if job else None,
                
                # Compensation
                "salary_offered": offer.salary_offered,
                "salary_range": job.salary_range if job else None,
                
                # Requirements
                "requires_food_safety": job.requires_food_safety if job else None,
                "requires_alcohol_cert": job.requires_alcohol_cert if job else None,
                "min_experience_years": job.min_hospitality_experience if job else None,
                
                # Match and timing
                "match_score": f"{int((app.match_score or 0) * 100)}%",
                "match_score_raw": app.match_score or 0,
                "sent_at": offer.sent_at.strftime("%B %d, %Y at %I:%M %p") if offer.sent_at else None,
                "days_pending": (datetime.utcnow() - offer.sent_at).days if offer.sent_at else 0,
                
                # Additional terms
                "additional_terms": offer.additional_terms or {},
                
                # Positions
                "positions_total": job.quantity_needed if job else None,
                "positions_filled": job.quantity_filled if job else None,
                "positions_available": (job.quantity_needed - job.quantity_filled) if (job and job.quantity_needed and job.quantity_filled is not None) else None
            }
            
            offer_list.append(offer_details)
        
        # Provide insights
        insights = []
        if len(offers) > 1:
            # Sort by match score
            sorted_offers = sorted(offer_list, key=lambda x: x["match_score_raw"], reverse=True)
            best_match = sorted_offers[0]
            insights.append(f"🌟 Best match: {best_match['job_title']} at {best_match['company_name']} ({best_match['match_score']})")
            
            # Check for urgent offers (older than 3 days)
            urgent = [o for o in offer_list if o["days_pending"] > 3]
            if urgent:
                insights.append(f"⏰ {len(urgent)} offer(s) pending for 3+ days - consider responding soon")
        
        return json.dumps({
            "success": True,
            "message": f"You have {len(offers)} pending offer(s) with detailed information below.",
            "pending_offers": len(offers),
            "offers": offer_list,
            "insights": insights,
            "actions_available": [
                "Say 'compare my offers' to see a side-by-side comparison",
                "Say 'accept offer from [company name]' to accept",
                "Say 'decline offer from [company name]' to decline"
            ]
        })
    
    def _compare_offers(self, db: Session, employee: Employee) -> str:
        """Compare all pending offers side-by-side."""
        offers = db.query(Offer).join(Application).filter(
            Application.employee_id == employee.id,
            Offer.status == "pending"
        ).order_by(Application.match_score.desc()).all()
        
        if len(offers) < 2:
            return json.dumps({
                "success": False,
                "message": "You need at least 2 pending offers to compare. You currently have {} offer(s).".format(len(offers)),
                "suggestion": "Use 'list' action to view your offer details."
            })
        
        comparison = {
            "total_offers": len(offers),
            "comparison_table": [],
            "recommendations": []
        }
        
        for offer in offers:
            app = offer.application
            job = db.query(Job).filter(Job.id == app.job_id).first()
            employer = db.query(Employer).filter(Employer.id == job.employer_id).first() if job else None
            
            comparison["comparison_table"].append({
                "company": employer.company_name if employer else "Unknown",
                "job_title": job.title if job else "Unknown",
                "match_score": f"{int((app.match_score or 0) * 100)}%",
                "salary": offer.salary_offered or "Not specified",
                "location": job.location if job else "Not specified",
                "shift_type": job.shift_type or "Not specified",
                "cuisine_type": job.cuisine_type or "Not specified",
                "positions_available": (job.quantity_needed - job.quantity_filled) if (job and job.quantity_needed and job.quantity_filled is not None) else "Unknown",
                "food_safety_required": "Yes" if (job and job.requires_food_safety) else "No",
                "days_pending": (datetime.utcnow() - offer.sent_at).days if offer.sent_at else 0
            })
        
        # Generate recommendations
        sorted_by_match = sorted(comparison["comparison_table"], key=lambda x: float(x["match_score"].rstrip('%')), reverse=True)
        best_match = sorted_by_match[0]
        comparison["recommendations"].append(
            f"🎯 Best fit: {best_match['job_title']} at {best_match['company']} with {best_match['match_score']} compatibility"
        )
        
        # Check for urgency
        oldest = max(comparison["comparison_table"], key=lambda x: x["days_pending"])
        if oldest["days_pending"] > 5:
            comparison["recommendations"].append(
                f"⏰ Urgent: {oldest['company']}'s offer has been pending for {oldest['days_pending']} days"
            )
        
        # Location insights
        locations = set(o["location"] for o in comparison["comparison_table"] if o["location"] != "Not specified")
        if len(locations) > 1:
            comparison["recommendations"].append(
                f"📍 Multiple locations available: {', '.join(locations)}"
            )
        
        return json.dumps({
            "success": True,
            "message": f"Comparing {len(offers)} job offers side-by-side",
            "comparison": comparison,
            "next_steps": "Review the comparison above and say 'accept offer from [company]' when ready"
        })
    
    
    def _accept_offer(self, db: Session, offer: Offer, app: Application, 
                      employee: Employee, job: Job, employer: Employer, now: datetime) -> str:
        """Accept the offer and trigger onboarding."""
        
        # Update offer
        offer.status = "accepted"
        offer.responded_at = now
        offer.offer_signed = True
        offer.nda_signed = True
        offer.signed_at = now
        
        # Update application status
        app.status = ApplicationStatus.HIRED
        app.updated_at = now
        
        # Create onboarding tasks
        onboarding_tasks = [
            OnboardingTask(
                employee_id=employee.id,
                job_id=job.id if job else app.job_id,
                task_type=OnboardingTaskType.CHECKLIST,
                title="Complete First Day Orientation",
                description="Review company policies and complete orientation checklist",
                status=OnboardingTaskStatus.PENDING
            ),
            OnboardingTask(
                employee_id=employee.id,
                job_id=job.id if job else app.job_id,
                task_type=OnboardingTaskType.DOCUMENT_UPLOAD,
                title="Upload Required Documents",
                description="Upload ID proof and any required certifications",
                status=OnboardingTaskStatus.PENDING
            )
        ]
        
        for task in onboarding_tasks:
            db.add(task)
        
        # Notify employer
        if employer:
            employer_user = db.query(User).filter(User.id == employer.user_id).first()
            if employer_user:
                notification = Notification(
                    recipient_id=employer_user.id,
                    title="🎉 Offer Accepted!",
                    message=f"{employee.full_name} has accepted the {job.title if job else 'position'} offer!",
                    notification_type="offer_accepted",
                    action_url="/employer/candidates",
                    meta_data={
                        "offer_id": offer.id,
                        "employee_id": employee.id,
                        "job_id": job.id if job else None
                    }
                )
                db.add(notification)
        
        db.commit()
        
        logger.info(f"✅ Employee {employee.id} accepted offer {offer.id}")
        
        return json.dumps({
            "success": True,
            "message": f"🎉 Congratulations! You've accepted the {job.title if job else 'position'} role at {employer.company_name if employer else 'the company'}!",
            "status": "hired",
            "offer_id": offer.id,
            "company": employer.company_name if employer else "Unknown",
            "job_title": job.title if job else "Unknown",
            "documents_signed": {
                "offer_letter": True,
                "nda": True
            },
            "next_steps": [
                "✅ Your documents have been digitally signed",
                "📋 Complete your onboarding tasks in the Onboarding section",
                "📅 Review your start date and location",
                "📞 Your new employer will contact you with more details"
            ]
        })
    
    def _decline_offer(self, db: Session, offer: Offer, app: Application,
                       employee: Employee, job: Job, employer: Employer, 
                       now: datetime, reason: str = None) -> str:
        """Decline the offer with follow-up actions."""
        from backend.services.decline_followup_service import (
            reopen_position_slot, get_next_best_candidates, auto_send_next_offer
        )
        
        # Update offer
        offer.status = "declined"
        offer.responded_at = now
        
        # Update application status
        app.status = ApplicationStatus.OFFER_DECLINED
        app.updated_at = now
        
        # Re-open position slot
        reopen_result = {}
        if job:
            reopen_result = reopen_position_slot(db, job.id)
        
        # Get next best candidates
        next_candidates = []
        if job:
            next_candidates = get_next_best_candidates(db, job.id, exclude_employee_id=employee.id, limit=3)
        
        auto_fill_result = None
        
        # Notify employer with suggestions
        if employer:
            employer_user = db.query(User).filter(User.id == employer.user_id).first()
            if employer_user:
                # Build enhanced message
                message = f"{employee.full_name} has declined the {job.title if job else 'position'} offer."
                if next_candidates:
                    message += f" We've identified {len(next_candidates)} alternative candidate(s)."
                if reopen_result.get("job_reopened"):
                    message += " Position is now open again."
                
                notification = Notification(
                    recipient_id=employer_user.id,
                    title="Offer Declined",
                    message=message,
                    notification_type="offer_declined",
                    action_url="/employer/candidates",
                    meta_data={
                        "offer_id": offer.id,
                        "employee_id": employee.id,
                        "job_id": job.id if job else None,
                        "reason": reason,
                        "next_candidates": next_candidates,
                        "positions_available": reopen_result.get("positions_available", 0),
                        "job_reopened": reopen_result.get("job_reopened", False)
                    }
                )
                db.add(notification)
        
        # Auto-fill if enabled
        if job and job.auto_fill_on_decline and next_candidates and employer:
            auto_fill_result = auto_send_next_offer(db, job, next_candidates[0], employer.id)
            if auto_fill_result.get("success"):
                logger.info(f"🔄 Auto-filled position with {next_candidates[0]['name']}")
        
        db.commit()
        
        logger.info(f"❌ Employee {employee.id} declined offer {offer.id}")
        
        response = {
            "success": True,
            "message": f"You've declined the {job.title if job else 'position'} offer from {employer.company_name if employer else 'the employer'}.",
            "status": "declined",
            "offer_id": offer.id,
            "next_steps": [
                "No worries! You can continue exploring other opportunities",
                "Check the Job Search page for more positions",
                "Your profile is still visible to other employers"
            ]
        }
        
        if reopen_result.get("job_reopened"):
            response["position_info"] = f"The position is now open again with {reopen_result.get('positions_available', 0)} spot(s) available."
        
        return json.dumps(response)
    
    async def _arun(self, employee_id: int, action: str, offer_id: int = None, reason: str = None) -> str:
        """Async wrapper."""
        return self._run(employee_id, action, offer_id, reason)
