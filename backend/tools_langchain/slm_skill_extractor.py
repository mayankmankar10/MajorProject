"""
SLM-powered skill extraction tool.
Uses local SLM for fast skill extraction from resumes.
"""
from langchain.tools import BaseTool
from typing import Type, Any
from pydantic import BaseModel, Field, ConfigDict
from backend.llm.slm_client import get_slm_client
import json
import logging

logger = logging.getLogger(__name__)

class SLMSkillExtractorInput(BaseModel):
    """Input schema for SLMSkillExtractor."""
    resume_text: str = Field(description="Resume text to extract skills from")

class SLMSkillExtractor(BaseTool):
    """
    Extract skills from resume using local SLM (fast, free).
    
    Uses phi3:mini for instant skill extraction without API costs.
    Falls back gracefully if SLM unavailable.
    """
    name: str = "SLMSkillExtractor"
    description: str = """
    Extract skills from resume text using local SLM (very fast, no API cost).
    
    Input:
    - resume_text (string): Resume or profile text
    
    Output: JSON with extracted skills
    
    Use this for quick skill extraction from candidate profiles.
    """
    args_schema: Type[BaseModel] = SLMSkillExtractorInput
    
    # Declare SLM client as excluded field
    slm: Any = Field(default=None, exclude=True)
    
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.slm = get_slm_client()
    
    def _run(self, resume_text: str) -> str:
        """Extract skills using SLM."""
        
        # Check if SLM available
        if not self.slm.is_available():
            logger.warning("⚠️  SLM unavailable for skill extraction")
            return json.dumps({
                "error": "SLM unavailable",
                "skills": [],
                "success": False,
                "fallback_needed": True
            })
        
        try:
            # Create extraction prompt
            prompt = f"""Extract technical skills, soft skills, and certifications from this resume.
Return ONLY a JSON object, no other text.

Resume:
{resume_text[:1000]}

Output format:
{{
  "technical_skills": ["skill1", "skill2", ...],
  "soft_skills": ["skill1", "skill2", ...],
  "certifications": ["cert1", "cert2", ...],
  "years_experience": <number or null>
}}"""
            
            # Invoke SLM
            logger.info("🤖 Using SLM for skill extraction...")
            result = self.slm.invoke(prompt, max_tokens=512)
            
            if not result:
                raise Exception("SLM returned empty response")
            
            # Try to parse JSON
            try:
                # Extract JSON from response (handle markdown code blocks)
                result_clean = result.strip()
                if "```json" in result_clean:
                    result_clean = result_clean.split("```json")[1].split("```")[0]
                elif "```" in result_clean:
                    result_clean = result_clean.split("```")[1].split("```")[0]
                
                parsed = json.loads(result_clean)
                parsed["success"] = True
                parsed["source"] = "slm"
                
                logger.info(f"✅ SLM extracted {len(parsed.get('technical_skills', []))} technical skills")
                return json.dumps(parsed)
                
            except json.JSONDecodeError:
                # Return raw result if not valid JSON
                logger.warning("⚠️  SLM response not valid JSON, returning raw")
                return json.dumps({
                    "raw_response": result,
                    "success": False,
                    "error": "Invalid JSON from SLM"
                })
                
        except Exception as e:
            logger.error(f"❌ SLM skill extraction error: {e}")
            return json.dumps({
                "error": str(e),
                "skills": [],
                "success": False
            })
    
    async def _arun(self, resume_text: str) -> str:
        """Async implementation."""
        return self._run(resume_text)
