"""
Repository Cleanup Script
Removes test files, utility scripts, temporary files, and old database backups
"""

import os
import shutil
from pathlib import Path

# Get the base directory
BASE_DIR = Path(__file__).parent

# Files to remove - organized by category
FILES_TO_REMOVE = {
    "Test Files": [
        "enable_autofill_test.py",
        "reset_bulk_hire_test.py",
        "run_all_tests.py",
        "correct_test_instructions.py",
        "setup_autofill_test.py",
        "simulate_autofill_test.py",
    ],
    
    "Check/Inspection Scripts": [
        "final_employee_check.py",
        "quick_db_check.py",
        "show_db_stats.py",
        "db_insights.py",
        "inspect_database.py",
        "complete_tool_audit.py",
        "audit_tool_ids.py",
    ],
    
    "Clear/Reset Scripts": [
        "clear_all_applications.py",
        "clear_vector_cache.py",
        "clear_faiss_cache.py",
        "clear_onboarding_tasks.py",
        "reset_bulk_hire.py",
        "reset_bharat_password.py",
        "reset_database.py",
        "reset_hiring_data.py",
        "reset_applications.py",
        "reset_sumit_data.py",
        "change_status_to_applied.py",
    ],
    
    "Generate/Temporary Data Scripts": [
        "generate_docs_offer4.py",
        "generate_embeddings.py",
        "generate_professional_profiles.py",
        "generate_realistic_data.py",
    ],
    
    "Analyze Scripts": [
        "analyze_jobs_34_35.py",
        "analyze_jobs.py",
        "analyze_dbs.py",
        "analyze_and_update_salaries.py",
    ],
    
    "Investigate/Debug Scripts": [
        "investigate_raw.py",
        "investigate_app_6.py",
    ],
    
    "Repair Scripts": [
        "repair_docs_7.py",
        "repair_job_count_471.py",
        "repair_offer_7.py",
        "repair_offer_7_v2.py",
    ],
    
    "Setup/Demo Scripts": [
        "setup_shohaib_for_demo.py",
        "trigger_autofill_now.py",
    ],
    
    "Enable Scripts": [
        "enable_autofill_all_jobs.py",
    ],
    
    "Temporary/Sample Files": [
        "cuisine_fix_log.txt",
        "offer_letter_sample.txt",
        "regenerated_offer_letter.txt",
        "tool_audit_results.txt",
        "add_interviews_endpoint.txt",
        "temp_applications_endpoint.py",
    ],
    
    "Database Backups": [
        "manpower_backup_before_cleanup_20260105_153844.db",
        "manpower_backup_before_rebuild_20260105_165911.db",
        "manpower_backup_before_rebuild_20260105_170058.db",
        "manpower_backup_before_rebuild_20260105_170411.db",
        "manpower_connector.db",
    ],
    
    "One-time Migration Scripts": [
        "add_arun_method.py",
        "add_auto_fill_column.py",
        "add_bio_column.py",
        "add_chat_persistence.py",
        "add_employer_hiring_preferences.py",
        "add_interviews_endpoint_script.py",
        "add_preferred_job_type.py",
        "add_profile_enhancements.py",
        "add_quantity_filled.py",
        "add_unique_application_constraint.py",
        "migrate_employee_fields.py",
        "remove_bio_column.py",
    ],
    
    "Utility/Sync Scripts": [
        "apply_universal_threshold.py",
        "assign_role_based_certifications.py",
        "auto_categorize_jobs.py",
        "autofill_job_fields.py",
        "backfill_onboarding_data.py",
        "backup_database.py",
        "compare_candidates.py",
        "complete_employee_data.py",
        "complete_job_data.py",
        "diversify_certifications.py",
        "employee_interviews_endpoint.py",
        "fetch_employer_data.py",
        "get_employer_profile.py",
        "get_nike_creds.py",
        "list_employees.py",
        "list_employers.py",
        "new_profile_loader.py",
        "nike_jobs.py",
        "populate_certifications.py",
        "realign_jobs_with_employers.py",
        "rebuild_jobs_from_prefs.py",
        "recalculate_match_scores.py",
        "regenerate_complete_documents.py",
        "regenerate_embeddings.py",
        "regenerate_employee_embeddings.py",
        "regenerate_employee_profiles.py",
        "regenerate_job_descriptions.py",
        "regenerate_job_embeddings.py",
        "regenerate_resume_texts.py",
        "remove_duplicate_jobs.py",
        "run_profile_analysis.py",
        "run_profile_analysis_standalone.py",
        "save_offer_letter.py",
        "send_interview_notification.py",
        "set_match_thresholds.py",
        "sync_descriptions.py",
        "sync_quantity_filled.py",
        "sync_vectors.py",
        "work_history_endpoint.py",
    ],
    
    "Redundant Documentation": [
        "APPLICATIONS_PAGE_ENHANCED.md",
        "BACKEND_FIX_SUMMARY.md",
        "CHAT_PERSISTENCE_FIX.md",
        "CURRENT_ISSUE_FIX.md",
        "IMPLEMENTATION_COMPLETE.md",
        "MATCH_THRESHOLD_IMPLEMENTATION.md",
        "ONBOARDING_ENHANCEMENT_COMPLETE.md",
        "REALTIME_DATA_FLOW_COMPLETE.md",
        "REALTIME_DATA_WORKING.md",
        "SLM_CACHING_STATUS.md",
        "STARTUP_ANALYSIS_CONFIGURED.md",
        "DATABASE_TESTING_EXPLAINED.md",
    ],
}

