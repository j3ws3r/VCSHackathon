from sqlalchemy.orm import Session
from sqlalchemy import and_, func, case
from app.models.achievements import Achievement, user_achievements
from app.models.users import User
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import random
import logging

logger = logging.getLogger(__name__)

class GoalCRUD:
    
    @staticmethod
    def _assign_goals_by_frequency(db: Session, frequency: str, target_count: int, user_id: Optional[int] = None) -> Dict:
        try:
            if user_id:
                users = db.query(User).filter(and_(User.id == user_id, User.is_active == True)).all()
            else:
                users = db.query(User).filter(User.is_active == True).all()
            
            if not users:
                return {"assigned": 0, "errors": ["No active users found to assign goals to."]}
                
            available_achievements = db.query(Achievement).filter(Achievement.frequency == frequency).all()

            if not available_achievements:
                msg = f"No '{frequency}' achievements exist in the database. Cannot assign any."
                logger.warning(msg)
                return {"assigned": 0, "errors": [msg]}

            results = {"assigned_to_users": 0, "total_goals_assigned": 0, "errors": []}
            
            for user in users:
                try:
                    db.query(user_achievements).filter(
                        and_(
                            user_achievements.c.user_id == user.id,
                            user_achievements.c.status == 'pending',
                            user_achievements.c.achievement_id.in_(
                                db.query(Achievement.id).filter(Achievement.frequency == frequency)
                            )
                        )
                    ).delete(synchronize_session=False)
                    
                    num_to_select = min(len(available_achievements), target_count)
                    
                    if num_to_select == 0:
                        continue

                    selected_achievements = random.sample(available_achievements, num_to_select)
                    
                    due_date = datetime.utcnow()
                    if frequency == 'daily':
                        due_date += timedelta(days=1)
                    elif frequency == 'weekly':
                        due_date += timedelta(weeks=1)
                    elif frequency == 'monthly':
                        due_date += timedelta(days=30)

                    for achievement in selected_achievements:
                        goal_assignment = {
                            'user_id': user.id,
                            'achievement_id': achievement.id,
                            'status': 'pending',
                            'due_date': due_date,
                            'created_at': datetime.utcnow()
                        }
                        db.execute(user_achievements.insert().values(**goal_assignment))
                        results["total_goals_assigned"] += 1
                    
                    results["assigned_to_users"] += 1
                    
                except Exception as e:
                    error_msg = f"Error assigning {frequency} goals to user {user.id}: {str(e)}"
                    results["errors"].append(error_msg)
                    logger.error(error_msg)
            
            return results
            
        except Exception as e:
            logger.error(f"General error in assign_{frequency}_goals: {str(e)}")
            raise

    @staticmethod
    def assign_daily_goals(db: Session, user_id: int = None) -> Dict:
        results = GoalCRUD._assign_goals_by_frequency(db, 'daily', 5, user_id)
        db.commit()
        return results
    
    @staticmethod
    def assign_weekly_goals(db: Session, user_id: int = None) -> Dict:
        results = GoalCRUD._assign_goals_by_frequency(db, 'weekly', 3, user_id)
        db.commit()
        return results
    
    @staticmethod
    def assign_monthly_goals(db: Session, user_id: int = None) -> Dict:
        results = GoalCRUD._assign_goals_by_frequency(db, 'monthly', 2, user_id)
        db.commit()
        return results
    
    @staticmethod
    def assign_goals_for_new_user(db: Session, user_id: int) -> Dict:
        try:
            daily_result = GoalCRUD._assign_goals_by_frequency(db, 'daily', 5, user_id)
            weekly_result = GoalCRUD._assign_goals_by_frequency(db, 'weekly', 3, user_id)
            monthly_result = GoalCRUD._assign_goals_by_frequency(db, 'monthly', 2, user_id)
            
            db.commit()
            
            return {
                "daily": daily_result,
                "weekly": weekly_result,
                "monthly": monthly_result
            }
        except Exception as e:
            db.rollback()
            logger.error(f"Error assigning goals for new user {user_id}: {str(e)}")
            raise

    @staticmethod
    def get_user_progress(db: Session, user_id: int) -> Dict:
        try:
            now = datetime.utcnow()
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            week_start = now - timedelta(days=7)
            month_start = now - timedelta(days=30)
            
            daily_pending = db.query(func.count(user_achievements.c.user_id)).select_from(user_achievements.join(Achievement)).filter(
                and_(user_achievements.c.user_id == user_id, user_achievements.c.status == 'pending', Achievement.frequency == 'daily', user_achievements.c.due_date > now)).scalar() or 0
            
            daily_completed = db.query(func.count(user_achievements.c.user_id)).select_from(user_achievements.join(Achievement)).filter(
                and_(user_achievements.c.user_id == user_id, user_achievements.c.status == 'completed', Achievement.frequency == 'daily', user_achievements.c.created_at >= today_start)).scalar() or 0
            
            weekly_pending = db.query(func.count(user_achievements.c.user_id)).select_from(user_achievements.join(Achievement)).filter(
                and_(user_achievements.c.user_id == user_id, user_achievements.c.status == 'pending', Achievement.frequency == 'weekly', user_achievements.c.due_date > now)).scalar() or 0
            
            weekly_completed = db.query(func.count(user_achievements.c.user_id)).select_from(user_achievements.join(Achievement)).filter(
                and_(user_achievements.c.user_id == user_id, user_achievements.c.status == 'completed', Achievement.frequency == 'weekly', user_achievements.c.created_at >= week_start)).scalar() or 0
            
            monthly_pending = db.query(func.count(user_achievements.c.user_id)).select_from(user_achievements.join(Achievement)).filter(
                and_(user_achievements.c.user_id == user_id, user_achievements.c.status == 'pending', Achievement.frequency == 'monthly', user_achievements.c.due_date > now)).scalar() or 0
            
            monthly_completed = db.query(func.count(user_achievements.c.user_id)).select_from(user_achievements.join(Achievement)).filter(
                and_(user_achievements.c.user_id == user_id, user_achievements.c.status == 'completed', Achievement.frequency == 'monthly', user_achievements.c.created_at >= month_start)).scalar() or 0
            
            total_points = db.query(func.sum(Achievement.point_value)).select_from(user_achievements.join(Achievement)).filter(
                and_(user_achievements.c.user_id == user_id, user_achievements.c.status == 'completed')).scalar() or 0
            
            return {
                "daily": {"completed": daily_completed, "total": 5, "assigned": daily_pending},
                "weekly": {"completed": weekly_completed, "total": 3, "assigned": weekly_pending},
                "monthly": {"completed": monthly_completed, "total": 2, "assigned": monthly_pending},
                "total_points": int(total_points)
            }
        except Exception as e:
            logger.error(f"Error getting user progress: {str(e)}")
            return {
                "daily": {"completed": 0, "total": 5, "assigned": 0},
                "weekly": {"completed": 0, "total": 3, "assigned": 0},
                "monthly": {"completed": 0, "total": 2, "assigned": 0},
                "total_points": 0
            }
    
    @staticmethod
    def complete_achievement(db: Session, user_id: int, achievement_id: int) -> Dict:
        try:
            goal_assignment = db.query(user_achievements).filter(and_(
                user_achievements.c.user_id == user_id,
                user_achievements.c.achievement_id == achievement_id,
                user_achievements.c.status == 'pending'
            )).first()
            
            if not goal_assignment:
                raise Exception("Achievement not found or already completed")
            
            db.query(user_achievements).filter(and_(
                user_achievements.c.user_id == user_id,
                user_achievements.c.achievement_id == achievement_id,
                user_achievements.c.status == 'pending'
            )).update({'status': 'completed', 'created_at': datetime.utcnow()})
            
            achievement = db.query(Achievement).filter(Achievement.id == achievement_id).first()
            if not achievement:
                raise Exception("Achievement not found")
            
            db.commit()
            
            return {
                "message": f"Achievement '{achievement.title}' completed!",
                "points_earned": achievement.point_value,
                "achievement_id": achievement_id,
                "user_id": user_id,
                "completed_at": datetime.utcnow().isoformat()
            }
        except Exception as e:
            db.rollback()
            logger.error(f"Error completing achievement: {str(e)}")
            raise Exception(f"Failed to complete achievement: {str(e)}")
    
    @staticmethod
    def get_user_current_goals(db: Session, user_id: int) -> Dict:
        try:
            now = datetime.utcnow()
            goals_query = db.query(
                Achievement.id, Achievement.title, Achievement.description,
                Achievement.point_value, Achievement.duration, Achievement.frequency,
                user_achievements.c.due_date, user_achievements.c.created_at
            ).select_from(user_achievements.join(Achievement)).filter(
                and_(
                    user_achievements.c.user_id == user_id,
                    user_achievements.c.status == 'pending',
                    user_achievements.c.due_date > now
                )
            ).order_by(Achievement.frequency, user_achievements.c.created_at)
            
            goals = goals_query.all()
            
            daily_goals = []
            weekly_goals = []
            monthly_goals = []
            
            for goal in goals:
                goal_data = {
                    "id": goal.id, "title": goal.title, "description": goal.description,
                    "points": goal.point_value, "duration": goal.duration, "category": goal.frequency,
                    "due_date": goal.due_date.isoformat() if goal.due_date else None,
                    "assigned_at": goal.created_at.isoformat() if goal.created_at else None
                }
                
                if goal.frequency == 'daily':
                    daily_goals.append(goal_data)
                elif goal.frequency == 'weekly':
                    weekly_goals.append(goal_data)
                elif goal.frequency == 'monthly':
                    monthly_goals.append(goal_data)
            
            return {
                "daily": daily_goals,
                "weekly": weekly_goals,
                "monthly": monthly_goals
            }
        except Exception as e:
            logger.error(f"Error getting user goals: {str(e)}")
            return {"daily": [], "weekly": [], "monthly": []}
    
    @staticmethod
    def cleanup_expired_goals(db: Session) -> int:
        try:
            now = datetime.utcnow()
            updated_count = db.query(user_achievements).filter(
                and_(user_achievements.c.status == 'pending', user_achievements.c.due_date < now)
            ).update({'status': 'expired'}, synchronize_session=False)
            
            db.commit()
            logger.info(f"Marked {updated_count} goals as expired")
            return updated_count
        except Exception as e:
            db.rollback()
            logger.error(f"Error cleaning up expired goals: {str(e)}")
            return 0
    
    @staticmethod
    def get_recent_completed_achievements(db: Session, user_id: int, limit: int = 10) -> List[Dict]:
        try:
            recent_query = db.query(
                Achievement.id, Achievement.title, Achievement.point_value,
                user_achievements.c.created_at.label('completed_at')
            ).select_from(user_achievements.join(Achievement)).filter(
                and_(user_achievements.c.user_id == user_id, user_achievements.c.status == 'completed')
            ).order_by(user_achievements.c.created_at.desc()).limit(limit)
            
            recent = recent_query.all()
            
            achievements = []
            for row in recent:
                achievements.append({
                    "id": row.id, "title": row.title, "points": row.point_value,
                    "completed_at": row.completed_at.isoformat() if row.completed_at else None
                })
            
            return achievements
        except Exception as e:
            logger.error(f"Error getting recent achievements: {str(e)}")
            return []