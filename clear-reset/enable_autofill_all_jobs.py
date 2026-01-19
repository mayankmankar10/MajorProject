"""
Enable auto-fill on decline for all jobs in the database
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "manpower.db"

def enable_autofill_all_jobs():
    """Enable auto_fill_on_decline for all jobs"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Get count of jobs
        cursor.execute("SELECT COUNT(*) FROM jobs WHERE auto_fill_on_decline = 0 OR auto_fill_on_decline IS NULL")
        count = cursor.fetchone()[0]
        
        print(f"Found {count} jobs with auto-fill disabled")
        
        if count == 0:
            print("All jobs already have auto-fill enabled")
            return
        
        # Enable auto-fill for all jobs
        cursor.execute("UPDATE jobs SET auto_fill_on_decline = 1")
        conn.commit()
        
        print(f"✓ Successfully enabled auto-fill for {count} jobs")
        
        # Show updated stats
        cursor.execute("SELECT COUNT(*) FROM jobs WHERE auto_fill_on_decline = 1")
        enabled_count = cursor.fetchone()[0]
        print(f"Total jobs with auto-fill enabled: {enabled_count}")
    
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    
    finally:
        conn.close()

if __name__ == "__main__":
    enable_autofill_all_jobs()