# Directories to remove
DIRS_TO_REMOVE = [
    "backend/tests",
    ".pytest_cache",
]


def get_file_size(filepath):
    """Get file size in human-readable format"""
    try:
        size = os.path.getsize(filepath)
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.2f} {unit}"
            size /= 1024.0
        return f"{size:.2f} TB"
    except:
        return "Unknown"


def main():
    print("=" * 70)
    print("REPOSITORY CLEANUP SCRIPT")
    print("=" * 70)
    print()
    
    total_removed = 0
    total_size_saved = 0
    failed_removals = []
    
    # Remove files
    for category, files in FILES_TO_REMOVE.items():
        print(f"\n{category}:")
        print("-" * 70)
        
        for filename in files:
            filepath = BASE_DIR / filename
            
            if filepath.exists():
                try:
                    file_size = os.path.getsize(filepath)
                    total_size_saved += file_size
                    
                    os.remove(filepath)
                    print(f"  ✓ Removed: {filename} ({get_file_size(filepath)})")
                    total_removed += 1
                except Exception as e:
                    print(f"  ✗ Failed to remove: {filename} - {str(e)}")
                    failed_removals.append((filename, str(e)))
            else:
                print(f"  - Not found: {filename}")
    
    # Remove directories
    print(f"\n\nDirectories:")
    print("-" * 70)
    
    for dirname in DIRS_TO_REMOVE:
        dirpath = BASE_DIR / dirname
        
        if dirpath.exists():
            try:
                # Calculate directory size
                dir_size = sum(f.stat().st_size for f in dirpath.rglob('*') if f.is_file())
                total_size_saved += dir_size
                
                shutil.rmtree(dirpath)
                print(f"  ✓ Removed directory: {dirname} ({get_file_size(dirpath)})")
                total_removed += 1
            except Exception as e:
                print(f"  ✗ Failed to remove directory: {dirname} - {str(e)}")
                failed_removals.append((dirname, str(e)))
        else:
            print(f"  - Not found: {dirname}")
    
    # Summary
    print("\n" + "=" * 70)
    print("CLEANUP SUMMARY")
    print("=" * 70)
    print(f"Total items removed: {total_removed}")
    print(f"Total space saved: {get_file_size(BASE_DIR / 'dummy') if total_size_saved == 0 else f'{total_size_saved / (1024*1024):.2f} MB'}")
    
    if failed_removals:
        print(f"\nFailed removals ({len(failed_removals)}):")
        for item, error in failed_removals:
            print(f"  - {item}: {error}")
    else:
        print("\n✓ All files removed successfully!")
    
    print("\n" + "=" * 70)
    print("Cleanup complete!")
    print("=" * 70)


if __name__ == "__main__":
    print("\n⚠️  WARNING: This will permanently delete files!")
    print("Make sure you have a backup if needed.\n")
    
    response = input("Do you want to proceed? (yes/no): ").strip().lower()
    
    if response == "yes":
        main()
    else:
        print("\nCleanup cancelled.")
