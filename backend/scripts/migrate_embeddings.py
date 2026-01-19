# backend/scripts/migrate_embeddings.py
"""
Migration script to:
1. Re-embed all employee profiles with Gemini
2. Create job embeddings (new)

Run with: python -m backend.scripts.migrate_embeddings
"""

import asyncio
import sys
import os
import logging
from datetime import datetime

# Add parent dir to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from langchain.schema import Document
from backend.db.sql_db import SessionLocal
from backend.db.models import Employee, Job, ProfileCache
from backend.db.vector_db import (
    get_embeddings, create_vector_store, init_vector_store,
    VECTOR_DB_DIR, EMPLOYEE_INDEX_NAME, JOB_INDEX_NAME
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def embed_employees():
    """Re-embed all employee profiles with Gemini."""
    logger.info("=" * 60)
    logger.info("PHASE 1: Embedding Employee Profiles")
    logger.info("=" * 60)
    
    db = SessionLocal()
    try:
        # Get all employees with profile data
        employees = db.query(Employee).filter(
            Employee.resume_text.isnot(None)
        ).all()
        
        logger.info(f"Found {len(employees)} employees with resumes")
        
        if not employees:
            logger.warning("No employees to embed!")
            return False
        
        documents = []
        for emp in employees:
            # Get cached profile if available
            cached = db.query(ProfileCache).filter(
                ProfileCache.employee_id == emp.id
            ).first()
            
            # Build rich document text
            text_parts = [
                f"Name: {emp.full_name}",
                f"Skills: {emp.skills}" if emp.skills else "",
                f"Experience: {emp.years_in_hospitality} years" if emp.years_in_hospitality else "",
            ]
            
            if cached:
                text_parts.extend([
                    f"Summary: {cached.professional_summary}" if cached.professional_summary else "",
                    f"Top Skills: {', '.join(cached.top_skills or [])}",
                    f"Recommended Roles: {', '.join(cached.recommended_roles or [])}",
                    f"Strengths: {', '.join(cached.strengths or [])}"
                ])
            
            if emp.resume_text:
                text_parts.append(f"Resume: {emp.resume_text[:500]}")
            
            content = "\n".join([p for p in text_parts if p])
            
            doc = Document(
                page_content=content,
                metadata={
                    "id": emp.id,
                    "user_id": emp.user_id,
                    "full_name": emp.full_name,
                    "skills": emp.skills,
                    "type": "employee"
                }
            )
            documents.append(doc)
        
        logger.info(f"📄 Creating embeddings for {len(documents)} employee documents...")
        
        # Create new vector store with Gemini embeddings
        store = create_vector_store(documents, index_type="employee")
        
        logger.info(f"✅ Employee embeddings complete! Saved to {EMPLOYEE_INDEX_NAME}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Employee embedding failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


def embed_jobs():
    """Embed all active jobs with Gemini."""
    logger.info("=" * 60)
    logger.info("PHASE 2: Embedding Job Postings")
    logger.info("=" * 60)
    
    db = SessionLocal()
    try:
        # Get all active jobs
        jobs = db.query(Job).filter(Job.is_active == True).all()
        
        logger.info(f"Found {len(jobs)} active jobs")
        
        if not jobs:
            logger.warning("No jobs to embed!")
            return False
        
        documents = []
        for job in jobs:
            # Build rich document text
            text_parts = [
                f"Title: {job.title}",
                f"Company: {job.employer.company_name if job.employer else 'Unknown'}",
                f"Location: {job.location}" if job.location else "",
                f"Type: {job.job_type}" if job.job_type else "",
                f"Description: {job.description}" if job.description else "",
                f"Requirements: {job.requirements}" if job.requirements else "",
                f"Salary: {job.salary_range}" if job.salary_range else "",
            ]
            
            # Add restaurant-specific fields if available
            if hasattr(job, 'cuisine_type') and job.cuisine_type:
                text_parts.append(f"Cuisine: {job.cuisine_type}")
            if hasattr(job, 'shift_type') and job.shift_type:
                text_parts.append(f"Shift: {job.shift_type}")
            
            content = "\n".join([p for p in text_parts if p])
            
            doc = Document(
                page_content=content,
                metadata={
                    "id": job.id,
                    "title": job.title,
                    "company_name": job.employer.company_name if job.employer else "Unknown",
                    "location": job.location,
                    "job_type": job.job_type,
                    "salary_range": job.salary_range,
                    "type": "job"
                }
            )
            documents.append(doc)
        
        logger.info(f"📄 Creating embeddings for {len(documents)} job documents...")
        
        # Create new vector store with Gemini embeddings
        store = create_vector_store(documents, index_type="job")
        
        logger.info(f"✅ Job embeddings complete! Saved to {JOB_INDEX_NAME}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Job embedding failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


def main():
    """Run full migration."""
    start_time = datetime.now()
    
    logger.info("🚀 Starting Gemini Embeddings Migration")
    logger.info(f"Time: {start_time}")
    logger.info("")
    
    # Initialize
    init_vector_store()
    
    # Test embeddings
    logger.info("Testing Gemini embeddings...")
    try:
        embeddings = get_embeddings()
        test_result = embeddings.embed_query("test embedding")
        logger.info(f"✅ Embeddings working! Dimension: {len(test_result)}")
    except Exception as e:
        logger.error(f"❌ Embeddings test failed: {e}")
        return False
    
    # Phase 1: Employees
    emp_success = embed_employees()
    
    # Phase 2: Jobs
    job_success = embed_jobs()
    
    # Summary
    duration = (datetime.now() - start_time).total_seconds()
    
    logger.info("")
    logger.info("=" * 60)
    logger.info("MIGRATION SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Employee embeddings: {'✅ SUCCESS' if emp_success else '❌ FAILED'}")
    logger.info(f"Job embeddings: {'✅ SUCCESS' if job_success else '❌ FAILED'}")
    logger.info(f"Total time: {duration:.2f} seconds")
    logger.info(f"Cost: $0.00 (Gemini is FREE!)")
    logger.info("")
    
    if emp_success and job_success:
        logger.info("🎉 Migration complete! Both indices ready for hybrid search.")
        return True
    else:
        logger.warning("⚠️ Migration incomplete. Check errors above.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
