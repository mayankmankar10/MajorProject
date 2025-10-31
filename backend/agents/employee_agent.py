# backend/agents/employee_agent.py
import logging
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)

class EmployeeConnectorAgent:
    """
    The EmployeeConnectorAgent manages worker/candidate data and 
    handles skill-based matching with job postings.
    """

    def __init__(self):
        logger.info("👷 EmployeeConnectorAgent initialized successfully.")

    def get_available_candidates(self):
        """
        Retrieve a list of available candidates (mock data for demonstration).
        """
        candidates = [
            {
                "id": 1,
                "name": "Ravi Kumar",
                "skills": ["communication", "teamwork", "english"],
                "preferred_location": "Mumbai",
            },
            {
                "id": 2,
                "name": "Pooja Singh",
                "skills": ["cooking", "cleaning", "hospitality"],
                "preferred_location": "Pune",
            },
            {
                "id": 3,
                "name": "Aman Verma",
                "skills": ["service", "customer service", "teamwork"],
                "preferred_location": "Delhi",
            },
        ]

        logger.info(f"🧑‍💼 Found {len(candidates)} available candidates.")
        return candidates

    def match_candidates_with_jobs(self, jobs, candidates):
        """
        Perform skill-based matching between job postings and candidates.
        Uses a basic text similarity heuristic for demonstration.
        """
        matches = []
        for job in jobs:
            for candidate in candidates:
                score = self._calculate_match_score(job["skills"], candidate["skills"])
                if score > 0.45:  # threshold for a reasonable match
                    matches.append({
                        "job": job,
                        "candidate": candidate,
                        "score": round(score, 2)
                    })

        logger.info(f"🤝 Matched {len(matches)} candidate-job pairs.")
        return matches

    def _calculate_match_score(self, job_skills, candidate_skills):
        """
        Calculates a basic skill similarity score.
        """
        total_score = 0
        for js in job_skills:
            for cs in candidate_skills:
                total_score += SequenceMatcher(None, js, cs).ratio()
        return total_score / (len(job_skills) * len(candidate_skills))
