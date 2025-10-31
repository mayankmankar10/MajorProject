# backend/agents/scheduler_agent.py

import schedule
import time
import threading
from datetime import datetime
from backend.agents.employer_agent import EmployerConnectorAgent
from backend.agents.employee_agent import EmployeeConnectorAgent

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
            result = self.employer_agent.match_candidates()
            print(f"✅ Matching complete: {result}")
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
