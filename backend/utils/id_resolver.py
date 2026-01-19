"""
ID Resolution Utilities

This module provides helper functions to resolve between different ID types:
- user_id (users table primary key)
- employee_id (employees table primary key)  
- employer_id (employers table primary key)

These utilities ensure consistent ID handling across all tools and routes.
"""

from sqlalchemy.orm import Session
from backend.db.models import Employee, Employer, User
from typing import Optional
import logging

logger = logging.getLogger(__name__)


def get_employee_id_from_user(db: Session, user_id: int) -> int:
    """
    Resolve user_id to employee_id.
    
    Args:
        db: Database session
        user_id: User ID from users table
        
    Returns:
        employee_id: Employee ID from employees table
        
    Raises:
        ValueError: If no employee found for user_id
    """
    employee = db.query(Employee).filter(Employee.user_id == user_id).first()
    if not employee:
        raise ValueError(f"No employee profile found for user_id {user_id}")
    return employee.id


def get_employer_id_from_user(db: Session, user_id: int) -> int:
    """
    Resolve user_id to employer_id.
    
    Args:
        db: Database session
        user_id: User ID from users table
        
    Returns:
        employer_id: Employer ID from employers table
        
    Raises:
        ValueError: If no employer found for user_id
    """
    employer = db.query(Employer).filter(Employer.user_id == user_id).first()
    if not employer:
        raise ValueError(f"No employer profile found for user_id {user_id}")
    return employer.id


def get_user_id_from_employee(db: Session, employee_id: int) -> int:
    """
    Resolve employee_id to user_id.
    
    Args:
        db: Database session
        employee_id: Employee ID from employees table
        
    Returns:
        user_id: User ID from users table
        
    Raises:
        ValueError: If no employee found for employee_id
    """
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise ValueError(f"No employee found for employee_id {employee_id}")
    return employee.user_id


def get_user_id_from_employer(db: Session, employer_id: int) -> int:
    """
    Resolve employer_id to user_id.
    
    Args:
        db: Database session
        employer_id: Employer ID from employers table
        
    Returns:
        user_id: User ID from users table
        
    Raises:
        ValueError: If no employer found for employer_id
    """
    employer = db.query(Employer).filter(Employer.id == employer_id).first()
    if not employer:
        raise ValueError(f"No employer found for employer_id {employer_id}")
    return employer.user_id


def get_employee_from_application(db: Session, application_id: int) -> Employee:
    """
    Get employee record from application_id.
    
    Args:
        db: Database session
        application_id: Application ID
        
    Returns:
        Employee object
        
    Raises:
        ValueError: If application or employee not found
    """
    from backend.db.models import Application
    
    application = db.query(Application).filter(Application.id == application_id).first()
    if not application:
        raise ValueError(f"No application found for application_id {application_id}")
    
    employee = db.query(Employee).filter(Employee.id == application.employee_id).first()
    if not employee:
        raise ValueError(f"No employee found for application {application_id}")
    
    return employee


def safe_get_employee_id(db: Session, user_id: int) -> Optional[int]:
    """
    Safely resolve user_id to employee_id, returning None if not found.
    
    Args:
        db: Database session
        user_id: User ID
        
    Returns:
        employee_id or None
    """
    try:
        return get_employee_id_from_user(db, user_id)
    except ValueError:
        logger.warning(f"Could not resolve user_id {user_id} to employee_id")
        return None


def safe_get_employer_id(db: Session, user_id: int) -> Optional[int]:
    """
    Safely resolve user_id to employer_id, returning None if not found.
    
    Args:
        db: Database session
        user_id: User ID
        
    Returns:
        employer_id or None
    """
    try:
        return get_employer_id_from_user(db, user_id)
    except ValueError:
        logger.warning(f"Could not resolve user_id {user_id} to employer_id")
        return None
