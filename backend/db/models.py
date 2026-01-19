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
    SHORTLISTED = "shortlisted" # NEW
    INTERVIEW_SCHEDULED = "interview_scheduled"  # Legacy, for traditional flow
    OFFER_SENT = "offer_sent"           # AI auto-selected, offer dispatched
    OFFER_ACCEPTED = "offer_accepted"   # Employee accepted the offer
    OFFER_DECLINED = "offer_declined"   # Employee declined the offer
    SELECTED = "selected"               # Legacy, keep for compatibility
    REJECTED = "rejected"
    HIRED = "hired"
    # End of status enum


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

# Restaurant-specific enums
class RestaurantRole(str, enum.Enum):
    WAITER = "waiter"
    COOK = "cook"
    CHEF = "chef"
    BARTENDER = "bartender"
    HOST = "host"
    DISHWASHER = "dishwasher"

class JobCategory(str, enum.Enum):
    WAITER = "waiter"
    COOK = "cook"
    CHEF = "chef"
    BARTENDER = "bartender"
    HOST = "host"
    DISHWASHER = "dishwasher"
    OTHER = "other"

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
    
    # Hiring preferences/templates
    hiring_preferences = Column(JSON, default=list)  # List of {role, positions, location, shift, salary_min, salary_max}
    
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
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    # Restaurant-specific fields
    food_safety_certified = Column(Boolean, default=False, index=True)
    servsafe_certified = Column(Boolean, default=False)
    alcohol_service_certified = Column(Boolean, default=False)
    preferred_role = Column(Enum(RestaurantRole), nullable=True, index=True)
    cuisine_experience = Column(JSON, default=list)  # ["Italian", "Chinese", "French"]
    shift_preferences = Column(JSON, default=list)  # ["morning", "evening", "weekends"]
    preferred_shift = Column(String, nullable=True)  # Single preferred shift from onboarding
    years_in_hospitality = Column(Integer, default=0)
    preferred_job_type = Column(JSON, default=list)  # ["full_time", "part_time", "contract"]
    expected_salary_min = Column(Integer, nullable=True)  # Minimum expected salary
    expected_salary_max = Column(Integer, nullable=True)  # Maximum expected salary
    last_profile_analysis = Column(DateTime, nullable=True)
    profile_summary = Column(Text, nullable=True)  # Cached summary from ProfileAnalyzerTool
    
    # Profile enhancement fields
    soft_skills = Column(JSON, default=list)  # ["Communication", "Leadership", "Teamwork"]
    work_history = Column(JSON, default=list)  # [{"employer": "...", "position": "...", ...}]    
    # Relationships
    user = relationship("User", back_populates="employee_profile")
    applications = relationship("Application", back_populates="employee")
    onboarding_tasks = relationship("OnboardingTask", back_populates="employee")
    onboarding_progress = relationship("OnboardingProgress", back_populates="employee", uselist=False)

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
    match_score_threshold = Column(Float, default=0.50)  # Universal default: 50% threshold
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    # Restaurant-specific fields
    cuisine_type = Column(String, index=True, nullable=True)  # "Italian", "Chinese", "Mexican", etc.
    shift_type = Column(String, nullable=True)  # "morning", "afternoon", "evening", "night"
    requires_food_safety = Column(Boolean, default=True)
    requires_alcohol_cert = Column(Boolean, default=False)
    min_hospitality_experience = Column(Integer, default=0)  # Years
    job_category = Column(Enum(JobCategory), nullable=True, index=True)
    quantity_needed = Column(Integer, default=1)  # For bulk hiring requests
    quantity_filled = Column(Integer, default=0)  # Track hired positions
    auto_fill_on_decline = Column(Boolean, default=False)  # Auto-send to next candidate when declined
    
    # Relationships
    employer = relationship("Employer", back_populates="jobs")
    applications = relationship("Application", back_populates="job")

class Application(Base):
    __tablename__ = "applications"
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    status = Column(String, default=ApplicationStatus.APPLIED.value)
    match_score = Column(Float, nullable=True)  # Semantic similarity score
    cover_letter = Column(Text, nullable=True)
    applied_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
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

