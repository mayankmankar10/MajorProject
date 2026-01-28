"""
Background Jobs for Restaurant Hiring Platform
Scheduled tasks for profile analysis and maintenance
"""

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import logging
import asyncio

logger = logging.getLogger(__name__)

# Global scheduler instance
scheduler = AsyncIOScheduler()

async def analyze_profiles_nightly():
    """
    Nightly job to analyze new and updated employee profiles.
    Runs at midnight every day.
    """
    try:
        from backend.tools_langchain.bulk_profile_processor_tool import BulkProfileProcessorTool
        
        logger.info("🌙 Starting nightly profile analysis...")
        
        processor = BulkProfileProcessorTool()
        result_str = await processor._arun(mode="new_and_updated", batch_size=10)
        
        import json
        result = json.loads(result_str)
        
        if result.get("success"):
            logger.info(f"✅ Nightly analysis complete: {result.get('profiles_analyzed', 0)} profiles processed")
            logger.info(f"   Duration: {result.get('duration_seconds', 0)}s")
            logger.info(f"   Cost: ${result.get('estimated_cost_usd', 0)}")
        else:
            logger.error(f"❌ Nightly analysis failed: {result.get('error', 'Unknown error')}")
    
    except Exception as e:
        logger.error(f"❌ Nightly profile analysis error: {str(e)}")
        import traceback
        traceback.print_exc()

async def cleanup_stale_cache_weekly():
    """
    Weekly job to clean up old profile cache entries.
    Runs every Sunday at 2 AM.
    """
    try:
        from backend.db.sql_db import SessionLocal
        from backend.db.models import ProfileCache
        
        logger.info("🧹 Starting weekly cache cleanup...")
        
        db = SessionLocal()
        try:
            # Remove cache entries older than 30 days
            cutoff = datetime.utcnow() - timedelta(days=30)
            deleted = db.query(ProfileCache).filter(
                ProfileCache.analyzed_at < cutoff
            ).delete()
            
            db.commit()
            logger.info(f"✅ Cache cleanup complete: {deleted} old entries removed")
        
        finally:
            db.close()
    
    except Exception as e:
        logger.error(f"❌ Cache cleanup error: {str(e)}")
        import traceback
        traceback.print_exc()

async def cleanup_old_chat_sessions_weekly():
    """
    Weekly job to clean up old chat sessions.
    Removes sessions that have been inactive for more than 30 days.
    Chat history is retained for at least 7 days, with 30 days as the cleanup threshold.
    Runs every Sunday at 3 AM.
    """
    try:
        from backend.db.sql_db import SessionLocal
        from backend.db.models import ChatSession, ChatMessage
        
        logger.info("💬 Starting weekly chat history cleanup...")
        
        db = SessionLocal()
        try:
            # Remove chat sessions inactive for more than 30 days
            cutoff = datetime.utcnow() - timedelta(days=30)
            
            # Find old sessions
            old_sessions = db.query(ChatSession).filter(
                ChatSession.last_message_at < cutoff
            ).all()
            
            deleted_sessions = 0
            deleted_messages = 0
            
            for session in old_sessions:
                # Delete messages first (due to foreign key)
                msg_count = db.query(ChatMessage).filter(
                    ChatMessage.session_id == session.id
                ).delete()
                deleted_messages += msg_count
                
                # Delete session
                db.delete(session)
                deleted_sessions += 1
            
            db.commit()
            logger.info(f"✅ Chat cleanup complete: {deleted_sessions} sessions, {deleted_messages} messages removed")
        
        finally:
            db.close()
    
    except Exception as e:
        logger.error(f"❌ Chat cleanup error: {str(e)}")
        import traceback
        traceback.print_exc()

