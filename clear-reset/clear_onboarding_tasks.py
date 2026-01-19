"""
Clear onboarding tasks from the database
WARNING: This will delete all onboarding task records
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "manpower.db"

def clear_onboarding_tasks():
    """Remove all onboarding tasks from the database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Get count before deletion
        cursor.execute("SELECT COUNT(*) FROM onboarding_tasks")
        count = cursor.fetchone()[0]
        
        print(f"Found {count} onboarding tasks in database")
        
        if count == 0:
            print("No onboarding tasks to delete")
            return
        
        # Confirm deletion
        response = input(f"Are you sure you want to delete all {count} onboarding tasks? (yes/no): ").strip().lower()
        
        if response == "yes":
            cursor.execute("DELETE FROM onboarding_tasks")
            conn.commit()
            print(f"✓ Successfully deleted {count} onboarding tasks")
        else:
            print("Operation cancelled")
    
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    
    finally:
        conn.close()

if __name__ == "__main__":
    clear_onboarding_tasks()
