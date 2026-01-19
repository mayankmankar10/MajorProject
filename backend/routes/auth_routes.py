# backend/routes/auth_routes.py
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from backend.db.sql_db import SessionLocal
from backend.db.models import User, Employer, Employee, UserRole
from backend.utils.auth import get_password_hash, verify_password, create_access_token, get_current_user
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


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
    profile_id: int | None = None  # employee_id or employer_id
    is_active: bool
    created_at: datetime
    last_login: datetime | None = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class UserProfileResponse(BaseModel):
    user_id: int
    email: str
    role: str
    is_verified: bool
    profile: dict


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/register", response_model=TokenResponse)
def register(request: RegisterRequest, db: Session = Depends(get_db)):
    """Register a new user with role-based profile creation."""
    
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
        
        # Get profile ID based on role
        profile_id = None
        if request.role == UserRole.EMPLOYER:
            employer = db.query(Employer).filter(Employer.user_id == user.id).first()
            profile_id = employer.id if employer else None
        elif request.role == UserRole.EMPLOYEE:
            employee = db.query(Employee).filter(Employee.user_id == user.id).first()
            profile_id = employee.id if employee else None
        
        # Create access token
        token_data = {
            "user_id": user.id,
            "email": user.email,
            "role": user.role.value
        }
        access_token = create_access_token(token_data)
        
        logger.info(f"New user registered: {user.email} as {user.role.value} (profile_id={profile_id})")
        
        return TokenResponse(
            access_token=access_token,
            user=UserResponse(
                id=user.id,
                email=user.email,
                role=user.role.value,
                profile_id=profile_id,
                is_active=user.is_active,
                created_at=user.created_at,
                last_login=user.last_login
            )
        )
    
    except Exception as e:
        db.rollback()
        logger.error(f"Registration error: {e}")
        raise HTTPException(status_code=500, detail="Registration failed")


@router.post("/login", response_model=TokenResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """Authenticate user and return JWT token."""
    
    # Find user
    user = db.query(User).filter(User.email == request.email).first()
    
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    # Verify password
    if not verify_password(request.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    # Check if user is active
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is deactivated")
    
    # Update last login
    user.last_login = datetime.utcnow()
    db.commit()
    
    # Get profile ID based on role
    profile_id = None
    if user.role == UserRole.EMPLOYER:
        employer = db.query(Employer).filter(Employer.user_id == user.id).first()
        profile_id = employer.id if employer else None
    elif user.role == UserRole.EMPLOYEE:
        employee = db.query(Employee).filter(Employee.user_id == user.id).first()
        profile_id = employee.id if employee else None
    
    # Create access token
    token_data = {
        "user_id": user.id,
        "email": user.email,
        "role": user.role.value
    }
    access_token = create_access_token(token_data)
    
    logger.info(f"User logged in: {user.email} (profile_id={profile_id})")
    
    return TokenResponse(
        access_token=access_token,
        user=UserResponse(
            id=user.id,
            email=user.email,
            role=user.role.value,
            profile_id=profile_id,
            is_active=user.is_active,
            created_at=user.created_at,
            last_login=user.last_login
        )
    )


@router.get("/me", response_model=UserProfileResponse)
def get_current_user_profile(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get current user's profile information."""
    
    user = db.query(User).filter(User.id == current_user["user_id"]).first()
    
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
    
    return UserProfileResponse(
        user_id=user.id,
        email=user.email,
        role=user.role.value,
        is_verified=user.is_verified,
        profile=profile
    )


@router.post("/verify-token")
def verify_token(current_user: dict = Depends(get_current_user)):
    """Verify if token is valid."""
    return {"valid": True, "user_id": current_user["user_id"], "role": current_user["role"]}