class Offer(Base):
    """
    Tracks job offers sent to employees via the autonomous hiring pipeline.
    Links generated documents (offer letter, NDA) to the application.
    """
    __tablename__ = "offers"
    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("applications.id"), unique=True, nullable=False)
    
    # Offer details
    offer_letter_content = Column(Text, nullable=True)  # Generated offer letter
    nda_content = Column(Text, nullable=True)  # Generated NDA
    salary_offered = Column(String, nullable=True)
    start_date = Column(DateTime, nullable=True)
    additional_terms = Column(JSON, nullable=True)  # Shift, location, etc.
    
    # Status tracking
    status = Column(String, default="pending", index=True)  # pending, accepted, declined, expired
    sent_at = Column(DateTime, default=datetime.datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)  # Optional expiry
    responded_at = Column(DateTime, nullable=True)
    
    # Digital signing simulation
    offer_signed = Column(Boolean, default=False)
    nda_signed = Column(Boolean, default=False)
    signed_at = Column(DateTime, nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    # Relationship
    application = relationship("Application", backref="offer")

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
    meta_data = Column(JSON, nullable=True)  # Additional context
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    read_at = Column(DateTime, nullable=True)
    
    # Relationships
    recipient = relationship("User", back_populates="notifications", foreign_keys=[recipient_id])

class ProfileCache(Base):
    """
    Cache for analyzed employee profiles.
    Stores GPT-4 analysis results to avoid re-processing.
    """
    __tablename__ = "profile_cache"
    
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), unique=True, nullable=False)
    
    # Cached analysis from ProfileAnalyzerTool
    professional_summary = Column(Text)
    experience_level = Column(String)  # "entry", "mid", "senior"
    top_skills = Column(JSON)  # ["customer service", "multitasking", ...]
    recommended_roles = Column(JSON)  # ["waiter", "server", "host"]
    strengths = Column(JSON)  # ["Friendly personality", "Fast learner"]
    
    # Metadata
    analyzed_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    cache_version = Column(Integer, default=1)  # For invalidation strategy
    is_stale = Column(Boolean, default=False)  # Mark for re-analysis
    
    # Relationship
    employee = relationship("Employee", backref="cached_profile", foreign_keys=[employee_id])

class OnboardingProgress(Base):
    """
    Track employee onboarding progress through chat-based onboarding.
    Each step is completed through conversation with the AI assistant.
    """
    __tablename__ = "onboarding_progress"
    
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), unique=True, nullable=False, index=True)
    
    # Onboarding steps completion status
    profile_completed = Column(Boolean, default=False)  # Name, phone, location
    skills_completed = Column(Boolean, default=False)  # Experience, skills
    preferences_completed = Column(Boolean, default=False)  # Shifts, cuisine, role
    certifications_completed = Column(Boolean, default=False)  # Food safety, etc.
    documents_completed = Column(Boolean, default=False)  # Resume upload
    
    # Current state
    current_step = Column(String, default="profile")  # profile, skills, preferences, certifications, documents, complete
    is_complete = Column(Boolean, default=False, index=True)
    completion_percentage = Column(Integer, default=0)  # 0-100
    
    # Timestamps
    started_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    last_updated = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    # Relationship
    employee = relationship("Employee", back_populates="onboarding_progress")

class ChatSession(Base):
    """
    Represents a chat conversation session between a user and the AI assistant.
    Sessions are persistent and survive beyond Redis TTL.
    """
    __tablename__ = "chat_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, unique=True, nullable=False, index=True)  # UUID
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String, nullable=True)  # Auto-generated from first message
    
    # Metadata
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    last_message_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    user = relationship("User", backref="chat_sessions", foreign_keys=[user_id])
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")

class ChatMessage(Base):
    """
    Individual chat messages within a session.
    Stores both user messages and AI responses.
    """
    __tablename__ = "chat_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id"), nullable=False, index=True)
    role = Column(String, nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False, index=True)
    
    # Relationship
    session = relationship("ChatSession", back_populates="messages")
