# backend/agents/scheduler_agent.py

import schedule
import time
import threading
from datetime import datetime
from backend.agents.employer_agent import EmployerConnectorAgent
from backend.agents.employee_agent import EmployeeConnectorAgent
from backend.db.sql_db import SessionLocal
from backend.db.models import Job, Application
from datetime import datetime

class SchedulerAgent:
    """
    Scheduler Agent that coordinates periodic tasks like matching employers and employees.
    """

    def __init__(self):
        self.employer_agent = EmployerConnectorAgent()
        self.employee_agent = EmployeeConnectorAgent()

    def daily_match(self):
        print(f"[{datetime.now()}] 🔁 Running Daily Matching Task...")
        try:
            # simple matching: for each active job, find top candidates and create applications
            jobs = self.employer_agent.get_active_job_posts()
            candidates = self.employee_agent.get_available_candidates()
            matches = self.employee_agent.match_candidates_with_jobs(jobs, candidates)

            # persist applications for matches
            db = SessionLocal()
            created = 0
            try:
                for m in matches:
                    # m['job'] may be dict with id or a text; try to resolve job id
                    job_id = None
                    if isinstance(m.get("job"), dict) and m["job"].get("id"):
                        job_id = m["job"]["id"]
                    elif isinstance(m.get("job"), int):
                        job_id = m["job"]
                    else:
                        # skip if we cannot map job id
                        continue

                    candidate = m.get("candidate")
                    emp_id = candidate.get("id") if isinstance(candidate, dict) else None
                    if job_id and emp_id:
                        app = Application(job_id=job_id, employee_id=emp_id)
                        db.add(app)
                        created += 1
                db.commit()
            finally:
                db.close()

            print(f"✅ Matching complete. Applications created: {created}")
        except Exception as e:
            print(f"❌ Error during matching: {e}")

    def initialize_daily_schedule(self):
        """Schedules daily job-matching at a fixed interval."""
        schedule.every(24).hours.do(self.daily_match)

        def run_scheduler():
            while True:
                schedule.run_pending()
                time.sleep(1)

        t = threading.Thread(target=run_scheduler, daemon=True)
        t.start()
        print("🕒 Scheduler Agent started — Daily matching job initialized.")
