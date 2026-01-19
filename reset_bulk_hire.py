"""
Reset Recent Bulk Hire Data

This script deletes offers and applications from recent bulk hire tests
so you can redo the process from scratch.
"""

from backend.db.sql_db import SessionLocal
from backend.db.models import Application, Offer, Job

db = SessionLocal()

try:
    print("="*60)
    print("RESETTING BULK HIRE DATA")
    print("="*60)
    print()
    
    # Option 1: Reset specific job (uncomment and set job_id)
    # job_id = 570  # Line Cook
    # job = db.query(Job).filter(Job.id == job_id).first()
    
    # Option 2: Reset ALL jobs
    print("Resetting ALL applications and offers...")
    
    # Count before deletion
    total_apps = db.query(Application).count()
    total_offers = db.query(Offer).count()
    
    print(f"[INFO] Found {total_apps} applications")
    print(f"[INFO] Found {total_offers} offers")
    print()
    
    # Delete all offers first (foreign key constraint)
    db.query(Offer).delete()
    print(f"[OK] Deleted all {total_offers} offers")
    
    # Delete all applications
    db.query(Application).delete()
    print(f"[OK] Deleted all {total_apps} applications")
    
    # Reset all job position counts
    jobs = db.query(Job).all()
    reset_count = 0
    for job in jobs:
        if job.quantity_filled > 0:
            job.quantity_filled = 0
            job.is_active = True
            reset_count += 1
    
    print(f"[OK] Reset {reset_count} job position counts")
    print()
    
    # Commit changes
    db.commit()
    
    print("="*60)
    print("[SUCCESS] Bulk hire data reset complete!")
    print("="*60)
    print()
    print("You can now:")
    print("1. Run bulk hire for any job")
    print("2. Send offers to candidates")
    print("3. Test the auto-fill flow")
    
except Exception as e:
    print(f"[ERROR] {e}")
    import traceback
    traceback.print_exc()
    db.rollback()
finally:
    db.close()
