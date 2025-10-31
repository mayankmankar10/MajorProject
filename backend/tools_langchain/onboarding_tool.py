# backend/tools_langchain/onboarding_tool.py
from langchain.tools import BaseTool
from langchain_openai import ChatOpenAI
from typing import Type
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from backend.db.sql_db import get_db
from backend.db.models import OnboardingTask, OnboardingTaskType, OnboardingTaskStatus
import os
import json
import logging

logger = logging.getLogger(__name__)

class OnboardingToolInput(BaseModel):
    """Input schema for OnboardingTool."""
    employee_id: int = Field(description="Employee ID for onboarding")
    job_id: int = Field(description="Job ID they were hired for")
    document_type: str = Field(description="Type: 'offer_letter' or 'nda'")
    context_data: str = Field(description="JSON string with context (salary, start_date, company_name, etc.)")

class OnboardingTool(BaseTool):
    """
    Generates onboarding documents (offer letters, NDAs) using GPT-4.
    """
    name: str = "OnboardingTool"
    description: str = """
    Generates professional onboarding documents using AI.
    
    Input:
    - employee_id (int): Employee ID
    - job_id (int): Job ID
    - document_type (string): Either 'offer_letter' or 'nda'
    - context_data (JSON string): Contains salary, start_date, company_name, etc.
    
    Output: JSON with document_id, content, and success status
    
    Use this to generate offer letters and NDAs for newly hired employees.
    """
    args_schema: Type[BaseModel] = OnboardingToolInput
    
    def __init__(self):
        super().__init__()
        self.llm = ChatOpenAI(
            model=os.getenv("OPENAI_MODEL_REASONING", "gpt-4o"),
            temperature=0.3,
            api_key=os.getenv("OPENAI_API_KEY")
        )
    
    def _run(self, employee_id: int, job_id: int, document_type: str, context_data: str) -> str:
        """Generate onboarding document."""
        try:
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
    
    async def _arun(self, employee_id: int, job_id: int, document_type: str, context_data: str) -> str:
        """Async implementation."""
        return self._run(employee_id, job_id, document_type, context_data)
