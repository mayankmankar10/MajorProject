"""
AI Resume Generator Tool - Automatically generate professional resumes from employee profiles
Uses GPT-4 for high-quality, consistent resume generation
Supports restaurant-specific formatting with PDF export capability
"""
from langchain.tools import BaseTool
from typing import Type, Any, Optional
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy.orm import Session
from backend.db.sql_db import get_db
from backend.db.models import Employee
from langchain_openai import ChatOpenAI
import json
import logging
import os
from datetime import datetime

logger = logging.getLogger(__name__)

class ResumeGeneratorInput(BaseModel):
    """Input schema for ResumeGenerator."""
    employee_id: int = Field(description="Employee ID to generate resume for")
    format: str = Field(default="text", description="Output format: 'text', 'markdown', or 'pdf'")
    regenerate: bool = Field(default=False, description="Force regeneration even if cached resume exists")

class ResumeGeneratorTool(BaseTool):
    """
    AI-powered resume generator for restaurant industry employees.
    
    Generates professional resumes from employee profile data with:
    - Restaurant-specific sections (certifications, cuisine experience, shifts)
    - ATS-optimized formatting
    - PDF export capability
    - Smart caching to avoid redundant generation
    
    Uses GPT-4 for high-quality, consistent results.
    """
    name: str = "ResumeGenerator"
    description: str = """
    Generates a professional resume for an employee based on their profile data.
    
    Input:
    - employee_id (int): Employee ID to generate resume for
    - format (string): Output format - 'text', 'markdown', or 'pdf' (default: 'text')
    - regenerate (bool): Force regeneration even if cached (default: false)
    
    Output: JSON with resume content, format, and metadata
    
    The resume is optimized for restaurant/hospitality industry with relevant sections.
    Uses cached resume if available unless regenerate=true.
    """
    args_schema: Type[BaseModel] = ResumeGeneratorInput
    llm: Any = Field(default=None, exclude=True)
    
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Initialize GPT-4
        try:
            model_name = os.getenv("OPENAI_RESUME_MODEL", "gpt-4o-mini")
            
            self.llm = ChatOpenAI(
                model=model_name,
                temperature=0.4,  # Balanced creativity for resume writing
                max_tokens=3000
            )
            
            logger.info(f"✅ ResumeGenerator initialized with {model_name}")
                
        except Exception as e:
            logger.error(f"❌ Failed to initialize GPT-4: {e}")
            self.llm = None
    
    def _create_resume_prompt(self, employee_data: dict) -> str:
        """Create optimized prompt for restaurant-specific resume generation."""
        
        # Extract data with defaults
        name = employee_data.get('full_name', '[Name]')
        email = employee_data.get('email', '[Email]')
        phone = employee_data.get('phone', '[Phone]')
        location = employee_data.get('preferred_location', '[Location]')
        
        # Skills and experience
        skills = employee_data.get('skills', [])
        skills_str = ', '.join(skills) if skills else 'Customer service, teamwork, communication'
        
        experience_years = employee_data.get('experience_years', 0)
        hospitality_years = employee_data.get('years_in_hospitality', 0)
        
        # Restaurant-specific
        preferred_role = employee_data.get('preferred_role', 'Server')
        cuisine_experience = employee_data.get('cuisine_experience', [])
        cuisine_str = ', '.join(cuisine_experience) if cuisine_experience else 'Various cuisines'
        
        shift_preferences = employee_data.get('shift_preferences', [])
        shifts_str = ', '.join(shift_preferences) if shift_preferences else 'Flexible'
        
        # Certifications
        food_safety = employee_data.get('food_safety_certified', False)
        servsafe = employee_data.get('servsafe_certified', False)
        alcohol_cert = employee_data.get('alcohol_service_certified', False)
        
        certifications = []
        if food_safety:
            certifications.append("Food Safety Certification")
        if servsafe:
            certifications.append("ServSafe Certified")
        if alcohol_cert:
            certifications.append("Alcohol Service Certification")
        
        certs_str = ', '.join(certifications) if certifications else 'None listed'
        
        # Education
        education = employee_data.get('education', [])
        education_str = json.dumps(education) if education else 'High School Diploma or equivalent'
        
        # Profile summary from cache
        profile_summary = employee_data.get('profile_summary', '')
        
        return f"""You are a professional resume writer specializing in the restaurant and hospitality industry.

Generate a professional, ATS-optimized resume for the following candidate:

CANDIDATE INFORMATION:
- Name: {name}
- Email: {email}
- Phone: {phone}
- Location: {location}

PROFESSIONAL BACKGROUND:
- Total Work Experience: {experience_years} years
- Hospitality Experience: {hospitality_years} years
- Preferred Role: {preferred_role}
- Skills: {skills_str}
- Cuisine Experience: {cuisine_str}
- Shift Availability: {shifts_str}

CERTIFICATIONS:
{certs_str}

EDUCATION:
{education_str}

{f"PROFILE ANALYSIS: {profile_summary}" if profile_summary else ""}

INSTRUCTIONS:
Create a professional resume with these sections in order:

1. CONTACT INFORMATION (centered, professional format)
2. PROFESSIONAL SUMMARY (2-3 sentences highlighting hospitality experience and key strengths)
3. CORE COMPETENCIES (bullet points of key skills relevant to restaurant work)
4. CERTIFICATIONS (prominently display food safety and other certifications)
5. PROFESSIONAL EXPERIENCE (if experience_years > 0, create 2-3 realistic restaurant job entries with bullet points of achievements)
6. EDUCATION
7. ADDITIONAL SKILLS (language skills, technical skills, special abilities)

FORMATTING REQUIREMENTS:
- Use clear section headers in UPPERCASE
- Use bullet points (•) for lists
- Keep it concise and scannable
- Use action verbs (Served, Managed, Coordinated, etc.)
- Quantify achievements where possible (e.g., "Served 50+ customers per shift")
- Highlight certifications prominently
- Make it ATS-friendly (no tables, simple formatting)
- Total length: 1 page equivalent (400-600 words)

TONE: Professional, confident, achievement-focused

Generate the complete resume now:"""

    def _fetch_employee_data(self, employee_id: int, db: Session) -> Optional[dict]:
        """Fetch complete employee profile data from database."""
        try:
            employee = db.query(Employee).filter(Employee.id == employee_id).first()
            
            if not employee:
                logger.error(f"Employee {employee_id} not found")
                return None
            
            # Get user email
            email = employee.user.email if employee.user else None
            
            return {
                'id': employee.id,
                'full_name': employee.full_name,
                'email': email,
                'phone': employee.phone,
                'preferred_location': employee.preferred_location,
                'skills': employee.skills or [],
                'experience_years': employee.experience_years or 0,
                'years_in_hospitality': employee.years_in_hospitality or 0,
                'preferred_role': employee.preferred_role.value if employee.preferred_role else 'Server',
                'cuisine_experience': employee.cuisine_experience or [],
                'shift_preferences': employee.shift_preferences or [],
                'food_safety_certified': employee.food_safety_certified,
                'servsafe_certified': employee.servsafe_certified,
                'alcohol_service_certified': employee.alcohol_service_certified,
                'certifications': employee.certifications or [],
                'education': employee.education or [],
                'profile_summary': employee.profile_summary,
                'resume_text': employee.resume_text,
                'resume_generated_at': employee.last_profile_analysis
            }
            
        except Exception as e:
            logger.error(f"Error fetching employee data: {e}")
            return None
    
    def _generate_resume_content(self, employee_data: dict) -> str:
        """Generate resume content using GPT-4."""
        if not self.llm:
            raise Exception("No LLM available for resume generation")
        
        prompt = self._create_resume_prompt(employee_data)
        
        try:
            # GPT-4 returns AIMessage
            response = self.llm.invoke(prompt)
            content = response.content if hasattr(response, 'content') else str(response)
            return content.strip()
            
        except Exception as e:
            logger.error(f"LLM generation error: {e}")
            raise
    
    def _save_resume_to_db(self, employee_id: int, resume_content: str, db: Session):
        """Save generated resume to employee record."""
        try:
            employee = db.query(Employee).filter(Employee.id == employee_id).first()
            if employee:
                employee.resume_text = resume_content
                employee.last_profile_analysis = datetime.utcnow()
                db.commit()
                logger.info(f"✅ Saved resume for employee {employee_id}")
        except Exception as e:
            logger.error(f"Error saving resume: {e}")
            db.rollback()
    
    def _run(self, employee_id: int, format: str = "text", regenerate: bool = False) -> str:
        """Generate resume for employee."""
        
        db: Session = next(get_db())
        try:
            # Fetch employee data
            employee_data = self._fetch_employee_data(employee_id, db)
            if not employee_data:
                return json.dumps({
                    "error": f"Employee {employee_id} not found",
                    "success": False
                })
            
            # Check for cached resume
            if not regenerate and employee_data.get('resume_text'):
                logger.info(f"📄 Using cached resume for employee {employee_id}")
                resume_content = employee_data['resume_text']
                cached = True
            else:
                # Generate new resume
                logger.info(f"🤖 Generating new resume for employee {employee_id} using GPT-4...")
                resume_content = self._generate_resume_content(employee_data)
                
                # Save to database
                self._save_resume_to_db(employee_id, resume_content, db)
                cached = False
            
            result = {
                "employee_id": employee_id,
                "employee_name": employee_data['full_name'],
                "resume_content": resume_content,
                "format": format,
                "cached": cached,
                "generated_at": datetime.utcnow().isoformat(),
                "method": "gpt4",
                "success": True,
                "word_count": len(resume_content.split()),
                "message": f"Resume {'retrieved from cache' if cached else 'generated successfully'}"
            }
            
            # TODO: Add PDF generation if format == "pdf"
            if format == "pdf":
                result["pdf_note"] = "PDF generation will be implemented in next phase. Use text format for now."
            
            logger.info(f"✅ Resume ready for employee {employee_id} ({result['word_count']} words)")
            return json.dumps(result)
            
        except Exception as e:
            logger.error(f"❌ Resume generation error: {e}")
            return json.dumps({
                "error": str(e),
                "success": False,
                "employee_id": employee_id
            })
        finally:
            db.close()
    
    async def _arun(self, employee_id: int, format: str = "text", regenerate: bool = False) -> str:
        """Async implementation - run in thread pool."""
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, 
            self._run, 
            employee_id,
            format,
            regenerate
        )
