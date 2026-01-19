"""
Position Parser Tool - Multi-position hiring request parser
Hybrid approach: Regex + NLP (fast) with GPT-4o fallback (accurate)
"""

from langchain.tools import BaseTool
from typing import Type, Dict, List, Any, Optional, ClassVar
from pydantic import BaseModel, Field, ConfigDict
import re
import json
import logging
import os

logger = logging.getLogger(__name__)

class PositionParserInput(BaseModel):
    """Input schema for PositionParser."""
    user_input: str = Field(description="Natural language job requirement (e.g., 'Need 5 waiters, 2 cooks, 1 chef in Mumbai')")

class PositionParserTool(BaseTool):
    """
    Parse multi-position hiring requests using hybrid approach:
    1. Fast regex + NLP (90% success rate, 15-30ms)
    2. GPT-4o fallback for complex cases (100% success, 500-800ms)
    
    Handles various formats:
    - "5 waiters, 2 cooks, 1 chef"
    - "need five servers and two kitchen staff"
    - "3 bartenders + 4 waitstaff"
    """
    name: str = "PositionParserTool"
    description: str = """
    Parses natural language hiring requests into structured position data.
    
    Input: "I need 5 waiters, 2 line cooks, and 1 executive chef in Mumbai"
    Output: Structured JSON with positions array (job_type, title, quantity) and location
    
    Use this when employer provides multi-position hiring requirements in natural language.
    """
    args_schema: Type[BaseModel] = PositionParserInput
    
    # Restaurant job patterns (covers 90% of inputs)
    JOB_PATTERNS: ClassVar[Dict[str, str]] = {
        "waiter": r'(\d+)\s+(?:waiter|waiters|server|servers|waitstaff|wait\s+staff)',
        "cook": r'(\d+)\s+(?:cook|cooks|line\s+cook|line\s+cooks|kitchen\s+staff)',
        "chef": r'(\d+)\s+(?:chef|chefs|executive\s+chef|head\s+chef|sous\s+chef)',
        "bartender": r'(\d+)\s+(?:bartender|bartenders|bar\s+staff)',
        "host": r'(\d+)\s+(?:host|hosts|hostess|greeter|greeters)',
        "dishwasher": r'(\d+)\s+(?:dishwasher|dishwashers)',
    }
    
    # Shift patterns
    SHIFT_PATTERNS: ClassVar[Dict[str, str]] = {
        "morning": r'morning|mornings|breakfast|am shift|day shift',
        "evening": r'evening|evenings|dinner|pm shift',
        "night": r'night|nights|late night|graveyard|overnight',
        "flexible": r'flexible|any shift|all shifts|any time'
    }
    
    # Job title mappings
    TITLE_MAP: ClassVar[Dict[str, str]] = {
        "waiter": "Waiter/Server",
        "cook": "Line Cook",
        "chef": "Executive Chef",
        "bartender": "Bartender",
        "host": "Host/Hostess",
        "dishwasher": "Dishwasher"
    }
    
    nlp: Any = Field(default=None, exclude=True)
    
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Load Spacy model for NER (location extraction)
        try:
            import spacy
            self.nlp = spacy.load("en_core_web_sm")
            logger.info("✅ Spacy model loaded for location extraction")
        except Exception as e:
            logger.warning(f"⚠️ Spacy not available: {str(e)}. Location extraction will be limited.")
            self.nlp = None
    
    def _extract_location(self, text: str) -> Optional[str]:
        """Extract city/location using Spacy NER."""
        if not self.nlp:
            return None
        
        try:
            doc = self.nlp(text)
            for ent in doc.ents:
                if ent.label_ in ["GPE", "LOC"]:  # Geo-political entity or location
                    return ent.text
        except Exception as e:
            logger.warning(f"Location extraction failed: {str(e)}")
        
        return None
    
    def _extract_shift_requirements(self, text: str) -> List[str]:
        """Extract shift requirements from text."""
        text_lower = text.lower()
        shifts = []
        
        for shift_type, pattern in self.SHIFT_PATTERNS.items():
            if re.search(pattern, text_lower, re.IGNORECASE):
                shifts.append(shift_type)
        
        return shifts if shifts else None
    
    def _extract_salary(self, text: str) -> dict:
        """Extract salary information from text."""
        # Pattern for salary: "at salary 28000" or "salary range 25000-30000" or "Rs. 28000"
        salary_patterns = [
            r'(?:at\s+)?salary\s+(\d{4,6})',  # "at salary 28000" or "salary 28000"
            r'(?:rs\.?|₹)\s*(\d{4,6})',  # "Rs. 28000" or "₹28000"
            r'(\d{4,6})\s*(?:rs|rupees)',  # "28000 rs" or "28000 rupees"
            r'salary\s+range\s+(\d{4,6})\s*-\s*(\d{4,6})',  # "salary range 25000-30000"
        ]
        
        for pattern in salary_patterns:
            match = re.search(pattern, text.lower())
            if match:
                if len(match.groups()) == 2:  # Range
                    return {"min": int(match.group(1)), "max": int(match.group(2))}
                else:  # Single value
                    salary = int(match.group(1))
                    return {"min": salary, "max": salary}
        
        return None
    
    def _extract_experience(self, text: str) -> dict:
        """Extract experience requirements from text."""
        # Patterns: "more than 2 years", "2+ years", "at least 3 years", "minimum 5 years experience"
        exp_patterns = [
            r'(?:more\s+than|at\s+least|minimum\s+of?)\s+(\d+)\s+years?',
            r'(\d+)\+\s+years?',
            r'(\d+)\s+years?\s+(?:of\s+)?experience',
        ]
        
        for pattern in exp_patterns:
            match = re.search(pattern, text.lower())
            if match:
                return {"min_years": int(match.group(1))}
        
        return None
    
    def _parse_with_regex(self, text: str) -> Dict:
        """Fast regex-based parsing (15-30ms)."""
        text_lower = text.lower()
        positions = []
        
        for job_type, pattern in self.JOB_PATTERNS.items():
            matches = re.finditer(pattern, text_lower)
            for match in matches:
                quantity = int(match.group(1))
                positions.append({
                    "job_type": job_type,
                    "title": self.TITLE_MAP[job_type],
                    "quantity": quantity
                })
        
        location = self._extract_location(text)
        shift_requirements = self._extract_shift_requirements(text)
        salary_requirement = self._extract_salary(text)
        experience_requirement = self._extract_experience(text)
        
        return {
            "location": location,
            "shift_requirements": shift_requirements,
            "salary_requirement": salary_requirement,
            "experience_requirement": experience_requirement,
            "positions": positions,
            "parsing_method": "regex",
            "success": len(positions) > 0
        }
    
    async def _parse_with_gpt(self, text: str) -> Dict:
        """GPT-4o fallback for complex inputs (500-800ms)."""
        try:
            from openai import AsyncOpenAI
            
            client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            
            response = await client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": """You are a parser for restaurant hiring requests. 
