# backend/background_jobs.py - Enhanced with notification triggers
"""
Background job scheduler for SmartServe.
Handles automated tasks like daily job recommendations and notifications.
"""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.orm import Session
from backend.db.sql_db import SessionLocal
from backend.db.models import Employee, Notification, Application
from backend.notifications.connection_manager import manager
import json
import logging
from datetime import datetime, timedelta
import asyncio

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()

def send_daily_job_recommendations():
    """Send daily job recommendation notifications to active employees"""
    db: Session = SessionLocal()
    
    try:
        from backend.tools_langchain.job_recommender_tool import JobRecommenderTool
        
        # Get all active employees
        employees = db.query(Employee).filter(Employee.user_id.isnot(None)).limit(50).all()
        
        recommender = JobRecommenderTool()
        notifications_sent = 0
        
        for employee in employees:
            try:
                # Get recommendations
                result_json = recommender._run(employee_id=employee.id, limit=3)
                result = json.loads(result_json)
                
                recommendations = result.get("recommendations", [])
                
                if recommendations and len(recommendations) > 0:
                    # Create notification
                    job_titles = [rec["title"] for rec in recommendations[:2]]
                    message = f"We found {len(recommendations)} new jobs for you: {', '.join(job_titles)}"
                    if len(recommendations) > 2:
                        message += f" and {len(recommendations) - 2} more!"
                    
                    notification = Notification(
                        recipient_id=employee.user_id,
                        title="🎯 New Job Matches!",
                        message=message,
                        notification_type="job_match",
                        action_url="/employee/jobs",
                        metadata={"recommendation_count": len(recommendations)}
                    )
                    
                    db.add(notification)
                    db.commit()
                    notifications_sent += 1
                    
                    # Try WebSocket delivery (best effort)
                    try:
                        loop = asyncio.new_event_loop()
                        notification_data = {
                            "id": notification.id,
                            "title": notification.title,
                            "message": notification.message,
                            "type": "job_match",
                            "action_url": notification.action_url
                        }
                        loop.run_until_complete(manager.send_personal_message(
                            json.dumps(notification_data),
                            employee.user_id
                        ))
                    except:
                        pass  # WebSocket failure is non-critical
                        
            except Exception as e:
                logger.warning(f"Failed to send recommendations for employee {employee.id}: {e}")
                continue
        
        logger.info(f"✅ Daily job recommendations: Sent {notifications_sent} notifications")
        
    except Exception as e:
        logger.error(f"❌ Daily recommendations job failed: {str(e)}")
    finally:
        db.close()

def send_application_status_updates():
    """Check and notify for application status changes"""
    db: Session = SessionLocal()
    
    try:
        # Get applications updated in last hour
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)
        
        recent_updates = db.query(Application).filter(
            Application.updated_at >= one_hour_ago,
            Application.updated_at != Application.applied_at  # Status changed
        ).all()
        
        notifications_sent = 0
        
        for application in recent_updates:
            try:
                from backend.db.models import Job, Employer
                
                job = db.query(Job).filter(Job.id == application.job_id).first()
                employer = db.query(Employer).filter(Employer.id == job.employer_id).first() if job else None
                employee = db.query(Employee).filter(Employee.id == application.employee_id).first()
                
                if not (job and employee):
                    continue
                
                # Create status update notification
                status_messages = {
                    "reviewing": f"Your application for {job.title} is being reviewed!",
                    "interview_scheduled": f"🎉 Interview scheduled for {job.title} at {employer.company_name if employer else 'the company'}!",
                    "selected": f"🌟 Congratulations! You've been selected for {job.title}!",
                    "hired": f"🎊 You're hired! Welcome to {employer.company_name if employer else 'the team'}!",
                    "rejected": f"Your application for {job.title} was not selected this time. Keep applying!"
                }
                
                message = status_messages.get(application.status.value, f"Status update: {application.status.value}")
                
                notification = Notification(
                    recipient_id=employee.user_id,
                    title="Application Status Update",
                    message=message,
                    notification_type="application_status",
                    action_url=f"/employee/applications/{application.id}"
                )
                
                db.add(notification)
                db.commit()
                notifications_sent += 1
                
                # Try WebSocket delivery
                try:
                    loop = asyncio.new_event_loop()
                    notification_data = {
                        "id": notification.id,
                        "title": notification.title,
                        "message": notification.message,
                        "type": "application_status",
                        "action_url": notification.action_url
                    }
                    loop.run_until_complete(manager.send_personal_message(
                        json.dumps(notification_data),
                        employee.user_id
                    ))
                except:
                    pass
                    
            except Exception as e:
                logger.warning(f"Failed to send status update for application {application.id}: {e}")
                continue
        
        if notifications_sent > 0:
            logger.info(f"✅ Application status updates: Sent {notifications_sent} notifications")
        
    except Exception as e:
        logger.error(f"❌ Status update job failed: {str(e)}")
    finally:
        db.close()

def start_notification_scheduler():
    """Start the background scheduler for notifications"""
    
    # Daily job recommendations at 9 AM
    scheduler.add_job(
        send_daily_job_recommendations,
        CronTrigger(hour=9, minute=0),
        id='daily_job_recommendations',
        name='Send daily job recommendations',
        replace_existing=True
    )
    
    # Application status updates every hour
    scheduler.add_job(
        send_application_status_updates,
        IntervalTrigger(hours=1),
        id='application_status_updates',
        name='Send application status updates',
        replace_existing=True
    )
    
    scheduler.start()
    logger.info("✅ Notification scheduler started")

if __name__ == "__main__":
    # For testing
    logging.basicConfig(level=logging.INFO)
    start_notification_scheduler()
    
    # Keep the script running
    try:
        while True:
            import time
            time.sleep(60)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
