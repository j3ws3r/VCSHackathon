# app/services/goal_manager.py
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, text
from app.models.achievements import Achievement, user_achievements
from app.models.users import User
from datetime import datetime, timedelta
import random
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

class GoalManager:
    """Manages automatic goal assignment for users"""
    
    @staticmethod
    def assign_daily_goals(db: Session, user_id: int = None) -> Dict:
        """Assign 5 random daily achievements to user(s)"""
        try:
            # Get users to assign goals to
            if user_id:
                users = db.query(User).filter(User.id == user_id, User.is_active == True).all()
            else:
                users = db.query(User).filter(User.is_active == True).all()
            
            results = {"assigned": 0, "errors": []}
            
            for user in users:
                try:
                    # Clear existing pending daily goals
                    db.execute(
                        text("""
                            DELETE FROM user_achievements 
                            WHERE user_id = :user_id 
                            AND status = 'pending' 
                            AND achievement_id IN (
                                SELECT id FROM achievements WHERE frequency = 'daily'
                            )
                        """),
                        {"user_id": user.id}
                    )
                    
                    # Get available daily achievements
                    daily_achievements = db.query(Achievement).filter(
                        Achievement.frequency == 'daily'
                    ).all()
                    
                    if len(daily_achievements) < 5:
                        results["errors"].append(f"Not enough daily achievements for user {user.id}")
                        continue
                    
                    # Randomly select 5 achievements
                    selected_achievements = random.sample(daily_achievements, 5)
                    
                    # Assign them
                    for achievement in selected_achievements:
                        due_date = datetime.utcnow() + timedelta(days=1)
                        db.execute(
                            text("""
                                INSERT INTO user_achievements (user_id, achievement_id, status, due_date, created_at)
                                VALUES (:user_id, :achievement_id, 'pending', :due_date, :created_at)
                            """),
                            {
                                "user_id": user.id,
                                "achievement_id": achievement.id,
                                "due_date": due_date,
                                "created_at": datetime.utcnow()
                            }
                        )
                    
                    results["assigned"] += 1
                    logger.info(f"Assigned 5 daily goals to user {user.id}")
                    
                except Exception as e:
                    results["errors"].append(f"Error assigning daily goals to user {user.id}: {str(e)}")
                    logger.error(f"Error assigning daily goals to user {user.id}: {str(e)}")
            
            db.commit()
            return results
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error in assign_daily_goals: {str(e)}")
            raise Exception(f"Failed to assign daily goals: {str(e)}")
    
    @staticmethod
    def assign_weekly_goals(db: Session, user_id: int = None) -> Dict:
        """Assign 3 random weekly achievements to user(s)"""
        try:
            # Get users to assign goals to
            if user_id:
                users = db.query(User).filter(User.id == user_id, User.is_active == True).all()
            else:
                users = db.query(User).filter(User.is_active == True).all()
            
            results = {"assigned": 0, "errors": []}
            
            for user in users:
                try:
                    # Clear existing pending weekly goals
                    db.execute(
                        text("""
                            DELETE FROM user_achievements 
                            WHERE user_id = :user_id 
                            AND status = 'pending' 
                            AND achievement_id IN (
                                SELECT id FROM achievements WHERE frequency = 'weekly'
                            )
                        """),
                        {"user_id": user.id}
                    )
                    
                    # Get available weekly achievements
                    weekly_achievements = db.query(Achievement).filter(
                        Achievement.frequency == 'weekly'
                    ).all()
                    
                    if len(weekly_achievements) < 3:
                        results["errors"].append(f"Not enough weekly achievements for user {user.id}")
                        continue
                    
                    # Randomly select 3 achievements
                    selected_achievements = random.sample(weekly_achievements, 3)
                    
                    # Assign them
                    for achievement in selected_achievements:
                        due_date = datetime.utcnow() + timedelta(days=7)
                        db.execute(
                            text("""
                                INSERT INTO user_achievements (user_id, achievement_id, status, due_date, created_at)
                                VALUES (:user_id, :achievement_id, 'pending', :due_date, :created_at)
                            """),
                            {
                                "user_id": user.id,
                                "achievement_id": achievement.id,
                                "due_date": due_date,
                                "created_at": datetime.utcnow()
                            }
                        )
                    
                    results["assigned"] += 1
                    logger.info(f"Assigned 3 weekly goals to user {user.id}")
                    
                except Exception as e:
                    results["errors"].append(f"Error assigning weekly goals to user {user.id}: {str(e)}")
                    logger.error(f"Error assigning weekly goals to user {user.id}: {str(e)}")
            
            db.commit()
            return results
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error in assign_weekly_goals: {str(e)}")
            raise Exception(f"Failed to assign weekly goals: {str(e)}")
    
    @staticmethod
    def assign_monthly_goals(db: Session, user_id: int = None) -> Dict:
        """Assign 2 random monthly achievements to user(s)"""
        try:
            # Get users to assign goals to
            if user_id:
                users = db.query(User).filter(User.id == user_id, User.is_active == True).all()
            else:
                users = db.query(User).filter(User.is_active == True).all()
            
            results = {"assigned": 0, "errors": []}
            
            for user in users:
                try:
                    # Clear existing pending monthly goals
                    db.execute(
                        text("""
                            DELETE FROM user_achievements 
                            WHERE user_id = :user_id 
                            AND status = 'pending' 
                            AND achievement_id IN (
                                SELECT id FROM achievements WHERE frequency = 'monthly'
                            )
                        """),
                        {"user_id": user.id}
                    )
                    
                    # Get available monthly achievements
                    monthly_achievements = db.query(Achievement).filter(
                        Achievement.frequency == 'monthly'
                    ).all()
                    
                    if len(monthly_achievements) < 2:
                        results["errors"].append(f"Not enough monthly achievements for user {user.id}")
                        continue
                    
                    # Randomly select 2 achievements
                    selected_achievements = random.sample(monthly_achievements, 2)
                    
                    # Assign them
                    for achievement in selected_achievements:
                        due_date = datetime.utcnow() + timedelta(days=30)
                        db.execute(
                            text("""
                                INSERT INTO user_achievements (user_id, achievement_id, status, due_date, created_at)
                                VALUES (:user_id, :achievement_id, 'pending', :due_date, :created_at)
                            """),
                            {
                                "user_id": user.id,
                                "achievement_id": achievement.id,
                                "due_date": due_date,
                                "created_at": datetime.utcnow()
                            }
                        )
                    
                    results["assigned"] += 1
                    logger.info(f"Assigned 2 monthly goals to user {user.id}")
                    
                except Exception as e:
                    results["errors"].append(f"Error assigning monthly goals to user {user.id}: {str(e)}")
                    logger.error(f"Error assigning monthly goals to user {user.id}: {str(e)}")
            
            db.commit()
            return results
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error in assign_monthly_goals: {str(e)}")
            raise Exception(f"Failed to assign monthly goals: {str(e)}")
    
    @staticmethod
    def get_user_progress(db: Session, user_id: int) -> Dict:
        """Get user's current goal progress"""
        try:
            # Daily progress
            daily_total = db.execute(
                text("""
                    SELECT COUNT(*) FROM user_achievements ua
                    JOIN achievements a ON ua.achievement_id = a.id
                    WHERE ua.user_id = :user_id 
                    AND a.frequency = 'daily' 
                    AND ua.status = 'pending'
                    AND ua.due_date > :now
                """),
                {"user_id": user_id, "now": datetime.utcnow()}
            ).scalar() or 0
            
            daily_completed = db.execute(
                text("""
                    SELECT COUNT(*) FROM user_achievements ua
                    JOIN achievements a ON ua.achievement_id = a.id
                    WHERE ua.user_id = :user_id 
                    AND a.frequency = 'daily' 
                    AND ua.status = 'completed'
                    AND DATE(ua.created_at) = DATE(:today)
                """),
                {"user_id": user_id, "today": datetime.utcnow()}
            ).scalar() or 0
            
            # Weekly progress
            weekly_total = db.execute(
                text("""
                    SELECT COUNT(*) FROM user_achievements ua
                    JOIN achievements a ON ua.achievement_id = a.id
                    WHERE ua.user_id = :user_id 
                    AND a.frequency = 'weekly' 
                    AND ua.status = 'pending'
                    AND ua.due_date > :now
                """),
                {"user_id": user_id, "now": datetime.utcnow()}
            ).scalar() or 0
            
            weekly_completed = db.execute(
                text("""
                    SELECT COUNT(*) FROM user_achievements ua
                    JOIN achievements a ON ua.achievement_id = a.id
                    WHERE ua.user_id = :user_id 
                    AND a.frequency = 'weekly' 
                    AND ua.status = 'completed'
                    AND ua.created_at >= :week_start
                """),
                {"user_id": user_id, "week_start": datetime.utcnow() - timedelta(days=7)}
            ).scalar() or 0
            
            # Monthly progress
            monthly_total = db.execute(
                text("""
                    SELECT COUNT(*) FROM user_achievements ua
                    JOIN achievements a ON ua.achievement_id = a.id
                    WHERE ua.user_id = :user_id 
                    AND a.frequency = 'monthly' 
                    AND ua.status = 'pending'
                    AND ua.due_date > :now
                """),
                {"user_id": user_id, "now": datetime.utcnow()}
            ).scalar() or 0
            
            monthly_completed = db.execute(
                text("""
                    SELECT COUNT(*) FROM user_achievements ua
                    JOIN achievements a ON ua.achievement_id = a.id
                    WHERE ua.user_id = :user_id 
                    AND a.frequency = 'monthly' 
                    AND ua.status = 'completed'
                    AND ua.created_at >= :month_start
                """),
                {"user_id": user_id, "month_start": datetime.utcnow() - timedelta(days=30)}
            ).scalar() or 0
            
            # Total points
            total_points = db.execute(
                text("""
                    SELECT COALESCE(SUM(a.point_value), 0) FROM user_achievements ua
                    JOIN achievements a ON ua.achievement_id = a.id
                    WHERE ua.user_id = :user_id AND ua.status = 'completed'
                """),
                {"user_id": user_id}
            ).scalar() or 0
            
            return {
                "daily": {
                    "completed": daily_completed,
                    "total": 5,  # Always 5 daily goals
                    "assigned": daily_total
                },
                "weekly": {
                    "completed": weekly_completed,
                    "total": 3,  # Always 3 weekly goals
                    "assigned": weekly_total
                },
                "monthly": {
                    "completed": monthly_completed,
                    "total": 2,  # Always 2 monthly goals
                    "assigned": monthly_total
                },
                "total_points": total_points
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
        """Mark an achievement as completed for a user"""
        try:
            # Check if user has this achievement assigned and pending
            result = db.execute(
                text("""
                    UPDATE user_achievements 
                    SET status = 'completed', created_at = :completed_at
                    WHERE user_id = :user_id 
                    AND achievement_id = :achievement_id 
                    AND status = 'pending'
                """),
                {
                    "user_id": user_id,
                    "achievement_id": achievement_id,
                    "completed_at": datetime.utcnow()
                }
            )
            
            if result.rowcount == 0:
                raise Exception("Achievement not found or already completed")
            
            # Get achievement details
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
        """Get user's current pending goals by category"""
        try:
            goals = db.execute(
                text("""
                    SELECT a.id, a.title, a.description, a.point_value, 
                           a.duration, a.frequency, ua.due_date, ua.created_at
                    FROM user_achievements ua
                    JOIN achievements a ON ua.achievement_id = a.id
                    WHERE ua.user_id = :user_id 
                    AND ua.status = 'pending'
                    AND ua.due_date > :now
                    ORDER BY a.frequency, ua.created_at
                """),
                {"user_id": user_id, "now": datetime.utcnow()}
            ).fetchall()
            
            daily_goals = []
            weekly_goals = []
            monthly_goals = []
            
            for goal in goals:
                goal_data = {
                    "id": goal.id,
                    "title": goal.title,
                    "description": goal.description,
                    "points": goal.point_value,
                    "duration": goal.duration,
                    "category": goal.frequency,
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
            return {
                "daily": [],
                "weekly": [],
                "monthly": []
            }