async def _generate_initial_embeddings(db: Session):
    """Generate embeddings for ALL employees using structured columns only."""
    from backend.db.models import Employee
    
    employees = db.query(Employee).all()
    logger.info(f"📦 Generating embeddings for {len(employees)} employees...")
    
    if len(employees) == 0:
        logger.info("   No employees to embed")
        return
    
    # Use structured format matching migrate_embeddings.py
    from backend.db.vector_db import create_vector_store
    from langchain_core.documents import Document
    
    documents = []
    for emp in employees:
        # Build structured profile from database columns only
        text_parts = []
        
        # Preferred role
        if emp.preferred_role:
            text_parts.append(f"Preferred Role: {emp.preferred_role.value}")
        
        # Skills (technical)
        if emp.skills:
            text_parts.append(f"Skills: {', '.join(emp.skills)}")
        
        # Soft skills
        if emp.soft_skills:
            text_parts.append(f"Soft Skills: {', '.join(emp.soft_skills)}")
        
        # Cuisine experience
        if emp.cuisine_experience:
            text_parts.append(f"Cuisine Experience: {', '.join(emp.cuisine_experience)}")
        
        # Shift availability
        if emp.shift_preferences:
            text_parts.append(f"Available Shifts: {', '.join(emp.shift_preferences)}")
        
        content = "\n".join([p for p in text_parts if p])
        
        # Skip if no content
        if not content:
            logger.warning(f"  ⚠️  Skipping employee {emp.id} ({emp.full_name}) - no structured data")
            continue
        
        # Metadata for filtering and display
        metadata = {
            "id": emp.id,
            "employee_id": emp.id,
            "user_id": emp.user_id,
            "full_name": emp.full_name,
            "type": "employee",
            # Structured fields for filtering
            "role": emp.preferred_role.value if emp.preferred_role else None,
            "years_in_hospitality": emp.years_in_hospitality or 0,
            "food_safety_certified": emp.food_safety_certified or False,
            "servsafe_certified": emp.servsafe_certified or False,
            "alcohol_service_certified": emp.alcohol_service_certified or False,
            "preferred_location": emp.preferred_location,
            "certifications": emp.certifications or [],
        }
        
        documents.append(Document(page_content=content, metadata=metadata))
    
    # Create employee vector store
    vector_store = create_vector_store(documents, index_type="employee")
    logger.info(f"✅ Generated embeddings for {len(documents)} employees (skipped {len(employees) - len(documents)} without data)")


async def run_incremental_startup_sync():
    """
    Incremental startup sync - check and regenerate embeddings if needed.
    
    Steps:
    1. Count total employees with profile data
    2. Check if vector store exists and has data
    3. Regenerate embeddings if needed
    """
    try:
        from backend.db.sql_db import SessionLocal
        from backend.db.models import Employee
        from backend.db.vector_db import get_vector_store
        
        logger.info("🔄 Running incremental startup sync...")
        
        db = SessionLocal()
        try:
            # Count employees with structured profile data
            total_employees = db.query(Employee).filter(
                Employee.skills.isnot(None),  # At least has skills
            ).count()
            
            logger.info(f"📊 Sync Status:")
            logger.info(f"   Total employees with profile data: {total_employees}")
            
            if total_employees == 0:
                logger.info("ℹ️  No employees with profile data yet")
                return
            
            # Check vector embeddings
            logger.info(f"🔍 Checking vector embeddings...")
            
            vector_store = get_vector_store("employee")
            
            if vector_store is None:
                logger.info("⚠️ Vector store not initialized - creating with all employees")
                await _generate_initial_embeddings(db)
            else:
                # Check if vector store has data
                try:
                    if hasattr(vector_store, 'index') and vector_store.index is not None:
                        doc_count = vector_store.index.ntotal
                        if doc_count > 0:
                            logger.info(f"✅ Vector store loaded from disk")
                            logger.info(f"   Documents in vector store: {doc_count}")
                            logger.info(f"   Total employees: {total_employees}")
                            
                            # Check if counts match (within reason)
                            if abs(doc_count - total_employees) > 5:
                                logger.info(f"⚠️ Vector store out of sync (diff: {abs(doc_count - total_employees)})")
                                logger.info("   Consider running: python -m backend.scripts.migrate_embeddings")
                            else:
                                logger.info("   ✅ Vector store appears up-to-date")
                        else:
                            logger.info("⚠️ Vector store empty - generating all embeddings")
                            await _generate_initial_embeddings(db)
                    else:
                        logger.info("⚠️ Vector store has no index - generating all embeddings")
                        await _generate_initial_embeddings(db)
                except Exception as e:
                    logger.warning(f"⚠️ Could not verify vector store: {str(e)}")
                    logger.info("   Continuing without regeneration")
        
        finally:
            db.close()
        
        logger.info("✅ Incremental startup sync complete!")
        
    except Exception as e:
        logger.error(f"❌ Startup sync failed: {str(e)}")
        import traceback
        traceback.print_exc()

