"""
Helper utility to add login credentials to notifications for easier testing.
This allows you to see which users are involved without accessing the database.
"""
from sqlalchemy.orm import Session
from backend.db.models import User, Employee, Employer
import logging

logger = logging.getLogger(__name__)

def get_user_credentials(db: Session, user_id: int) -> dict:
    """
    Get user login credentials for notification metadata.
    
    Returns:
        dict with email, role, and name
    """
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return {"email": "unknown", "role": "unknown"}
        
        credentials = {
            "email": user.email,
            "role": user.role.value if hasattr(user.role, 'value') else str(user.role),
            "user_id": user.id
        }
        
        # Add name based on role
        if user.role.value == "employee":
            employee = db.query(Employee).filter(Employee.user_id == user_id).first()
            if employee:
                credentials["name"] = employee.full_name
        elif user.role.value == "employer":
            employer = db.query(Employer).filter(Employer.user_id == user_id).first()
            if employer:
                credentials["name"] = employer.company_name
        
        return credentials
    except Exception as e:
        logger.error(f"Error getting user credentials: {e}")
        return {"email": "error", "role": "unknown"}

def add_credentials_to_notification_metadata(
    db: Session, 
    recipient_id: int, 
    sender_id: int = None,
    existing_metadata: dict = None
) -> dict:
    """
    Add login credentials to notification metadata.
    
    Args:
        db: Database session
        recipient_id: User ID of notification recipient
        sender_id: User ID of notification sender (optional)
        existing_metadata: Existing metadata to merge with
        
    Returns:
        Updated metadata dict with credentials
    """
    metadata = existing_metadata.copy() if existing_metadata else {}
    
    # Add recipient credentials
    recipient_creds = get_user_credentials(db, recipient_id)
    metadata["recipient_credentials"] = {
        "email": recipient_creds.get("email"),
        "role": recipient_creds.get("role"),
        "name": recipient_creds.get("name", "Unknown")
    }
    
    # Add sender credentials if provided
    if sender_id:
        sender_creds = get_user_credentials(db, sender_id)
        metadata["sender_credentials"] = {
            "email": sender_creds.get("email"),
            "role": sender_creds.get("role"),
            "name": sender_creds.get("name", "Unknown")
        }
    
    # Add a helpful note for testing
    metadata["_testing_note"] = "Use these credentials to log in and test the notification flow"
    
    return metadata