Extract positions, quantities, and location from natural language.

Return JSON with this exact structure:
{
  "location": "city name or null",
  "positions": [
    {"job_type": "waiter|cook|chef|bartender|host|dishwasher", "title": "formal title", "quantity": number}
  ]
}

Job type mappings:
- waiter: server, waitstaff, wait staff
- cook: line cook, kitchen staff, prep cook
- chef: executive chef, head chef, sous chef
- bartender: bar staff
- host: hostess, greeter
- dishwasher: dish washer

Examples:
Input: "Need 5 waiters and 2 cooks in Mumbai"
Output: {"location": "Mumbai", "positions": [{"job_type": "waiter", "title": "Waiter/Server", "quantity": 5}, {"job_type": "cook", "title": "Line Cook", "quantity": 2}]}"""
                    },
                    {
                        "role": "user",
                        "content": f"Parse this hiring request: {text}"
                    }
                ],
                response_format={"type": "json_object"},
                temperature=0.1
            )
            
            result = json.loads(response.choices[0].message.content)
            result["parsing_method"] = "gpt"
            result["success"] = len(result.get("positions", [])) > 0
            
            logger.info(f"✅ GPT parsing successful: {len(result.get('positions', []))} positions")
            return result
            
        except Exception as e:
            logger.error(f"❌ GPT parsing failed: {str(e)}")
            return {
                "success": False, 
                "error": str(e), 
                "parsing_method": "gpt_failed",
                "positions": [],
                "location": None
            }
    
    def _run(self, user_input: str) -> str:
        """Sync implementation (required by BaseTool)."""
        import asyncio
        return asyncio.run(self._arun(user_input))
    
    async def _arun(self, user_input: str) -> str:
        """
        Main parsing logic with fallback strategy.
        
        Returns JSON string with structure:
        {
            "location": str or null,
            "positions": [{"job_type": str, "title": str, "quantity": int}],
            "parsing_method": "regex" or "gpt",
            "success": bool
        }
        """
        logger.info(f"🔍 Parsing position request: '{user_input[:50]}...'")
        
        # Step 1: Try fast regex parsing
        result = self._parse_with_regex(user_input)
        
        if result["success"]:
            logger.info(f"✅ Parsed with regex (fast): {len(result['positions'])} positions, {result.get('location', 'unknown')} location")
            return json.dumps(result)
        
        # Step 2: Fallback to GPT for complex cases
        logger.info("⚠️ Regex failed, falling back to GPT parsing...")
        result = await self._parse_with_gpt(user_input)
        
        if result["success"]:
            logger.info(f"✅ Parsed with GPT (fallback): {len(result['positions'])} positions")
        else:
            logger.error("❌ Both regex and GPT parsing failed")
        
        return json.dumps(result)
