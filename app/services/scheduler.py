from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.orm import sessionmaker
from app.core.database import engine
from app.services.goal_crud import GoalCRUD
import logging

logger = logging.getLogger(__name__)

class GoalScheduler:
    """Background scheduler for automatic goal assignment"""
    
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    def start(self):
        """Start the scheduler"""
        try:
            self.scheduler.add_job(
                func=self._assign_daily_goals,
                trigger=CronTrigger(hour=0, minute=1),
                id='daily_goals_assignment',
                name='Assign Daily Goals',
                replace_existing=True
            )
            
            self.scheduler.add_job(
                func=self._assign_weekly_goals,
                trigger=CronTrigger(day_of_week='mon', hour=0, minute=1),
                id='weekly_goals_assignment',
                name='Assign Weekly Goals',
                replace_existing=True
            )
            
            self.scheduler.add_job(
                func=self._assign_monthly_goals,
                trigger=CronTrigger(day=1, hour=0, minute=1),
                id='monthly_goals_assignment',
                name='Assign Monthly Goals',
                replace_existing=True
            )
            
            self.scheduler.add_job(
                func=self._cleanup_expired_goals,
                trigger=CronTrigger(hour=23, minute=59),
                id='cleanup_expired_goals',
                name='Clean Expired Goals',
                replace_existing=True
            )
            
            self.scheduler.start()
            logger.info("Goal scheduler started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start goal scheduler: {str(e)}")
    
    def stop(self):
        """Stop the scheduler"""
        try:
            self.scheduler.shutdown()
            logger.info("Goal scheduler stopped")
        except Exception as e:
            logger.error(f"Error stopping scheduler: {str(e)}")
    
    def _assign_daily_goals(self):
        """Background task to assign daily goals"""
        db = self.SessionLocal()
        try:
            result = GoalCRUD.assign_daily_goals(db)
            logger.info(f"Daily goals assigned: {result}")
        except Exception as e:
            logger.error(f"Error in daily goals assignment: {str(e)}")
        finally:
            db.close()
    
    def _assign_weekly_goals(self):
        """Background task to assign weekly goals"""
        db = self.SessionLocal()
        try:
            result = GoalCRUD.assign_weekly_goals(db)
            logger.info(f"Weekly goals assigned: {result}")
        except Exception as e:
            logger.error(f"Error in weekly goals assignment: {str(e)}")
        finally:
            db.close()
    
    def _assign_monthly_goals(self):
        """Background task to assign monthly goals"""
        db = self.SessionLocal()
        try:
            result = GoalCRUD.assign_monthly_goals(db)
            logger.info(f"Monthly goals assigned: {result}")
        except Exception as e:
            logger.error(f"Error in monthly goals assignment: {str(e)}")
        finally:
            db.close()
    
    def _cleanup_expired_goals(self):
        """Background task to clean up expired goals"""
        db = self.SessionLocal()
        try:
            cleaned_count = GoalCRUD.cleanup_expired_goals(db)
            logger.info(f"Cleaned up {cleaned_count} expired goals")
        except Exception as e:
            logger.error(f"Error in cleanup expired goals: {str(e)}")
        finally:
            db.close()
    
    def assign_goals_for_new_user(self, user_id: int):
        """Assign initial goals for a new user"""
        db = self.SessionLocal()
        try:
            result = GoalCRUD.assign_goals_for_new_user(db, user_id)
            logger.info(f"Goals assigned for new user {user_id}: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error assigning goals for new user {user_id}: {str(e)}")
            return None
        finally:
            db.close()

goal_scheduler = GoalScheduler()