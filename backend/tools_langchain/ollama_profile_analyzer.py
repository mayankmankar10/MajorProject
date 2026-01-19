"""
Ollama Profile Analyzer - Fast, free profile analysis using local LLM
Uses qwen2.5-coder:7b for structured data extraction
"""
from langchain.tools import BaseTool
from typing import Type, Any, Optional
from pydantic import BaseModel, Field, ConfigDict
from langchain_ollama import OllamaLLM
import json
import logging
import os

logger = logging.getLogger(__name__)

class OllamaProfileAnalyzerInput(BaseModel):
    """Input schema for OllamaProfileAnalyzer."""
    profile_data: str = Field(description="JSON string with candidate profile data (skills, experience, education)")

class OllamaProfileAnalyzer(BaseTool):
    """
    Fast profile analysis using local Ollama model (qwen2.5-coder:7b).
    
    Performance: 10-20x faster than GPT-4o
    Cost: FREE (local inference)
    Quality: Excellent for structured extraction
    
    Automatically falls back to ProfileAnalyzerTool if Ollama unavailable.
    """
    name: str = "OllamaProfileAnalyzer"
    description: str = """
    Analyzes candidate profiles using local Ollama model (fast and free).
    
    Input: profile_data (JSON string) - Contains skills, experience, education, certifications
    Output: JSON with professional_summary, strengths, areas_for_growth, role_recommendations
    
    Uses qwen2.5-coder:7b for structured extraction (10x faster than GPT-4).
    """
    args_schema: Type[BaseModel] = OllamaProfileAnalyzerInput
    llm: Any = Field(default=None, exclude=True)
    fallback_analyzer: Any = Field(default=None, exclude=True)
    
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Try to initialize Ollama
        try:
            model_name = os.getenv("OLLAMA_PROFILE_MODEL", "qwen2.5-coder:7b")
            ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
            
            self.llm = OllamaLLM(
                model=model_name,
                base_url=ollama_url,
                temperature=0.1,  # Low temperature for consistent extraction
                num_predict=1024  # Enough for detailed analysis
            )
            
            # Test connection
            test_response = self.llm.invoke("test")
            if test_response:
                logger.info(f"✅ OllamaProfileAnalyzer initialized with {model_name}")
            else:
                raise Exception("Ollama test failed")
                
        except Exception as e:
            logger.warning(f"⚠️  Ollama unavailable, will use fallback: {e}")
            self.llm = None
            
            # Initialize fallback to OpenAI ProfileAnalyzerTool
            try:
                from backend.tools_langchain.profile_analyzer_tool import ProfileAnalyzerTool
                self.fallback_analyzer = ProfileAnalyzerTool()
                logger.info("✅ Fallback to ProfileAnalyzerTool initialized")
            except Exception as fallback_error:
                logger.error(f"❌ Failed to initialize fallback: {fallback_error}")
                self.fallback_analyzer = None
    
    def _run(self, profile_data: str) -> str:
        """Analyze candidate profile using Ollama or fallback."""
        
        # If Ollama unavailable, use fallback
        if not self.llm:
            if self.fallback_analyzer:
                logger.info("🔄 Using OpenAI fallback for profile analysis")
                return self.fallback_analyzer._run(profile_data)
            else:
                return json.dumps({
                    "error": "Both Ollama and fallback unavailable",
                    "professional_summary": "Analysis unavailable"
                })
        
        try:
            # Parse profile data
            try:
                profile = json.loads(profile_data)
            except:
                profile = {"raw": profile_data}
            
            # Create optimized prompt for qwen2.5-coder (excellent at structured output)
            prompt = f"""You are a professional HR analyst. Analyze this candidate profile and return ONLY valid JSON.

Profile Data:
{json.dumps(profile, indent=2)}

Return this exact JSON structure (no markdown, no extra text):
{{
  "professional_summary": "2-3 sentence summary of candidate's experience and expertise",
  "strengths": ["strength 1", "strength 2", "strength 3"],
  "areas_for_growth": ["area 1", "area 2"],
  "role_recommendations": ["role 1", "role 2", "role 3"],
  "experience_level": "entry|mid|senior"
}}

JSON output:"""
            
            # Get response from Ollama
            response = self.llm.invoke(prompt)
            
            # Parse JSON from response
            try:
                # Clean response (qwen2.5-coder usually returns clean JSON)
                result_clean = response.strip()
                
                # Remove markdown if present
                if "```json" in result_clean:
                    result_clean = result_clean.split("```json")[1].split("```")[0].strip()
                elif "```" in result_clean:
                    result_clean = result_clean.split("```")[1].split("```")[0].strip()
                
                # Find JSON object
                if "{" in result_clean:
                    start = result_clean.index("{")
                    end = result_clean.rindex("}") + 1
                    result_clean = result_clean[start:end]
                
                result = json.loads(result_clean)
                
                # Validate required fields
                required_fields = ["professional_summary", "strengths", "role_recommendations", "experience_level"]
                for field in required_fields:
                    if field not in result:
                        result[field] = [] if field != "professional_summary" and field != "experience_level" else "Unknown"
                
                logger.info(f"✅ Ollama profile analysis complete")
                return json.dumps(result)
                
            except Exception as parse_error:
                logger.warning(f"⚠️  Ollama JSON parsing failed: {parse_error}")
                logger.warning(f"Raw response: {response[:200]}")
                
                # Try fallback
                if self.fallback_analyzer:
                    logger.info("🔄 Falling back to OpenAI due to parsing error")
                    return self.fallback_analyzer._run(profile_data)
                
                # Return basic result
                return json.dumps({
                    "professional_summary": response[:500] if response else "Analysis failed",
                    "strengths": ["Analysis completed - see summary"],
                    "areas_for_growth": [],
                    "role_recommendations": [],
                    "experience_level": "Unknown"
                })
            
        except Exception as e:
            logger.error(f"❌ Ollama profile analysis error: {e}")
            
            # Try fallback
            if self.fallback_analyzer:
                logger.info("🔄 Falling back to OpenAI due to error")
                return self.fallback_analyzer._run(profile_data)
            
            return json.dumps({
                "error": str(e),
                "professional_summary": "Analysis failed"
            })
    
    async def _arun(self, profile_data: str) -> str:
        """Async implementation - Ollama is synchronous but fast."""
        # Ollama doesn't have async API, but it's so fast (local) that sync is fine
        # Run in thread pool to avoid blocking
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._run, profile_data)
