# backend/tools_langchain/resume_parser_tool.py
from langchain.tools import BaseTool
from typing import Optional, Type
from pydantic import BaseModel, Field
import spacy
import re
import logging

logger = logging.getLogger(__name__)

# Load Spacy model
try:
    nlp = spacy.load("en_core_web_sm")
except Exception as e:
    logger.warning(f"Spacy model not loaded: {e}")
    nlp = None

class ResumeParserInput(BaseModel):
    """Input schema for ResumeParserTool."""
    resume_text: str = Field(description="The full text content of the resume to parse")

class ResumeParserTool(BaseTool):
    """
    Tool for parsing resume text and extracting structured information.
    Extracts skills, education, experience, and generates a summary using Spacy NLP.
    """
    name: str = "ResumeParserTool"
    description: str = """
    Parses resume text and extracts structured information including:
    - Skills (technical and soft skills)
    - Summary (brief overview)
    - Key entities (organizations, products, work)
    
    Input: resume_text (string) - The full text content of the resume
    Output: JSON with text, skills list, and summary
    
    Use this tool when you need to analyze a candidate's resume or extract information from resume text.
    """
    args_schema: Type[BaseModel] = ResumeParserInput
    
    def _run(self, resume_text: str) -> str:
        """Synchronous implementation of resume parsing."""
        try:
            if not resume_text:
                return str({"text": "", "skills": [], "summary": "", "entities": []})
            
            if nlp:
                doc = nlp(resume_text)
                
                # Extract skills from entities and noun chunks
                skills = set()
                entities = []
                
                for ent in doc.ents:
                    if ent.label_ in ("ORG", "PRODUCT", "NORP", "WORK_OF_ART", "GPE", "SKILL"):
                        skills.add(ent.text)
                        entities.append({"text": ent.text, "label": ent.label_})
                
                # Extract noun chunks as potential skills
                for chunk in doc.noun_chunks:
                    if 2 < len(chunk.text) < 40:
                        skills.add(chunk.text.strip())
                
                # Generate summary from first 3 sentences
                sentences = [sent.text.strip() for sent in doc.sents]
                summary = " ".join(sentences[:3])
                
                result = {
                    "text": resume_text,
                    "skills": sorted(list(skills)[:30]),
                    "summary": summary[:500],
                    "entities": entities[:20],
                    "sentence_count": len(sentences),
                    "word_count": len([token for token in doc if not token.is_punct])
                }
                
                logger.info(f"✅ Parsed resume: {len(result['skills'])} skills extracted")
                return str(result)
            
            else:
                # Fallback: regex-based parsing
                skills = re.findall(r"(?:Skills?:|SKILLS?:)(.*?)(?:\n\n|\Z)", resume_text, re.IGNORECASE | re.DOTALL)
                skill_list = []
                if skills:
                    skill_list = [s.strip() for s in skills[0].split(",")][:30]
                
                result = {
                    "text": resume_text,
                    "skills": skill_list,
                    "summary": resume_text[:500],
                    "entities": [],
                    "word_count": len(resume_text.split())
                }
                
                logger.info(f"✅ Parsed resume (fallback): {len(skill_list)} skills extracted")
                return str(result)
                
        except Exception as e:
            logger.error(f"❌ Resume parsing error: {str(e)}")
            return str({"error": str(e), "text": "", "skills": [], "summary": ""})
    
    async def _arun(self, resume_text: str) -> str:
        """Async implementation (calls sync version)."""
        return self._run(resume_text)
