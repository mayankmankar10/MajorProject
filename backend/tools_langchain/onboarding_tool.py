# backend/tools_langchain/onboarding_tool.py
from langchain.tools import BaseTool
from langchain_openai import ChatOpenAI
from typing import Type, Any
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy.orm import Session
from backend.db.sql_db import get_db
from backend.db.models import OnboardingTask, OnboardingTaskType, OnboardingTaskStatus
import os
import json
import logging

logger = logging.getLogger(__name__)

class OnboardingToolInput(BaseModel):
    """Input schema for OnboardingTool."""
    application_id: int = Field(default=0, description="Application ID (alternative to employee_id + job_id)")
    employee_id: int = Field(default=0, description="Employee ID for onboarding")
    job_id: int = Field(default=0, description="Job ID they were hired for")
    document_type: str = Field(description="Type: 'offer_letter' or 'nda'")
    context_data: str = Field(description="JSON string with context (salary, start_date, company_name, etc.)")

class OnboardingTool(BaseTool):
    """
    Generates onboarding documents (offer letters, NDAs) using GPT-4.
    """
    name: str = "OnboardingTool"
    description: str = """
    Generates professional onboarding documents using AI.
    
    Input (choose ONE of these options):
    OPTION 1 (Recommended): Use application_id
    - application_id (int): Application ID (will auto-resolve employee_id and job_id)
    - document_type (string): Either 'offer_letter' or 'nda'
    - context_data (JSON string): Context data (see below)
    
    OPTION 2: Use employee_id + job_id
    - employee_id (int): Employee ID
    - job_id (int): Job ID
    - document_type (string): Either 'offer_letter' or 'nda'
    - context_data (JSON string): Context data (see below)
    
    Context data JSON fields:
    - company_name: Company name
    - job_title: Position title
    - candidate_name: Employee full name
    - salary: Formatted salary string
    - start_date: MUST be 2-4 weeks from TODAY (January 2026, NOT 2023!)
    - location: Work location
    
    CRITICAL DATE RULE:
    - NEVER use dates from 2023 or earlier - those are over 2 years old!
    - Always calculate start_date as TODAY + 2 to 4 weeks
    - Today is January 13, 2026
    - Example: "January 27, 2026" or "February 3, 2026"
    - Format: "Month Day, Year"
    
    Output: JSON with document_id, content, and success status
    
    Use this to generate offer letters and NDAs for newly hired employees.
    """
    args_schema: Type[BaseModel] = OnboardingToolInput

    llm: Any = Field(default=None, exclude=True)

    

    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.llm = ChatOpenAI(
            model=os.getenv("OPENAI_MODEL_REASONING", "gpt-4o"),
            temperature=0.3,
            api_key=os.getenv("OPENAI_API_KEY")
        )
    
    def _run(self, application_id: int = 0, employee_id: int = 0, job_id: int = 0, document_type: str = "", context_data: str = "") -> str:
        """Generate onboarding document."""
        try:
            # OPTION 1: Resolve application_id to employee_id and job_id
            if application_id:
                from backend.db.models import Application
                db: Session = next(get_db())
                app = db.query(Application).filter(Application.id == application_id).first()
                if not app:
                    return json.dumps({"error": f"Application {application_id} not found", "success": False})
                employee_id = app.employee_id
                job_id = app.job_id
                logger.info(f"📋 Resolved application #{application_id} → employee {employee_id}, job {job_id}")
            
            # OPTION 2: Validate that employee_id and job_id are provided
            elif not (employee_id and job_id):
                return json.dumps({
                    "error": "Either application_id OR (employee_id + job_id) required",
                    "success": False
                })
            
            # Parse context
            try:
                context = json.loads(context_data)
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
            response = self.llm.invoke(prompt)
            document_content = response.content
            
            # Store in database
            db: Session = next(get_db())
            task = OnboardingTask(
                employee_id=employee_id,
                job_id=job_id,
                task_type=task_type,
                title=title,
                description=f"Generated {document_type}",
                status=OnboardingTaskStatus.COMPLETED,
                document_content=document_content
            )
            
            db.add(task)
            db.commit()
            db.refresh(task)
            
            result = {
                "document_id": task.id,
                "document_type": document_type,
                "content": document_content,
                "employee_id": employee_id,
                "job_id": job_id,
                "success": True
            }
            
            
            logger.info(f"✅ Generated {document_type} for employee {employee_id}")
            
            # AUTOMATICALLY SYNC TO OFFER TABLE
            # This ensures the document appears in the UI
            try:
                from backend.db.models import Application, Offer
                
                # Find application (most recent for this employee/job)
                application = db.query(Application).filter(
                    Application.employee_id == employee_id,
                    Application.job_id == job_id
                ).order_by(Application.applied_at.desc()).first()
                
                if application:
                    offer = db.query(Offer).filter(Offer.application_id == application.id).first()
                    if offer:
                        if document_type == "offer_letter":
                            offer.offer_letter_content = document_content
                        elif document_type == "nda":
                            offer.nda_content = document_content
                        db.commit()
                        logger.info(f"✅ Synced {document_type} to Offer #{offer.id}")
                    else:
                        logger.warning(f"⚠️ Offer record not found for Application #{application.id}")
                else:
                    logger.warning(f"⚠️ Application not found for Employee {employee_id} / Job {job_id}")
                    
            except Exception as e:
                logger.error(f"❌ Failed to sync document to Offer table: {e}")
            
            return json.dumps(result)
            
        except Exception as e:
            logger.error(f"❌ Onboarding document generation error: {str(e)}")
            return json.dumps({"error": str(e), "success": False})
    
    def _create_offer_letter_prompt(self, context: dict) -> str:
        """Create prompt for offer letter."""
        return f"""Generate a professional job offer letter with the following details:

Company: {context.get('company_name', '[Company Name]')}
Position: {context.get('job_title', '[Job Title]')}
Candidate: {context.get('candidate_name', '[Candidate Name]')}
Salary: {context.get('salary', '[Salary]')}
Start Date: {context.get('start_date', '[Start Date]')}
Location: {context.get('location', '[Location]')}

Include:
1. Welcoming opening
2. Position details and responsibilities
3. Compensation and benefits
4. Start date and location
5. Next steps
6. Professional closing

Make it warm, professional, and exciting."""
    
    def _create_nda_prompt(self, context: dict) -> str:
        """Create prompt for NDA."""
        return f"""Generate a standard Non-Disclosure Agreement (NDA) for:

Company: {context.get('company_name', '[Company Name]')}
Employee: {context.get('candidate_name', '[Employee Name]')}
Effective Date: {context.get('start_date', '[Date]')}

Include standard NDA clauses:
1. Definition of confidential information
2. Obligations of the receiving party
3. Permitted disclosures
4. Term and termination
5. Remedies
6. Miscellaneous provisions

Use clear, professional legal language."""
    
    async def _arun(self, application_id: int = 0, employee_id: int = 0, job_id: int = 0, document_type: str = "", context_data: str = "") -> str:
        """Async implementation with parallel execution support."""
        try:
            # OPTION 1: Resolve application_id to employee_id and job_id
            if application_id:
                from backend.db.models import Application
                import asyncio
                from functools import partial
                
                def get_application():
                    db: Session = next(get_db())
                    try:
                        return db.query(Application).filter(Application.id == application_id).first()
                    finally:
                        db.close()
                
                loop = asyncio.get_event_loop()
                app = await loop.run_in_executor(None, get_application)
                
                if not app:
                    return json.dumps({"error": f"Application {application_id} not found", "success": False})
                employee_id = app.employee_id
                job_id = app.job_id
                logger.info(f"📋 Resolved application #{application_id} → employee {employee_id}, job {job_id}")
            
            # OPTION 2: Validate that employee_id and job_id are provided
            elif not (employee_id and job_id):
                return json.dumps({
                    "error": "Either application_id OR (employee_id + job_id) required",
                    "success": False
                })
            
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
            
            # Generate content asynchronously
            response = await self.llm.ainvoke(prompt)
            document_content = response.content
            
            # Store in database (run in thread pool to avoid blocking)
            import asyncio
            from functools import partial
            
            def save_to_db():
                db: Session = next(get_db())
                try:
                    task = OnboardingTask(
                        employee_id=employee_id,
                        job_id=job_id,
                        task_type=task_type,
                        title=title,
                        description=f"Generated {document_type}",
                        status=OnboardingTaskStatus.COMPLETED,
                        document_content=document_content
                    )
                    db.add(task)
                    db.commit()
                    db.refresh(task)
                    
                    # AUTOMATICALLY SYNC TO OFFER TABLE
                    try:
                        from backend.db.models import Application, Offer
                        application = db.query(Application).filter(
                            Application.employee_id == employee_id,
                            Application.job_id == job_id
                        ).order_by(Application.applied_at.desc()).first()
                        
                        if application:
                            offer = db.query(Offer).filter(Offer.application_id == application.id).first()
                            if offer:
                                if document_type == "offer_letter":
                                    offer.offer_letter_content = document_content
                                elif document_type == "nda":
                                    offer.nda_content = document_content
                                db.commit()
                                logger.info(f"✅ Synced {document_type} to Offer #{offer.id}")
                    except Exception as e:
                        logger.error(f"❌ Failed to sync document to Offer table (async): {e}")

                    return task.id
                finally:
                    db.close()
            
            loop = asyncio.get_event_loop()
            task_id = await loop.run_in_executor(None, save_to_db)
            
            result = {
                "document_id": task_id,
                "document_type": document_type,
                "content": document_content,
                "employee_id": employee_id,
                "job_id": job_id,
                "success": True
            }
            
            logger.info(f"✅ Generated {document_type} for employee {employee_id}")
            return json.dumps(result)
            
        except Exception as e:
            logger.error(f"❌ Onboarding document generation error: {str(e)}")
            return json.dumps({"error": str(e), "success": False})
