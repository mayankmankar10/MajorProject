# backend/agents/employer_agent.py
import logging

logger = logging.getLogger(__name__)

class EmployerConnectorAgent:
    """
    The EmployerConnectorAgent handles job postings and related information 
    provided by employers. For demo purposes, we return mock job postings.
    """

    def __init__(self):
        logger.info("🏢 EmployerConnectorAgent initialized successfully.")

    def get_active_job_posts(self):
        """
        Retrieve active job postings (mock data for demonstration).
        In production, this would query a database or vector store.
        """
        jobs = [
            {
                "id": 1,
                "title": "Front Desk Executive",
                "company": "Hotel Sunrise",
                "skills": ["communication", "hospitality", "customer service"],
                "location": "Mumbai",
            },
            {
                "id": 2,
                "title": "Chef Assistant",
                "company": "Royal Tandoor",
                "skills": ["cooking", "teamwork", "cleanliness"],
                "location": "Pune",
            },
            {
                "id": 3,
                "title": "Waiter",
                "company": "Cafe Delight",
                "skills": ["service", "teamwork", "communication"],
                "location": "Delhi",
            },
        ]

        logger.info(f"📋 Found {len(jobs)} active job postings.")
        return jobs
