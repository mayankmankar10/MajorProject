# backend/agents/tools/resume_parser_tool.py
from typing import Dict, Any
import re

# Use spacy if available for a richer parser
try:
    import spacy
    nlp = spacy.load("en_core_web_sm")
except Exception:
    nlp = None

def parse_resume_text(text: str) -> Dict[str, Any]:
    if not text:
        return {"text": "", "skills": [], "summary": ""}
    if nlp:
        doc = nlp(text)
        # basic skills extraction: proper nouns + noun chunks heuristics
        skills = set()
        for ent in doc.ents:
            if ent.label_ in ("ORG", "PRODUCT", "NORP", "WORK_OF_ART"):
                skills.add(ent.text)
        for chunk in doc.noun_chunks:
            if len(chunk.text) < 40:
                skills.add(chunk.text.strip())
        summary = " ".join([sent.text for sent in list(doc.sents)[:3]])
        return {"text": text, "skills": list(skills)[:30], "summary": summary}
    # fallback: regex-based micro parser
    skills = re.findall(r"(?:Skills:|SKILLS:)(.*)", text)
    skill_list = []
    if skills:
        skill_list = [s.strip() for s in skills[0].split(",")][:30]
    return {"text": text, "skills": skill_list, "summary": text[:500]}
