# backend/db/models.py
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Boolean, Float, JSON, Enum
from sqlalchemy.orm import relationship
from backend.db.sql_db import Base
import datetime
import enum

# Enums for type safety
class UserRole(str, enum.Enum):
    EMPLOYER = "employer"
    EMPLOYEE = "employee"

class ApplicationStatus(str, enum.Enum):
    APPLIED = "applied"
    REVIEWING = "reviewing"
    INTERVIEW_SCHEDULED = "interview_scheduled"
    SELECTED = "selected"
    REJECTED = "rejected"
    HIRED = "hired"

class InterviewStatus(str, enum.Enum):
    SCHEDULED = "scheduled"
    CONFIRMED = "confirmed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class OnboardingTaskType(str, enum.Enum):
    OFFER_LETTER = "offer_letter"
    NDA = "nda"
    CHECKLIST = "checklist"
    DOCUMENT_UPLOAD = "document_upload"

class OnboardingTaskStatus(str, enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"

# User model - unified authentication
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(Enum(UserRole), nullable=False)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    
    # Relationships
    employer_profile = relationship("Employer", back_populates="user", uselist=False)
    employee_profile = relationship("Employee", back_populates="user", uselist=False)
    notifications = relationship("Notification", back_populates="recipient", foreign_keys="Notification.recipient_id")

class Employer(Base):
    __tablename__ = "employers"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    company_name = Column(String, index=True, nullable=False)
    company_profile = Column(Text, nullable=True)
    industry = Column(String, nullable=True)
    location = Column(String, nullable=True)
    website = Column(String, nullable=True)
    verification_status = Column(String, default="pending")  # pending, verified, rejected
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="employer_profile")
    jobs = relationship("Job", back_populates="employer")

class Employee(Base):
    __tablename__ = "employees"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    full_name = Column(String, index=True, nullable=False)
    phone = Column(String, nullable=True)
    resume_text = Column(Text, nullable=True)
    resume_filename = Column(String, nullable=True)
    skills = Column(JSON, nullable=True)  # ["Python", "FastAPI", ...]
    experience_years = Column(Float, nullable=True)
    certifications = Column(JSON, nullable=True)  # [{"name": "...", "issuer": "..."}]
    education = Column(JSON, nullable=True)
    preferred_location = Column(String, nullable=True)
    availability = Column(String, default="immediate")  # immediate, 2_weeks, 1_month
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="employee_profile")
    applications = relationship("Application", back_populates="employee")
    onboarding_tasks = relationship("OnboardingTask", back_populates="employee")

class Job(Base):
    __tablename__ = "jobs"
    id = Column(Integer, primary_key=True, index=True)
    employer_id = Column(Integer, ForeignKey("employers.id"), nullable=False)
    title = Column(String, index=True, nullable=False)
    description = Column(Text, nullable=False)
    enhanced_description = Column(Text, nullable=True)  # GPT-4 enhanced version
    requirements = Column(JSON, nullable=True)  # {"skills": [], "experience": 2, "certifications": []}
    location = Column(String, nullable=True)
    job_type = Column(String, default="full_time")  # full_time, part_time, contract
    salary_range = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    match_score_threshold = Column(Float, default=0.6)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    # Relationships
    employer = relationship("Employer", back_populates="jobs")
    applications = relationship("Application", back_populates="job")

class Application(Base):
    __tablename__ = "applications"
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    status = Column(Enum(ApplicationStatus), default=ApplicationStatus.APPLIED)
    match_score = Column(Float, nullable=True)  # Semantic similarity score
    cover_letter = Column(Text, nullable=True)
    applied_at = Column(DateTime, default=datetime.datetime.utcnow)
    reviewed_at = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)  # Employer notes
    
    # Relationships
    job = relationship("Job", back_populates="applications")
    employee = relationship("Employee", back_populates="applications")
    interview = relationship("Interview", back_populates="application", uselist=False)

class Interview(Base):
    __tablename__ = "interviews"
    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("applications.id"), unique=True, nullable=False)
    scheduled_at = Column(DateTime, nullable=False)
    duration_minutes = Column(Integer, default=60)
    location = Column(String, nullable=True)
    meeting_link = Column(String, nullable=True)  # Video call link
    calendar_link = Column(String, nullable=True)
    status = Column(Enum(InterviewStatus), default=InterviewStatus.SCHEDULED)
    interviewer_notes = Column(Text, nullable=True)
    feedback = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    # Relationships
    application = relationship("Application", back_populates="interview")

class OnboardingTask(Base):
    __tablename__ = "onboarding_tasks"
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False)
    task_type = Column(Enum(OnboardingTaskType), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    status = Column(Enum(OnboardingTaskStatus), default=OnboardingTaskStatus.PENDING)
    document_url = Column(String, nullable=True)  # Generated document path
    document_content = Column(Text, nullable=True)  # LLM-generated content
    deadline = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Relationships
    employee = relationship("Employee", back_populates="onboarding_tasks")

class Notification(Base):
    __tablename__ = "notifications"
    id = Column(Integer, primary_key=True, index=True)
    recipient_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    notification_type = Column(String, nullable=False)  # job_match, interview, application, onboarding
    action_url = Column(String, nullable=True)  # Link to relevant page
    metadata = Column(JSON, nullable=True)  # Additional context
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    read_at = Column(DateTime, nullable=True)
    
    # Relationships
    recipient = relationship("User", back_populates="notifications", foreign_keys=[recipient_id])
