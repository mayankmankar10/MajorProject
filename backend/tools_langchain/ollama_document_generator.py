"""
Document Generator - Fast document generation using Google Gemini (new google.genai package).
Uses Gemini Flash for professional offer letters and NDAs.
"""
from langchain.tools import BaseTool
from typing import Type, Any
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy.orm import Session
from backend.db.sql_db import get_db
from backend.db.models import OnboardingTask, OnboardingTaskType, OnboardingTaskStatus
import json
import logging
import os

logger = logging.getLogger(__name__)

class DocumentGeneratorInput(BaseModel):
    """Input schema for DocumentGenerator."""
    employee_id: int = Field(description="Employee ID for onboarding")
    job_id: int = Field(description="Job ID they were hired for")
    document_type: str = Field(description="Type: 'offer_letter' or 'nda'")
    context_data: str = Field(description="JSON string with context (salary, start_date, company_name, etc.)")

class OllamaDocumentGenerator(BaseTool):
    """
    Fast document generation using Google Gemini.
    
    Performance: 3-5x faster than GPT-4o
    Cost: 90% cheaper than GPT-4o
    Quality: Excellent for template-based documents
    
    Automatically falls back to GPT-4o-mini if Gemini unavailable.
    """
    name: str = "OllamaDocumentGenerator"
    description: str = """
    Generates professional onboarding documents using Gemini (ultra-fast and cheap).
    
    Input:
    - employee_id (int): Employee ID
    - job_id (int): Job ID
    - document_type (string): Either 'offer_letter' or 'nda'
    - context_data (JSON string): Contains salary, start_date, company_name, etc.
    
    Output: JSON with document_id, content, and success status
    
    Uses Gemini 2.0 Flash for professional document generation.
    """
    args_schema: Type[BaseModel] = DocumentGeneratorInput
    client: Any = Field(default=None, exclude=True)
    model_name: str = Field(default="", exclude=True)
    is_gemini: bool = Field(default=False, exclude=True)
    
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Try Gemini first
        try:
            from google import genai
            
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                raise Exception("GEMINI_API_KEY not found")
            
            self.client = genai.Client(api_key=api_key)
            
            # Use Gemini 2.0 Flash for documents
            self.model_name = os.getenv("DOCUMENT_MODEL", "gemini-2.0-flash-exp")
            self.is_gemini = True
            
            logger.info(f"✅ DocumentGenerator initialized with {self.model_name} (Gemini)")
                
        except Exception as e:
            logger.warning(f"⚠️  Gemini unavailable: {e}, using GPT-4o-mini fallback")
            
            # Fallback to OpenAI
            try:
                from langchain_openai import ChatOpenAI
                
                api_key = os.getenv("OPENAI_API_KEY")
                if not api_key:
                    raise Exception("OPENAI_API_KEY not found")
                
                self.model_name = "gpt-4o-mini"
                self.client = ChatOpenAI(
                    model=self.model_name,
                    temperature=0.3,
                    api_key=api_key
                )
                self.is_gemini = False
                
                logger.info(f"✅ DocumentGenerator initialized with {self.model_name} (OpenAI fallback)")
                
            except Exception as fallback_error:
                logger.error(f"❌ Failed to initialize DocumentGenerator: {fallback_error}")
                self.client = None
    
    def _create_offer_letter_prompt(self, context: dict) -> str:
        """Create prompt for offer letter."""
        return f"""You are a professional HR document writer. Generate a formal job offer letter.

IMPORTANT: Use EXACTLY the information provided below. Do NOT modify, estimate, or generate different values.

Context:
- Company: {context.get('company_name', '[Company Name]')}
- Position: {context.get('job_title', '[Job Title]')}
- Candidate: {context.get('candidate_name', '[Candidate Name]')}
- Salary Range: {context.get('salary', '[Salary]')} (USE THIS EXACT SALARY RANGE - DO NOT CHANGE)
- Start Date: {context.get('start_date', '[Start Date]')}
- Location: {context.get('location', '[Location]')}

Write a professional offer letter that includes:
1. Warm welcoming opening paragraph
2. Position title and department
3. Compensation details using the EXACT salary range provided above
4. Start date and work location
5. Next steps for acceptance
6. Professional closing

CRITICAL: When mentioning salary, use the EXACT salary range provided: {context.get('salary', '[Salary]')}
Do NOT calculate, estimate, or generate a different salary range.

Make it warm, professional, and exciting. Use proper business letter format.

OFFER LETTER:"""
    
    def _create_nda_prompt(self, context: dict) -> str:
        """Create prompt for NDA."""
        return f"""You are a legal document writer. Generate a standard Non-Disclosure Agreement (NDA).

Context:
- Company: {context.get('company_name', '[Company Name]')}
- Employee: {context.get('candidate_name', '[Employee Name]')}
- Effective Date: {context.get('start_date', '[Date]')}

Write a professional NDA that includes these standard sections:
1. Parties and Effective Date
2. Definition of Confidential Information
3. Obligations of the Receiving Party
4. Permitted Disclosures
5. Term and Termination
6. Remedies for Breach
7. Miscellaneous Provisions
8. Signature Lines

Use clear, professional legal language. Make it comprehensive but readable.

NON-DISCLOSURE AGREEMENT:"""
    
    def _run(self, employee_id: int, job_id: int, document_type: str, context_data: str) -> str:
        """Generate onboarding document using Gemini or GPT-4o-mini."""
        
        if not self.client:
            return json.dumps({
                "error": "Document generator not available",
                "success": False
            })
        
        try:
            # Parse context
            try:
                context = json.loads(context_data) if isinstance(context_data, str) else context_data
            except:
                context = {"raw": context_data}
            
            # Generate document based on type
            if document_type == "offer_letter":
                prompt = self._create_offer_letter_prompt(context)
                title = "Offer Letter"
                task_type = OnboardingTaskType.OFFER_LETTER
            elif document_type == "nda":
                prompt = self._create_nda_prompt(context)
                title = "Non-Disclosure Agreement"
                task_type = OnboardingTaskType.NDA
            else:
                return json.dumps({"error": "Invalid document_type. Use 'offer_letter' or 'nda'"})
            
            # Generate content
            logger.info(f"📄 Generating {document_type} with {self.model_name}...")
            
            if self.is_gemini:
                # Gemini generation
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=prompt
                )
                document_content = response.text
            else:
                # OpenAI generation
                response = self.client.invoke(prompt)
                document_content = response.content if hasattr(response, 'content') else str(response)
            
            # Store in database
            db: Session = next(get_db())
            try:
                task = OnboardingTask(
                    employee_id=employee_id,
                    job_id=job_id,
                    task_type=task_type,
                    title=title,
                    description=f"Generated {document_type} using {self.model_name}",
                    status=OnboardingTaskStatus.COMPLETED,
                    document_content=document_content
                )
                
                db.add(task)
                
                # ALSO update the Offer record with document content
                # This fixes the "Pending" status issue in the frontend
                from backend.db.models import Offer, Application
                
                # Find the offer by employee_id and job_id
                application = db.query(Application).filter(
                    Application.employee_id == employee_id,
                    Application.job_id == job_id
                ).first()
                
                if application:
                    offer = db.query(Offer).filter(Offer.application_id == application.id).first()
                    if offer:
                        if document_type == "offer_letter":
                            offer.offer_letter_content = document_content
                            logger.info(f"📄 Updated offer #{offer.id} with offer_letter_content")
                        elif document_type == "nda":
                            offer.nda_content = document_content
                            logger.info(f"📄 Updated offer #{offer.id} with nda_content")
                    else:
                        logger.warning(f"⚠️ No offer found for application {application.id}")
                else:
                    logger.warning(f"⚠️ No application found for employee {employee_id}, job {job_id}")
                
                db.commit()
                db.refresh(task)
                
                result = {
                    "document_id": task.id,
                    "document_type": document_type,
                    "content": document_content,
                    "employee_id": employee_id,
                    "job_id": job_id,
                    "success": True,
                    "method": "gemini" if self.is_gemini else "gpt4o-mini"
                }
                
                logger.info(f"✅ Generated {document_type} for employee {employee_id}")
                return json.dumps(result)
                
            finally:
                db.close()
            
        except Exception as e:
            logger.error(f"❌ Document generation error: {e}")
            return json.dumps({"error": str(e), "success": False})
    
    async def _arun(self, employee_id: int, job_id: int, document_type: str, context_data: str) -> str:
        """Async implementation - run in thread pool."""
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, 
            self._run, 
            employee_id, 
            job_id, 
            document_type, 
            context_data
        )
