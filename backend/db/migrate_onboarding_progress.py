"""
Database migration script to add onboarding_progress table.
Run this to create the new table for tracking employee onboarding.
"""
import sys
sys.path.append('.')

from backend.db.sql_db import engine, Base
from backend.db.models import OnboardingProgress
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate():
    """Create onboarding_progress table"""
    try:
        logger.info("Creating onboarding_progress table...")
        Base.metadata.tables['onboarding_progress'].create(engine, checkfirst=True)
        logger.info("✅ onboarding_progress table created successfully!")
        return True
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        return False

if __name__ == "__main__":
    success = migrate()
    sys.exit(0 if success else 1)
