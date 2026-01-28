"""
Quick script to analyze all employee profiles and populate ProfileCache
Run with: python analyze_all_profiles.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.db.sql_db import SessionLocal
from backend.db.models import Employee
from backend.tools_langchain.bulk_profile_processor_tool import analyze_single_employee
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    db = SessionLocal()
    try:
        # Get all employees with resumes
        employees = db.query(Employee).filter(
            Employee.resume_text.isnot(None)
        ).all()
        
        logger.info(f"Found {len(employees)} employees with resumes")
        
        if not employees:
            logger.warning("No employees to analyze!")
            return
        
        success_count = 0
        error_count = 0
        
        for i, emp in enumerate(employees, 1):
            logger.info(f"\n[{i}/{len(employees)}] Analyzing {emp.full_name} (ID: {emp.id})...")
            
            try:
                # Use the existing analyze_single_employee function
                result = analyze_single_employee(emp.id, db)
                
                if result and result.get('success'):
                    success_count += 1
                    logger.info(f"  ✅ Success! Summary: {result.get('summary', '')[:100]}...")
                else:
                    error_count += 1
                    logger.error(f"  ❌ Failed: {result.get('error', 'Unknown error')}")
                    
            except Exception as e:
                error_count += 1
                logger.error(f"  ❌ Exception: {str(e)}")
        
        logger.info("\n" + "="*60)
        logger.info("ANALYSIS COMPLETE")
        logger.info("="*60)
        logger.info(f"✅ Successful: {success_count}")
        logger.info(f"❌ Failed: {error_count}")
        logger.info(f"📊 Total: {len(employees)}")
        
    finally:
        db.close()

if __name__ == "__main__":
    main()