def init_scheduler():
    """Initialize and start the background job scheduler."""
    
    try:
        # DISABLED: Nightly profile analysis (user wants startup-only processing)
        # scheduler.add_job(
        #     analyze_profiles_nightly,
        #     CronTrigger(hour=0, minute=0),  # Every day at 00:00
        #     id='nightly_profile_analysis',
        #     name='Analyze new/updated employee profiles',
        #     replace_existing=True
        # )
        logger.info("ℹ️  Profile analysis: STARTUP-ONLY (no nightly job)")
        
        # Job 2: Weekly cache cleanup on Sunday at 2 AM
        scheduler.add_job(
            cleanup_stale_cache_weekly,
            CronTrigger(day_of_week='sun', hour=2, minute=0),  # Sunday 02:00
            id='weekly_cache_cleanup',
            name='Clean up stale profile cache',
            replace_existing=True
        )
        logger.info("✅ Scheduled: Weekly cache cleanup (Sunday 02:00)")
        
        # Job 3: Weekly chat history cleanup on Sunday at 3 AM
        scheduler.add_job(
            cleanup_old_chat_sessions_weekly,
            CronTrigger(day_of_week='sun', hour=3, minute=0),  # Sunday 03:00
            id='weekly_chat_cleanup',
            name='Clean up old chat sessions (30+ days inactive)',
            replace_existing=True
        )
        logger.info("✅ Scheduled: Weekly chat cleanup (Sunday 03:00) - Retains 30 days")
        
        # Start the scheduler
        scheduler.start()
        logger.info("🚀 Background job scheduler started")
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize scheduler: {str(e)}")
        raise

def shutdown_scheduler():
    """Gracefully shutdown the scheduler."""
    if scheduler.running:
        scheduler.shutdown()
        logger.info("🛑 Background job scheduler stopped")

# Manual trigger functions (useful for testing or manual runs)
async def trigger_profile_analysis_manually():
    """Manually trigger profile analysis."""
    logger.info("🔧 Manual trigger: Profile analysis")
    await analyze_profiles_nightly()

async def trigger_cache_cleanup_manually():
    """Manually trigger cache cleanup."""
    logger.info("🔧 Manual trigger: Cache cleanup")
    await cleanup_stale_cache_weekly()

async def check_and_run_startup_catchup():
    """
    Check if profile analysis needs to run on startup (catch-up for missed jobs).
    Runs if last analysis was more than 24 hours ago.
    """
    try:
        from backend.db.sql_db import SessionLocal
        from backend.db.models import ProfileCache, Employee
        
        db = SessionLocal()
        try:
            # Check when last analysis ran
            last_cache = db.query(ProfileCache).order_by(
                ProfileCache.analyzed_at.desc()
            ).first()
            
            total_employees = db.query(Employee).filter(
                Employee.resume_text.isnot(None)
            ).count()
            
            if not last_cache:
                # No profiles cached yet - run analysis
                logger.info("🔄 No cached profiles found - running startup catch-up analysis...")
                await analyze_profiles_nightly()
                return
            
            # Calculate hours since last analysis
            hours_since_last = (datetime.utcnow() - last_cache.analyzed_at).total_seconds() / 3600
            
            if hours_since_last > 24:
                logger.info(f"🔄 Running startup catch-up: Last analysis was {hours_since_last:.1f} hours ago")
                await analyze_profiles_nightly()
            else:
                logger.info(f"✅ No catch-up needed: Last analysis was {hours_since_last:.1f} hours ago")
                
                # Show cache coverage
                cached_count = db.query(ProfileCache).count()
                if total_employees > 0:
                    coverage = (cached_count / total_employees) * 100
                    logger.info(f"   Cache coverage: {cached_count}/{total_employees} profiles ({coverage:.1f}%)")
        
        finally:
            db.close()
    
    except Exception as e:
        logger.error(f"❌ Startup catch-up check failed: {str(e)}")
        import traceback
        traceback.print_exc()

async def run_startup_analysis():
    """
    ALWAYS run profile analysis on startup.
    Ensures cache is fresh every time the backend starts.
    This is useful for development and testing.
    """
    try:
        from backend.db.sql_db import SessionLocal
        from backend.db.models import ProfileCache, Employee
        
        logger.info("🚀 Running startup profile analysis...")
        
        db = SessionLocal()
        try:
            total_employees = db.query(Employee).filter(
                Employee.resume_text.isnot(None)
            ).count()
            
            cached_count = db.query(ProfileCache).count()
            
            logger.info(f"📊 Current cache status:")
            logger.info(f"   Total employees with resumes: {total_employees}")
            logger.info(f"   Cached profiles: {cached_count}")
            
            if total_employees == 0:
                logger.info("ℹ️  No employees to analyze yet")
                return
        finally:
            db.close()
        
        # Run analysis
        logger.info("🔄 Analyzing all new/updated profiles...")
        await analyze_profiles_nightly()
        logger.info("✅ Startup profile analysis complete!")
        
    except Exception as e:
        logger.error(f"❌ Startup analysis failed: {str(e)}")
        import traceback
        traceback.print_exc()
