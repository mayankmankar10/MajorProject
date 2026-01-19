"""
Reset bulk hire data (applications and offers)
WARNING: This will delete bulk hire related data
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "manpower.db"

def reset_bulk_hire():
    """Reset bulk hire data"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Get counts
        cursor.execute("SELECT COUNT(*) FROM applications")
        app_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM offers")
        offer_count = cursor.fetchone()[0]
        
        print(f"Found {app_count} applications and {offer_count} offers")
        
        # Confirm deletion
        response = input(f"Delete all applications and offers? (yes/no): ").strip().lower()
        
        if response == "yes":
            cursor.execute("DELETE FROM offers")
            cursor.execute("DELETE FROM applications")
            conn.commit()
            print(f"✓ Successfully deleted {app_count} applications and {offer_count} offers")
        else:
            print("Operation cancelled")
    
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    
    finally:
        conn.close()

if __name__ == "__main__":
    reset_bulk_hire()
