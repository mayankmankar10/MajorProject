# backend/routes/registration_routes.py
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from backend.db.sql_db import SessionLocal
from backend.db.models import User, Employer, Employee, UserRole
from backend.utils.auth import get_password_hash
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["Registration"])


# Pydantic models
class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    role: UserRole
    # Role-specific fields
    company_name: str | None = None  # For employer
    full_name: str | None = None  # For employee


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    email: str
    role: str
    profile_id: int | None = None  # employee_id or employer_id for role-specific operations
    is_active: bool
    created_at: datetime


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/register", response_model=TokenResponse)
def register(request: RegisterRequest, db: Session = Depends(get_db)):
    """Register a new user with role-based profile creation (no auth required for testing)."""
    
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == request.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Validate role-specific fields
    if request.role == UserRole.EMPLOYER and not request.company_name:
        raise HTTPException(status_code=400, detail="Company name required for employer registration")
    
    if request.role == UserRole.EMPLOYEE and not request.full_name:
        raise HTTPException(status_code=400, detail="Full name required for employee registration")
    
    try:
        # Create user
        user = User(
            email=request.email,
            hashed_password=get_password_hash(request.password),
            role=request.role,
            is_active=True,
            is_verified=False
        )
        db.add(user)
        db.flush()  # Get user.id without committing
        
        # Create role-specific profile
        if request.role == UserRole.EMPLOYER:
            employer = Employer(
                user_id=user.id,
                company_name=request.company_name,
                verification_status="pending"
            )
            db.add(employer)
        
        elif request.role == UserRole.EMPLOYEE:
            employee = Employee(
                user_id=user.id,
                full_name=request.full_name
            )
            db.add(employee)
        
        db.commit()
        db.refresh(user)
        
        # Get the profile ID based on role
        profile_id = None
        if request.role == UserRole.EMPLOYER:
            employer_profile = db.query(Employer).filter(Employer.user_id == user.id).first()
            if employer_profile:
                profile_id = employer_profile.id
        elif request.role == UserRole.EMPLOYEE:
            employee_profile = db.query(Employee).filter(Employee.user_id == user.id).first()
            if employee_profile:
                profile_id = employee_profile.id
        
        logger.info(f"New user registered: {user.email} as {user.role.value}")
        
        # Create mock access token
        from backend.utils.auth import create_access_token
        token_data = {"user_id": user.id, "role": user.role.value}
        access_token = create_access_token(token_data)
        
        # Build user response with both user_id and profile_id
        user_response = UserResponse(
            id=user.id,  # user_id for authentication
            email=user.email,
            role=user.role.value,
            profile_id=profile_id,  # employee_id or employer_id for role operations
            is_active=user.is_active,
            created_at=user.created_at
        )
        
        return TokenResponse(
            access_token=access_token,
            user=user_response
        )
    
    except Exception as e:
        db.rollback()
        logger.error(f"Registration error: {e}")
        raise HTTPException(status_code=500, detail="Registration failed")


@router.post("/login", response_model=TokenResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """Simple login without JWT - just validates credentials and returns user info."""
    
    # Find user
    user = db.query(User).filter(User.email == request.email).first()
    
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    # Verify password using mock function
    from backend.utils.auth import verify_password
    if not verify_password(request.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    # Check if user is active
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is deactivated")
    
    logger.info(f"User logged in: {user.email}")
    
    # Get the profile ID based on role
    profile_id = None
    if user.role == UserRole.EMPLOYER:
        employer_profile = db.query(Employer).filter(Employer.user_id == user.id).first()
        if employer_profile:
            profile_id = employer_profile.id
    elif user.role == UserRole.EMPLOYEE:
        employee_profile = db.query(Employee).filter(Employee.user_id == user.id).first()
        if employee_profile:
            profile_id = employee_profile.id
    
    # Create mock access token
    from backend.utils.auth import create_access_token
    token_data = {"user_id": user.id, "role": user.role.value}
    access_token = create_access_token(token_data)
    
    return TokenResponse(
        access_token=access_token,
        user=UserResponse(
            id=user.id,  # user_id for authentication
            email=user.email,
            role=user.role.value,
            profile_id=profile_id,  # employee_id or employer_id for role operations
            is_active=user.is_active,
            created_at=user.created_at
        )
    )


@router.post("/verify-token")
def verify_token():
    """Mock token verification - always returns success for testing."""
    # In testing mode, just return success without actual validation
    # The frontend checks this to maintain session
    return {"valid": True, "message": "Token is valid"}


@router.get("/me")
def get_me():
    """Mock current user endpoint - returns placeholder."""
    # Without actual auth, we can't identify the current user
    # Frontend should rely on localStorage instead
    return {
        "message": "Use localStorage to get current user in testing mode",
        "user": None
    }


@router.get("/users")
def list_users(db: Session = Depends(get_db)):
    """List all registered users (for testing purposes)."""
    users = db.query(User).all()
    return [
        {
            "id": user.id,
            "email": user.email,
            "role": user.role.value,
            "is_active": user.is_active,
            "created_at": user.created_at
        }
        for user in users
    ]


@router.get("/user/{user_id}")
def get_user(user_id: int, db: Session = Depends(get_db)):
    """Get user details by ID (for testing purposes)."""
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Build profile based on role
    profile = {}
    
    if user.role == UserRole.EMPLOYER and user.employer_profile:
        emp = user.employer_profile
        profile = {
            "employer_id": emp.id,
            "company_name": emp.company_name,
            "company_profile": emp.company_profile,
            "industry": emp.industry,
            "location": emp.location,
            "website": emp.website,
            "verification_status": emp.verification_status
        }
    
    elif user.role == UserRole.EMPLOYEE and user.employee_profile:
        emp = user.employee_profile
        profile = {
            "employee_id": emp.id,
            "full_name": emp.full_name,
            "phone": emp.phone,
            "skills": emp.skills,
            "experience_years": emp.experience_years,
            "certifications": emp.certifications,
            "education": emp.education,
            "preferred_location": emp.preferred_location,
            "availability": emp.availability
        }
    
    return {
        "user_id": user.id,
        "email": user.email,
        "role": user.role.value,
        "is_verified": user.is_verified,
        "profile": profile
    }
