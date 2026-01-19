"""
Bulk Hire Routes - API endpoints for bulk hiring from existing jobs
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.db.sql_db import get_db
from backend.db.models import Job, Application, Offer, Employee, Employer, User, Notification
from pydantic import BaseModel
from typing import List
import logging
import json
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter()


# Request/Response Models
class BulkHireInitiateRequest(BaseModel):
    job_id: int
    quantity: int


class CandidateMatch(BaseModel):
    id: int
    name: str
    base_score: float
    bonus_score: float
    final_score: float
    skills: List[str]
    experience_years: int
    cuisine_experience: List[str] = []
    shift_preferences: List[str] = []


class BulkHireInitiateResponse(BaseModel):
    success: bool
    job_title: str
    job_id: int
    quantity_requested: int
    matches: List[CandidateMatch]
    total_matches: int


class CandidateSelection(BaseModel):
    employee_id: int
    score: float


class BulkHireConfirmRequest(BaseModel):
    job_id: int
    candidates: List[CandidateSelection]  # Changed from employee_ids to candidates with scores


class BulkHireConfirmResponse(BaseModel):
    success: bool
    message: str
    total_hired: int
    applications_created: int
    offers_sent: int
    job_title: str
    candidates: List[dict]


# Multi-Job Bulk Hire Models
class JobSelection(BaseModel):
    job_id: int
    quantity: int


class MultiJobInitiateRequest(BaseModel):
    job_selections: List[JobSelection]


class JobCandidates(BaseModel):
    job_id: int
    job_title: str
    quantity_requested: int
    candidates: List[CandidateMatch]


class MultiJobInitiateResponse(BaseModel):
    success: bool
    total_positions: int
    jobs_count: int
    matches_by_job: List[JobCandidates]


class JobEmployeeSelection(BaseModel):
    job_id: int
    candidates: List[CandidateSelection]  # Changed to include scores


class MultiJobConfirmRequest(BaseModel):
    selections: List[JobEmployeeSelection]


class JobHireResult(BaseModel):
    job_id: int
    job_title: str
    hired_count: int
    candidates: List[dict]


class MultiJobConfirmResponse(BaseModel):
    success: bool
    message: str
    total_hired: int
    jobs_processed: int
    results_by_job: List[JobHireResult]


@router.get("/jobs")
async def get_employer_jobs(user_id: int, db: Session = Depends(get_db)):
    """
    Get all active jobs for an employer that have remaining positions.
    """
    try:
        # Get employer from user_id
        employer = db.query(Employer).filter(Employer.user_id == user_id).first()
        if not employer:
            raise HTTPException(status_code=404, detail="Employer not found")
        
        # Get active jobs with remaining positions
        jobs = db.query(Job).filter(
            Job.employer_id == employer.id,
            Job.is_active == True,
            Job.quantity_filled < Job.quantity_needed
        ).all()
        
        result = []
        for job in jobs:
            result.append({
                "id": job.id,
                "title": job.title,
                "location": job.location,
                "job_category": job.job_category.value if job.job_category else None,
                "cuisine_type": job.cuisine_type,
                "shift_type": job.shift_type,
                "quantity_needed": job.quantity_needed,
                "quantity_filled": job.quantity_filled,
                "remaining": job.quantity_needed - job.quantity_filled,
                "salary_range": job.salary_range
            })
        
        return {
            "success": True,
            "jobs": result,
            "total": len(result)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching employer jobs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/initiate", response_model=BulkHireInitiateResponse)
async def initiate_bulk_hire(request: BulkHireInitiateRequest, db: Session = Depends(get_db)):
    """
    Initiate bulk hiring by matching candidates for a specific job.
    Returns matched candidates with scores for employer review.
    """
    try:
        # Fetch job details
        job = db.query(Job).filter(Job.id == request.job_id).first()
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Validate quantity
        remaining = job.quantity_needed - job.quantity_filled
        if request.quantity > remaining:
            raise HTTPException(
                status_code=400, 
                detail=f"Requested quantity ({request.quantity}) exceeds remaining positions ({remaining})"
            )
        
        if request.quantity < 1:
            raise HTTPException(status_code=400, detail="Quantity must be at least 1")
        
        # Use MatchingTool to find candidates
        from backend.tools_langchain.matching_tool import MatchingTool
        
        matcher = MatchingTool()
        
        # Get 3x candidates for better selection
        top_k = request.quantity * 3
        
        logger.info(f"🎯 Matching candidates for job {job.id} ({job.title}), quantity: {request.quantity}")
        
        match_result = json.loads(await matcher._arun(
            query_text=job.enhanced_description or job.description,
            match_type="job_to_candidates",
            top_k=top_k,
            job_id=job.id,  # Pass job_id for bonus scoring
            shift_requirements=[job.shift_type] if job.shift_type else None,
            role=job.job_category.value if job.job_category else None
        ))
        
        if not match_result.get("success"):
            raise HTTPException(status_code=500, detail="Matching failed")
        
        # Format candidates for response
        candidates = []
        for match in match_result.get("matches", []):
            employee_id = match.get("id")
            employee = db.query(Employee).filter(Employee.id == employee_id).first()
            
            if employee:
                candidates.append(CandidateMatch(
                    id=employee.id,
                    name=employee.full_name,
                    base_score=match.get("base_score", 0),
                    bonus_score=match.get("bonus_score", 0),
                    final_score=match.get("final_score", 0),
                    skills=employee.skills if employee.skills else [],
                    experience_years=employee.years_in_hospitality or 0,
                    cuisine_experience=employee.cuisine_experience if employee.cuisine_experience else [],
                    shift_preferences=employee.shift_preferences if employee.shift_preferences else []
                ))
        
        logger.info(f"✅ Found {len(candidates)} matching candidates")
        
        return BulkHireInitiateResponse(
            success=True,
            job_title=job.title,
            job_id=job.id,
            quantity_requested=request.quantity,
            matches=candidates,
            total_matches=len(candidates)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error initiating bulk hire: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/confirm", response_model=BulkHireConfirmResponse)
async def confirm_bulk_hire(request: BulkHireConfirmRequest, db: Session = Depends(get_db)):
    """
    Confirm bulk hire by creating applications, offers, and sending notifications.
    Updates database with all hiring records.
    """
    try:
        # Fetch job
        job = db.query(Job).filter(Job.id == request.job_id).first()
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        logger.info(f"📋 Confirming bulk hire for job {job.id}: {len(request.candidates)} candidates")
        
        # Validate: Check available positions
        available_positions = job.quantity_needed - job.quantity_filled
        if len(request.candidates) > available_positions:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot hire {len(request.candidates)} candidates. Only {available_positions} position(s) available (needed: {job.quantity_needed}, filled: {job.quantity_filled})"
            )
        
        applications_created = 0
        offers_sent = 0
        candidates_hired = []
        
        # Import tools
        from backend.tools_langchain.ollama_document_generator import OllamaDocumentGenerator
        from backend.tools_langchain.notification_tool import NotificationTool
        
        doc_generator = OllamaDocumentGenerator()
        notifier = NotificationTool()
        
        # First pass: Create all applications
        applications_to_process = []
        for candidate in request.candidates:
            employee_id = candidate.employee_id
            match_score = candidate.score
            
            employee = db.query(Employee).filter(Employee.id == employee_id).first()
            if not employee:
                logger.warning(f"Employee {employee_id} not found, skipping")
                continue
            
            # Check for existing application
            existing_app = db.query(Application).filter(
                Application.employee_id == employee_id,
                Application.job_id == job.id
            ).first()
            
            if existing_app:
                # Update existing application
                existing_app.status = "offer_sent"
                existing_app.match_score = match_score  # Update score
                existing_app.updated_at = datetime.utcnow()
                application = existing_app
                logger.info(f"  Updated existing application for {employee.full_name}")
            else:
                # Create new application
                application = Application(
                    job_id=job.id,
                    employee_id=employee_id,
                    status="offer_sent",
                    match_score=match_score,  # Store score
                    applied_at=datetime.utcnow()
                )
                db.add(application)
                db.flush()  # Get application.id
                applications_created += 1
                logger.info(f"  Created new application for {employee.full_name}")
            
            # Check if offer already exists
            existing_offer = db.query(Offer).filter(
                Offer.application_id == application.id
            ).first()
            
            if not existing_offer:
                applications_to_process.append({
                    'application': application,
                    'employee': employee,
                    'employee_id': employee_id,
                    'match_score': match_score
                })
        
        # Commit applications before generating documents
        db.commit()
        
        # Second pass: Generate all documents in parallel
        if applications_to_process:
            logger.info(f"  Generating documents for {len(applications_to_process)} candidates in parallel...")
            
            async def generate_documents_for_candidate(app_data):
                """Generate offer letter and NDA for a single candidate"""
                try:
                    employee_id = app_data['employee_id']
                    application = app_data['application']
                    employee = app_data['employee']
                    
                    # Generate both documents in parallel
                    from datetime import datetime, timedelta
                    
                    # Prepare complete context data
                    context_data = {
                        "candidate_name": employee.full_name,
                        "company_name": job.employer.company_name if job.employer else "Nike",
                        "job_title": job.title,
                        "salary": job.salary_range,
                        "location": job.location,
                        "start_date": (datetime.utcnow() + timedelta(days=14)).strftime("%B %d, %Y")
                    }
                    
                    offer_letter, nda = await asyncio.gather(
                        doc_generator._arun(
                            employee_id=employee_id,
                            job_id=job.id,
                            document_type="offer_letter",
                            context_data=json.dumps(context_data)
                        ),
                        doc_generator._arun(
                            employee_id=employee_id,
                            job_id=job.id,
                            document_type="nda",
                            context_data=json.dumps(context_data)
                        )
                    )
                    
                    # Parse JSON responses and extract content
                    offer_letter_data = json.loads(offer_letter)
                    nda_data = json.loads(nda)
                    
                    return {
                        'success': True,
                        'application': application,
                        'employee': employee,
                        'offer_letter': offer_letter_data.get('content', offer_letter),
                        'nda': nda_data.get('content', nda)
                    }
                except Exception as e:
                    logger.error(f"  Error generating documents for {employee.full_name}: {e}")
                    return {
                        'success': False,
                        'employee': employee,
                        'error': str(e)
                    }
            
            # Generate all documents in parallel
            import asyncio
            results = await asyncio.gather(*[
                generate_documents_for_candidate(app_data) 
                for app_data in applications_to_process
            ])
            
            # Third pass: Create offers and send notifications
            for result, app_data in zip(results, applications_to_process):
                if result['success']:
                    # Create offer
                    offer = Offer(
                        application_id=result['application'].id,
                        offer_letter_content=result['offer_letter'],
                        nda_content=result['nda'],
                        salary_offered=job.salary_range,
                        status="pending"
                    )
                    db.add(offer)
                    offers_sent += 1
                    logger.info(f"  Created offer for {result['employee'].full_name}")
                    
                    # Send notification
                    try:
                        await notifier._arun(
                            user_id=result['employee'].user_id,
                            title="Job Offer Received!",
                            message=f"Congratulations! You've received an offer for the {job.title} role at {job.employer.company_name if job.employer else 'Nike'}. Match: {int(app_data['match_score'])}%. Review and accept your offer now!",
                            notification_type="offer_received"
                        )
                    except Exception as e:
                        logger.warning(f"  Failed to send notification to {result['employee'].full_name}: {e}")
                    
                    candidates_hired.append({
                        "id": result['employee'].id,
                        "name": result['employee'].full_name
                    })
        
        # Update job quantity
        job.quantity_filled = min(job.quantity_filled + len(candidates_hired), job.quantity_needed)
        
        # Commit all changes
        db.commit()
        
        logger.info(f"✅ Bulk hire complete: {applications_created} applications, {offers_sent} offers")
        
        return BulkHireConfirmResponse(
            success=True,
            message=f"Successfully hired {len(candidates_hired)} candidates",
            total_hired=len(candidates_hired),
            applications_created=applications_created,
            offers_sent=offers_sent,
            job_title=job.title,
            candidates=candidates_hired
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error confirming bulk hire: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/initiate-multi", response_model=MultiJobInitiateResponse)
async def initiate_multi_job_bulk_hire(request: MultiJobInitiateRequest, db: Session = Depends(get_db)):
    """
    Initiate bulk hiring for multiple jobs simultaneously.
    Returns matched candidates grouped by job.
    """
    try:
        if not request.job_selections:
            raise HTTPException(status_code=400, detail="No jobs selected")
        
        logger.info(f"🎯 Multi-job bulk hire: {len(request.job_selections)} jobs")
        
        matches_by_job = []
        total_positions = 0
        
        # Import MatchingTool once
        from backend.tools_langchain.matching_tool import MatchingTool
        matcher = MatchingTool()
        
        for selection in request.job_selections:
            # Fetch job details
            job = db.query(Job).filter(Job.id == selection.job_id).first()
            if not job:
                logger.warning(f"Job {selection.job_id} not found, skipping")
                continue
            
            # Validate quantity
            remaining = job.quantity_needed - job.quantity_filled
            if selection.quantity > remaining:
                raise HTTPException(
                    status_code=400,
                    detail=f"Job '{job.title}': Requested {selection.quantity} exceeds {remaining} remaining"
                )
            
            if selection.quantity < 1:
                continue
            
            # Match candidates for this job
            top_k = selection.quantity * 3
            
            logger.info(f"  Matching for {job.title}: {selection.quantity} positions")
            
            match_result = json.loads(await matcher._arun(
                query_text=job.enhanced_description or job.description,
                match_type="job_to_candidates",
                top_k=top_k,
                job_id=job.id,
                shift_requirements=[job.shift_type] if job.shift_type else None,
                role=job.job_category.value if job.job_category else None
            ))
            
            if not match_result.get("success"):
                logger.warning(f"  Matching failed for {job.title}")
                continue
            
            # Format candidates
            candidates = []
            for match in match_result.get("matches", []):
                employee_id = match.get("id")
                employee = db.query(Employee).filter(Employee.id == employee_id).first()
                
                if employee:
                    candidates.append(CandidateMatch(
                        id=employee.id,
                        name=employee.full_name,
                        base_score=match.get("base_score", 0),
                        bonus_score=match.get("bonus_score", 0),
                        final_score=match.get("final_score", 0),
                        skills=employee.skills if employee.skills else [],
                        experience_years=employee.years_in_hospitality or 0,
                        cuisine_experience=employee.cuisine_experience if employee.cuisine_experience else [],
                        shift_preferences=employee.shift_preferences if employee.shift_preferences else []
                    ))
            
            matches_by_job.append(JobCandidates(
                job_id=job.id,
                job_title=job.title,
                quantity_requested=selection.quantity,
                candidates=candidates
            ))
            
            total_positions += selection.quantity
            logger.info(f"  ✅ Found {len(candidates)} candidates for {job.title}")
        
        return MultiJobInitiateResponse(
            success=True,
            total_positions=total_positions,
            jobs_count=len(matches_by_job),
            matches_by_job=matches_by_job
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in multi-job bulk hire initiate: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/confirm-multi", response_model=MultiJobConfirmResponse)
async def confirm_multi_job_bulk_hire(request: MultiJobConfirmRequest, db: Session = Depends(get_db)):
    """
    Confirm multi-job bulk hire by creating applications and offers for all selected candidates.
    """
    try:
        if not request.selections:
            raise HTTPException(status_code=400, detail="No selections provided")
        
        logger.info(f"📋 Confirming multi-job bulk hire: {len(request.selections)} jobs")
        
        # Import tools
        from backend.tools_langchain.ollama_document_generator import OllamaDocumentGenerator
        from backend.tools_langchain.notification_tool import NotificationTool
        
        doc_generator = OllamaDocumentGenerator()
        notifier = NotificationTool()
        
        results_by_job = []
        total_hired = 0
        
        for job_selection in request.selections:
            # Fetch job
            job = db.query(Job).filter(Job.id == job_selection.job_id).first()
            if not job:
                logger.warning(f"Job {job_selection.job_id} not found, skipping")
                continue
            
            logger.info(f"  Processing {job.title}: {len(job_selection.candidates)} candidates")
            
            # Validate: Check available positions for this job
            available_positions = job.quantity_needed - job.quantity_filled
            if len(job_selection.candidates) > available_positions:
                logger.warning(f"  Skipping {job.title}: trying to hire {len(job_selection.candidates)} but only {available_positions} positions available")
                continue
            
            candidates_hired = []
            
            # First pass: Create all applications for this job
            applications_to_process = []
            for candidate_selection in job_selection.candidates:
                employee_id = candidate_selection.employee_id
                match_score = candidate_selection.score
                employee = db.query(Employee).filter(Employee.id == employee_id).first()
                if not employee:
                    logger.warning(f"    Employee {employee_id} not found, skipping")
                    continue
                
                # Check for existing application
                existing_app = db.query(Application).filter(
                    Application.employee_id == employee_id,
                    Application.job_id == job.id
                ).first()
                
                if existing_app:
                    existing_app.status = "offer_sent"
                    existing_app.match_score = match_score  # Update score
                    existing_app.updated_at = datetime.utcnow()
                    application = existing_app
                else:
                    application = Application(
                        job_id=job.id,
                        employee_id=employee_id,
                        status="offer_sent",
                        match_score=match_score,  # Store score
                        applied_at=datetime.utcnow()
                    )
                    db.add(application)
                    db.flush()
                
                # Check if offer already exists
                existing_offer = db.query(Offer).filter(
                    Offer.application_id == application.id
                ).first()
                
                if not existing_offer:
                    applications_to_process.append({
                        'application': application,
                        'employee': employee,
                        'employee_id': employee_id,
                        'match_score': match_score,
                        'job': job
                    })
            
            # Commit applications for this job
            db.commit()
            
            # Second pass: Generate documents in parallel for this job
            if applications_to_process:
                logger.info(f"    Generating documents for {len(applications_to_process)} candidates in parallel...")
                
                async def generate_docs_for_candidate(app_data):
                    """Generate offer letter and NDA for a single candidate"""
                    try:
                        employee_id = app_data['employee_id']
                        employee = app_data['employee']
                        job = app_data['job']
                        
                        # Prepare complete context data
                        from datetime import datetime, timedelta
                        context_data = {
                            "candidate_name": employee.full_name,
                            "company_name": job.employer.company_name if job.employer else "Nike",
                            "job_title": job.title,
                            "salary": job.salary_range,
                            "location": job.location,
                            "start_date": (datetime.utcnow() + timedelta(days=14)).strftime("%B %d, %Y")
                        }
                        
                        # Generate both documents in parallel
                        offer_letter, nda = await asyncio.gather(
                            doc_generator._arun(
                                employee_id=employee_id,
                                job_id=job.id,
                                document_type="offer_letter",
                                context_data=json.dumps(context_data)
                            ),
                            doc_generator._arun(
                                employee_id=employee_id,
                                job_id=job.id,
                                document_type="nda",
                                context_data=json.dumps(context_data)
                            )
                        )
                        
                        # Parse JSON responses and extract content
                        offer_letter_data = json.loads(offer_letter)
                        nda_data = json.loads(nda)
                        
                        return {
                            'success': True,
                            'application': app_data['application'],
                            'employee': app_data['employee'],
                            'offer_letter': offer_letter_data.get('content', offer_letter),
                            'nda': nda_data.get('content', nda)
                        }
                    except Exception as e:
                        logger.error(f"    Error generating documents for {app_data['employee'].full_name}: {e}")
                        return {
                            'success': False,
                            'employee': app_data['employee'],
                            'error': str(e)
                        }
                
                # Generate all documents in parallel
                import asyncio
                results = await asyncio.gather(*[
                    generate_docs_for_candidate(app_data)
                    for app_data in applications_to_process
                ])
                
                # Third pass: Create offers and send notifications
                for result, app_data in zip(results, applications_to_process):
                    if result['success']:
                        # Create offer
                        offer = Offer(
                            application_id=result['application'].id,
                            offer_letter_content=result['offer_letter'],
                            nda_content=result['nda'],
                            salary_offered=job.salary_range,
                            status="pending"
                        )
                        db.add(offer)
                        
                        # Send notification
                        try:
                            await notifier._arun(
                                user_id=result['employee'].user_id,
                                title="Job Offer Received!",
                                message=f"Congratulations! You've received an offer for the {job.title} role at {job.employer.company_name if job.employer else 'Nike'}. Match: {int(app_data['match_score'])}%. Review and accept your offer now!",
                                notification_type="offer_received"
                            )
                        except Exception as e:
                            logger.warning(f"    Failed to send notification to {result['employee'].full_name}: {e}")
                        
                        candidates_hired.append({
                            "id": result['employee'].id,
                            "name": result['employee'].full_name
                        })
            
            # Update job quantity
            job.quantity_filled = min(job.quantity_filled + len(candidates_hired), job.quantity_needed)
            
            results_by_job.append(JobHireResult(
                job_id=job.id,
                job_title=job.title,
                hired_count=len(candidates_hired),
                candidates=candidates_hired
            ))
            
            total_hired += len(candidates_hired)
            logger.info(f"  ✅ {job.title}: Hired {len(candidates_hired)} candidates")
        
        # Commit all changes
        db.commit()
        
        logger.info(f"✅ Multi-job bulk hire complete: {total_hired} total hires across {len(results_by_job)} jobs")
        
        return MultiJobConfirmResponse(
            success=True,
            message=f"Successfully hired {total_hired} candidates across {len(results_by_job)} jobs",
            total_hired=total_hired,
            jobs_processed=len(results_by_job),
            results_by_job=results_by_job
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error in multi-job bulk hire confirm: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
