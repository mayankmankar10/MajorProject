# backend/agents/tools/interview_scheduler_tool.py
import random
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class InterviewSchedulerTool:
    """
    The InterviewSchedulerTool automates interview scheduling between 
    matched candidates and employers.
    """

    def __init__(self):
        logger.info("📅 InterviewSchedulerTool initialized successfully.")

    def schedule_interview(self, match):
        """
        Mock scheduling logic: randomly assigns a date/time within the next 3 days.
        """
        job = match["job"]
        candidate = match["candidate"]

        scheduled_time = datetime.now() + timedelta(days=random.randint(1, 3), hours=random.randint(9, 17))
        interview = {
            "job_title": job["title"],
            "company": job["company"],
            "candidate_name": candidate["name"],
            "scheduled_time": scheduled_time.strftime("%Y-%m-%d %H:%M:%S"),
            "location": job["location"],
            "match_score": match["score"],
        }

        logger.info(f"📅 Interview Scheduled → {interview}")
        return interview
