"""
Database migration script for restaurant-specific features.
Run this to add new fields and tables to existing database.
"""

import sys
import os
# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from sqlalchemy import inspect, text
from backend.db.sql_db import engine, Base
from backend.db.models import ProfileCache
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate_database():
    """Add restaurant-specific fields and tables."""
    inspector = inspect(engine)
    
    logger.info("🔄 Starting database migration for restaurant features...")
    
    try:
        # Step 1: Create ProfileCache table if doesn't exist
        if not inspector.has_table("profile_cache"):
            ProfileCache.__table__.create(engine)
            logger.info("✅ Created profile_cache table")
        else:
            logger.info("ℹ️  profile_cache table already exists")
        
        # Step 2: Add new columns to employees table
        existing_employee_columns = [col['name'] for col in inspector.get_columns('employees')]
        
        new_employee_columns = {
            'updated_at': 'DATETIME',
            'food_safety_certified': 'BOOLEAN DEFAULT 0',
            'servsafe_certified': 'BOOLEAN DEFAULT 0',
            'alcohol_service_certified': 'BOOLEAN DEFAULT 0',
            'preferred_role': 'VARCHAR(50)',
            'cuisine_experience': 'JSON',
            'shift_preferences': 'JSON',
            'years_in_hospitality': 'INTEGER DEFAULT 0',
            'last_profile_analysis': 'DATETIME',
            'profile_summary': 'TEXT'
        }
        
        with engine.begin() as conn:
            for col_name, col_type in new_employee_columns.items():
                if col_name not in existing_employee_columns:
                    try:
                        conn.execute(text(f"ALTER TABLE employees ADD COLUMN {col_name} {col_type}"))
                        logger.info(f"✅ Added employees.{col_name}")
                    except Exception as e:
                        logger.warning(f"⚠️  Could not add employees.{col_name}: {str(e)}")
                else:
                    logger.info(f"ℹ️  employees.{col_name} already exists")
        
        # Step 3: Add new columns to jobs table
        existing_job_columns = [col['name'] for col in inspector.get_columns('jobs')]
        
        new_job_columns = {
            'cuisine_type': 'VARCHAR(100)',
            'shift_type': 'VARCHAR(50)',
            'requires_food_safety': 'BOOLEAN DEFAULT 1',
            'requires_alcohol_cert': 'BOOLEAN DEFAULT 0',
            'min_hospitality_experience': 'INTEGER DEFAULT 0',
            'job_category': 'VARCHAR(50)',
            'quantity_needed': 'INTEGER DEFAULT 1'
        }
        
        with engine.begin() as conn:
            for col_name, col_type in new_job_columns.items():
                if col_name not in existing_job_columns:
                    try:
                        conn.execute(text(f"ALTER TABLE jobs ADD COLUMN {col_name} {col_type}"))
                        logger.info(f"✅ Added jobs.{col_name}")
                    except Exception as e:
                        logger.warning(f"⚠️  Could not add jobs.{col_name}: {str(e)}")
                else:
                    logger.info(f"ℹ️  jobs.{col_name} already exists")
        
        logger.info("\n🎉 Database migration completed successfully!")
        logger.info("\n📊 Migration Summary:")
        logger.info(f"   - ProfileCache table: {'Created' if not inspector.has_table('profile_cache') else 'Already exists'}")
        logger.info(f"   - Employee fields added: {len([c for c in new_employee_columns if c not in existing_employee_columns])}")
        logger.info(f"   - Job fields added: {len([c for c in new_job_columns if c not in existing_job_columns])}")
        
        return {"success": True, "message": "Migration completed"}
        
    except Exception as e:
        logger.error(f"\n❌ Migration failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}

def verify_migration():
    """Verify that migration was successful."""
    inspector = inspect(engine)
    
    logger.info("\n🔍 Verifying migration...")
    
    # Check ProfileCache table
    has_profile_cache = inspector.has_table("profile_cache")
    logger.info(f"   ProfileCache table exists: {has_profile_cache}")
    
    # Check Employee fields
    employee_columns = [col['name'] for col in inspector.get_columns('employees')]
    required_employee_fields = ['food_safety_certified', 'preferred_role', 'cuisine_experience', 
                                 'shift_preferences', 'years_in_hospitality']
    has_employee_fields = all(field in employee_columns for field in required_employee_fields)
    logger.info(f"   Employee restaurant fields present: {has_employee_fields}")
    
    # Check Job fields
    job_columns = [col['name'] for col in inspector.get_columns('jobs')]
    required_job_fields = ['cuisine_type', 'shift_type', 'job_category', 'quantity_needed']
    has_job_fields = all(field in job_columns for field in required_job_fields)
    logger.info(f"   Job restaurant fields present: {has_job_fields}")
    
    if has_profile_cache and has_employee_fields and has_job_fields:
        logger.info("\n✅ Migration verification PASSED!")
        return True
    else:
        logger.error("\n❌ Migration verification FAILED!")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Restaurant Features Database Migration")
    print("=" * 60)
    print()
    
    result = migrate_database()
    
    if result["success"]:
        verify_migration()
    else:
        print(f"\nError: {result.get('error')}")
