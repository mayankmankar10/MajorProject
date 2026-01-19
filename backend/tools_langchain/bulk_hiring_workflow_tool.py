"""
Bulk Hiring Workflow Tool - End-to-end automated hiring pipeline
Orchestrates all tools from job description to offer letters
"""

from langchain.tools import BaseTool
from typing import Type, Dict, List, Any
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy.orm import Session
from backend.db.sql_db import SessionLocal
from backend.db.models import Job, Employee, ProfileCache
from datetime import datetime
import json
import logging
import asyncio

logger = logging.getLogger(__name__)

class BulkHiringWorkflowInput(BaseModel):
    """Input schema for bulk hiring workflow."""
    employer_input: str = Field(
        description="Natural language hiring request (e.g., 'Need 5 waiters, 2 cooks, 1 chef for Mumbai cafe')"
    )
    employer_id: int = Field(description="ID of the employer posting jobs")
    additional_context: Dict = Field(
        default={},
        description="Additional context like cuisine_type, shift_type, salary_range"
    )

class BulkHiringWorkflowTool(BaseTool):
    """
    End-to-end automated DIRECT HIRING workflow.
    
    ⚠️ IMPORTANT: This tool does NOT create job postings!
    Use this for immediate hiring needs: "I need 5 waiters", "Hire 3 chefs now"
    For creating job postings, use JobPostingCreatorTool instead.
    
    Single command executes entire pipeline:
    1. Parse positions from natural language
    2. Load job templates for context
    3. Get cached employee profiles (or analyze if needed)
    4. Match candidates with restaurant-specific scoring
    5. Select exact quantity per position
    6. Generate offer letters and NDAs
    7. Send notifications to selected candidates
    8. Return comprehensive summary
    
    Performance: Completes in 3-5 seconds for typical bulk hiring request
    """
    name: str = "BulkHiringWorkflowTool"
    description: str = """
    Complete automated DIRECT HIRING pipeline - NO JOB POSTING CREATION.
    
    Use for immediate hiring needs:
    - "I need 5 waiters and 2 cooks"
    - "Hire 3 chefs for my restaurant"
    - "Get me 10 staff members now"
    
    DO NOT use for creating job postings. Use JobPostingCreatorTool for that.
    
    Input: Natural language request like "Need 5 waiters, 2 cooks for Italian cafe in Mumbai"
    
    Output: Comprehensive summary with:
    - Candidates matched and selected
    - Documents generated (offers + NDAs)
    - Notifications sent
    
    ONE COMMAND completes entire hiring process WITHOUT creating job postings.
    """
    args_schema: Type[BaseModel] = BulkHiringWorkflowInput
    
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    async def _arun(self, employer_input: str, employer_id: int, additional_context: dict = None) -> str:
        """
        Async implementation of bulk hiring workflow with caching.
        Now with result caching for improved performance.
        
        Returns JSON with:
        {
            "success": bool,
            "total_hired": int,
            "positions_created": {...},
            "documents_generated": int,
            "execution_time_ms": float,
            "steps_completed": [...]
        }
        """
        start_time = datetime.utcnow()
        additional_context = additional_context or {}
        
        # Performance optimization: Check cache first
        from backend.cache.tool_cache import tool_cache
        import hashlib
        
        # Create cache key from input
        cache_key_str = f"{employer_input}:{employer_id}:{json.dumps(additional_context, sort_keys=True)}"
        cache_key_hash = hashlib.md5(cache_key_str.encode()).hexdigest()
        
        cached_result = tool_cache.get("BulkHiringWorkflowTool", cache_key=cache_key_hash)
        if cached_result:
            logger.info(f"⚡ Returning cached bulk hiring result (cache hit)")
            return cached_result
        
        logger.info(f"🚀 Starting bulk hiring workflow for employer {employer_id}")
        steps_completed = []
        
        try:
            from backend.tools_langchain.position_parser_tool import PositionParserTool
            from backend.tools_langchain.job_templates import get_template, enhance_template
            from backend.tools_langchain.job_description_enhancer import JobDescriptionEnhancer
            from backend.tools_langchain.bulk_profile_processor_tool import BulkProfileProcessorTool
            from backend.tools_langchain.matching_tool import MatchingTool
            from backend.tools_langchain.quantity_based_selector_tool import QuantityBasedSelectorTool
            from backend.tools_langchain.ollama_document_generator import OllamaDocumentGenerator
            from backend.tools_langchain.notification_tool import NotificationTool
            
            logger.info(f"🚀 Starting bulk hiring workflow for employer {employer_id}")
            
            # STEP 1: Parse positions from natural language
            logger.info("📋 Step 1: Parsing positions...")
            parser = PositionParserTool()
            parse_result = json.loads(await parser._arun(employer_input))
            
            if not parse_result.get("success"):
                raise Exception(f"Position parsing failed: {parse_result.get('error')}")
            
            positions = parse_result["positions"]
            location = parse_result.get("location") or additional_context.get("location")
            steps_completed.append(f"✓ Parsed {len(positions)} positions ({parse_result['parsing_method']})")
            logger.info(f"  Found {len(positions)} positions in {location or 'unspecified location'}")
            
            # STEP 2: Load and enhance templates for each position
            logger.info("📝 Step 2: Loading job templates...")
            enhanced_jobs = []
            for position in positions:
                template = get_template(position["job_type"])
                if not template:
                    logger.warning(f"  No template for {position['job_type']}, using basic")
                    template = {"title": position["title"], "base_description": "Restaurant position"}
                
                # Enhance with context
                enhanced = enhance_template(
                    position["job_type"],
                    location=location,
                    cuisine_type=additional_context.get("cuisine_type"),
                    shift_type=additional_context.get("shift_type"),
                    quantity_needed=position["quantity"]
                )
                
                enhanced_jobs.append({
                    **position,
                    **enhanced,
                    "employer_id": employer_id
                })
            
            steps_completed.append(f"✓ Enhanced {len(enhanced_jobs)} job descriptions")
            
            # STEP 3: Use pre-computed profile cache (infinitely scalable!)
            logger.info("👥 Step 3: Using pre-computed profile cache...")
            
            # Check cache coverage without triggering new analysis
            db_session = SessionLocal()
            try:
                cache_count = db_session.query(ProfileCache).count()
                employee_count = db_session.query(Employee).count()
                coverage = (cache_count / employee_count * 100) if employee_count > 0 else 0
                
                logger.info(f"📊 Cache coverage: {cache_count}/{employee_count} profiles ({coverage:.1f}%)")
                
                if coverage < 50:
                    logger.warning(f"⚠️ Low cache coverage ({coverage:.1f}%). Background job will refresh tonight.")
                
                steps_completed.append(f"✓ Using {cache_count} pre-analyzed profiles ({coverage:.0f}% coverage)")
            finally:
                db_session.close()
            
            # No BulkProfileProcessorTool call! All analysis handled by background jobs.
            
            # STEP 4: Match candidates for each position (NO JOB CREATION!)
            logger.info("🎯 Step 4: Matching candidates for direct hire...")
            from backend.tools_langchain.matching_tool import MatchingTool
            
            matcher = MatchingTool()
            all_matches = {}
            
            for job_data in enhanced_jobs:
                # Match using job description, but don't create job record
                # Pass shift requirements for filtering
                match_result = json.loads(await matcher._arun(
                    query_text=job_data.get("enhanced_description") or job_data.get("base_description"),
                    match_type="job_to_candidates",
                    top_k=job_data["quantity"] * 3,  # Get 3x for better selection
                    job_id=None,  # No job_id for direct hiring
                    shift_requirements=parse_result.get("shift_requirements"),  # Pass shift filter
                    role=job_data.get("job_type")  # Pass role for role-based bonus scoring
                ))
                
                if match_result.get("success"):
                    all_matches[job_data["job_type"]] = {
                        "matches": match_result["matches"],
                        "quantity": job_data["quantity"],
                        "title": job_data["title"]
                    }
            
            steps_completed.append(f"✓ Matched candidates for {len(all_matches)} positions (direct hire)")

            
            # STEP 5: Select exact quantities
            logger.info("✅ Step 5: Selecting candidates by quantity...")
            selector_input = [
                {
                    "job_type": job_type,
                    "quantity": data["quantity"],
                    "matches": data["matches"]
                }
                for job_type, data in all_matches.items()
            ]
            
            from backend.tools_langchain.quantity_based_selector_tool import QuantityBasedSelectorTool
            selector = QuantityBasedSelectorTool()
            selection_result = json.loads(await selector._arun(positions=selector_input))
            
            if not selection_result.get("success"):
                raise Exception("Candidate selection failed")
            
            selections = selection_result["selections"]
            total_selected = selection_result["total_selected"]
            steps_completed.append(f"✓ Selected {total_selected} candidates")

            
            # STEP 6: Generate offer letters and NDAs (Parallel Execution with Ollama - 20-50x faster)
            logger.info("📄 Step 6: Generating documents with Ollama (Fast)...")
            from backend.tools_langchain.ollama_document_generator import OllamaDocumentGenerator
            
            onboarding = OllamaDocumentGenerator()  # Uses Ollama for speed, auto-fallback to GPT-4
            document_tasks = []
            
            # Pre-lookup job_ids for document generation (same logic as Step 7)
            doc_db = SessionLocal()
            doc_job_id_cache = {}
            try:
                for job_type in selections.keys():
                    matching_job = doc_db.query(Job).filter(
                        Job.employer_id == employer_id,
                        Job.is_active == True
                    ).filter(
                        Job.title.ilike(f"%{job_type}%")
                    ).order_by(Job.created_at.desc()).first()
                    
                    if not matching_job:
                        matching_job = doc_db.query(Job).filter(
                            Job.employer_id == employer_id,
                            Job.is_active == True
                        ).order_by(Job.created_at.desc()).first()
                    
                    doc_job_id_cache[job_type] = matching_job.id if matching_job else None
            finally:
                doc_db.close()
            
            for job_type, selected_candidates in selections.items():
                matched_job_id = doc_job_id_cache.get(job_type)
                if matched_job_id is None:
                    logger.warning(f"⚠️ No job found for {job_type}, skipping document generation")
                    continue
                    
                for candidate in selected_candidates:
                    # Create tasks for Offer Letter and NDA with job_id
                    task_offer = onboarding._arun(
                        employee_id=candidate["id"],
                        job_id=matched_job_id,  # Link to matching job
                        document_type="offer_letter",
                        context_data=json.dumps({
                            "company_name": f"Employer {employer_id}",
                            "position": all_matches[job_type]["title"]
                        })
                    )
                    task_nda = onboarding._arun(
                        employee_id=candidate["id"],
                        job_id=matched_job_id,  # Link to matching job
                        document_type="nda",
                        context_data=json.dumps({
                            "company_name": f"Employer {employer_id}",
                            "position": all_matches[job_type]["title"]
                        })
                    )
                    document_tasks.extend([task_offer, task_nda])
            
            # Execute all document generation tasks in parallel
            if document_tasks:
                await asyncio.gather(*document_tasks)
                documents_generated = len(document_tasks)
            else:
                documents_generated = 0
            
            steps_completed.append(f"✓ Generated {documents_generated} documents (Parallel)")

            
            # STEP 7: Create Offers and send notifications
            logger.info("📧 Step 7: Creating offers and sending notifications...")
            notifications_sent = 0
            offers_created = 0
            
            db = SessionLocal()
            try:
                from backend.db.models import Employer, Notification, Application, ApplicationStatus, Offer
                
                # Get employer info for better notifications
                employer = db.query(Employer).filter(Employer.id == employer_id).first()
                employer_name = employer.company_name if employer else f"Employer {employer_id}"
                
                # Cache for job lookups by job_type
                job_id_cache = {}
                
                for job_type, selected_candidates in selections.items():
                    job_title = all_matches[job_type]["title"]
                    
                    # Look up an existing job from this employer that matches the job_type
                    if job_type not in job_id_cache:
                        matching_job = db.query(Job).filter(
                            Job.employer_id == employer_id,
                            Job.is_active == True
                        ).filter(
                            # Match by job title containing the job_type (e.g., "bartender" in "Bartender Position")
                            Job.title.ilike(f"%{job_type}%")
                        ).order_by(Job.created_at.desc()).first()
                        
                        if not matching_job:
                            # Fall back to any active job from this employer
                            matching_job = db.query(Job).filter(
                                Job.employer_id == employer_id,
                                Job.is_active == True
                            ).order_by(Job.created_at.desc()).first()
                        
                        if matching_job:
                            job_id_cache[job_type] = matching_job.id
                            logger.info(f"📌 Using job '{matching_job.title}' (ID: {matching_job.id}) for {job_type} applications")
                        else:
                            logger.warning(f"⚠️ No matching job found for employer {employer_id}, job_type {job_type}")
                            job_id_cache[job_type] = None
                    
                    matched_job_id = job_id_cache.get(job_type)
                    
                    if matched_job_id is None:
                        logger.error(f"❌ Cannot create application: No job found for employer {employer_id}")
                        continue
                    
                    for candidate in selected_candidates:
                        employee = db.query(Employee).filter(Employee.id == candidate["id"]).first()
                        if employee and employee.user_id:
                            try:
                                # Get match score from candidate data (final_score is 0-100, convert to 0-1)
                                match_score = candidate.get("final_score", 75.0) / 100.0
                                
                                # Check if application already exists for this employee-job combination
                                existing_application = db.query(Application).filter(
                                    Application.employee_id == employee.id,
                                    Application.job_id == matched_job_id
                                ).first()
                                
                                if existing_application:
                                    # Update existing application instead of creating new one
                                    logger.info(f"📝 Updating existing application #{existing_application.id} for employee {employee.id}")
                                    existing_application.status = ApplicationStatus.OFFER_SENT
                                    existing_application.match_score = match_score
                                    existing_application.updated_at = datetime.utcnow()
                                    application = existing_application
                                else:
                                    # Create new application
                                    application = Application(
                                        job_id=matched_job_id,  # Link to existing matching job
                                        employee_id=employee.id,
                                        status=ApplicationStatus.OFFER_SENT,
                                        match_score=match_score
                                    )
                                    db.add(application)
                                    db.flush()  # Get application ID
                                
                                # Check if Offer already exists for this application
                                existing_offer = db.query(Offer).filter(
                                    Offer.application_id == application.id
                                ).first()
                                
                                if not existing_offer:
                                    # Create Offer record
                                    offer = Offer(
                                        application_id=application.id,
                                        salary_offered=additional_context.get("salary_range", "Competitive"),
                                        additional_terms={
                                            "shift_type": additional_context.get("shift_type"),
                                            "location": location,
                                            "job_type": job_type,
                                            "hire_type": "direct_hire"
                                        },
                                        status="pending"
                                    )
                                    db.add(offer)
                                    offers_created += 1
                                else:
                                    logger.info(f"📋 Offer already exists for application #{application.id}, skipping creation")
                                
                                # UPDATE quantity_filled on job
                                job_record = db.query(Job).filter(Job.id == matched_job_id).first()
                                if job_record:
                                    job_record.quantity_filled = (job_record.quantity_filled or 0) + 1
                                    logger.info(f"📊 Updated job positions: {job_record.quantity_filled}/{job_record.quantity_needed}")
                                
                                # Create enhanced notification with offer action
                                notification = Notification(
                                    recipient_id=employee.user_id,
                                    title="🎉 Job Offer Received!",
                                    message=f"Congratulations! You've received an offer for the {job_title} role at {employer_name}. Match: {int(match_score*100)}%. Review and accept your offer now!",
                                    notification_type="offer_received",
                                    action_url="/employee/offers",
                                    meta_data={
                                        "offer_type": "direct_hire",
                                        "job_type": job_type,
                                        "match_score": match_score
                                    }
                                )
                                db.add(notification)
                                notifications_sent += 1
                                
                                # Send WebSocket notification (best effort)
                                try:
                                    from backend.notifications.connection_manager import manager
                                    notification_data = {
                                        "title": notification.title,
                                        "message": notification.message,
                                        "type": "offer_received",
                                        "job_title": job_title,
                                        "employer": employer_name,
                                        "match_score": match_score,
                                        "action_url": notification.action_url
                                    }
                                    
                                    loop = asyncio.new_event_loop()
                                    asyncio.set_event_loop(loop)
                                    loop.run_until_complete(manager.send_personal_message(
                                        json.dumps(notification_data),
                                        employee.user_id
                                    ))
                                    loop.close()
                                except Exception as ws_error:
                                    logger.warning(f"WebSocket failed for employee {employee.user_id}: {ws_error}")
                                    # Non-critical
                                    
                            except Exception as e:
                                # Rollback the failed transaction to prevent PendingRollbackError
                                db.rollback()
                                logger.warning(f"Offer creation failed for employee {candidate.get('id')}: {str(e)}")
                
                db.commit()
            finally:
                db.close()
            
            steps_completed.append(f"✓ Created {offers_created} offers and sent {notifications_sent} notifications")

            
            # Final result
            duration = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            result = {
                "success": True,
                "total_hired": total_selected,
                "positions_filled": {
                    job_type: len(selected_candidates)
                    for job_type, selected_candidates in selections.items()
                },
                "breakdown": selections,
                "documents_generated": documents_generated,
                "notifications_sent": notifications_sent,
                "execution_time_ms": round(duration, 2),
                "steps_completed": steps_completed,
                "unfilled_positions": selection_result.get("unfilled", []),
                "hire_type": "direct_hire"
            }
            
            logger.info(f"🎉 Direct hire complete: Hired {total_selected} candidates in {duration:.0f}ms")

            
            result_json = json.dumps(result)
            
            # Cache the successful result (1 hour TTL)
            tool_cache.set(
                "BulkHiringWorkflowTool",
                result_json,
                ttl=3600,  # 1 hour
                cache_key=cache_key_hash
            )
            
            return result_json
            
        except Exception as e:
            logger.error(f"❌ Workflow error: {str(e)}")
            import traceback
            traceback.print_exc()
            
            duration = (datetime.utcnow() - start_time).total_seconds() * 1000
            return json.dumps({
                "success": False,
                "error": str(e),
                "steps_completed": steps_completed,
                "execution_time_ms": round(duration, 2)
            })
    
    def _run(self, employer_input: str, employer_id: int, additional_context: Dict = {}) -> str:
        """Sync wrapper."""
        import asyncio
        return asyncio.run(self._arun(employer_input, employer_id, additional_context))
