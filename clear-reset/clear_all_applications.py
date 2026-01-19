"""
Clear all applications from the database
WARNING: This will delete all application records
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "manpower.db"

def clear_applications():
    """Remove all applications from the database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Get count before deletion
        cursor.execute("SELECT COUNT(*) FROM applications")
        count = cursor.fetchone()[0]
        
        print(f"Found {count} applications in database")
        
        if count == 0:
            print("No applications to delete")
            return
        
        # Confirm deletion
        response = input(f"Are you sure you want to delete all {count} applications? (yes/no): ").strip().lower()
        
        if response == "yes":
            cursor.execute("DELETE FROM applications")
            conn.commit()
            print(f"✓ Successfully deleted {count} applications")
        else:
            print("Operation cancelled")
    
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    
    finally:
        conn.close()

if __name__ == "__main__":
    clear_applications()
