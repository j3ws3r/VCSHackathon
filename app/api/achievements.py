from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, List
from app.core.database import get_db
from app.models.achievements import Achievement as AchievementModel
from app.models.users import User
from app.services.goal_crud import GoalCRUD
from app.schemas.achievements import Achievement, UserProgress, UserStats, AchievementListResponse
from app.api.authentication import JWTManager, AuthError
from app.services.crud import UserCRUD as UserCRUDService
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    try:
        payload = JWTManager.verify_token(credentials.credentials)
        user_id = payload.get("user_id")
        if user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    except AuthError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    user = UserCRUDService.get_user(db, user_id=user_id)
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")
    return user

async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> int:
    try:
        payload = JWTManager.verify_token(credentials.credentials)
        user_id = payload.get("user_id")
        if user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        return user_id
    except AuthError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

router = APIRouter()

@router.get("/achievements/", response_model=dict)
async def get_user_current_goals(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        goals = GoalCRUD.get_user_current_goals(db, current_user.id)
        all_achievements = goals.get("daily", []) + goals.get("weekly", []) + goals.get("monthly", [])
        return {
            "achievements": all_achievements,
            "total": len(all_achievements),
            "goals_by_category": goals
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get goals: {str(e)}")

@router.get("/achievements/all", response_model=AchievementListResponse)
async def get_all_achievements(
    skip: int = 0,
    limit: int = 100,
    category: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(AchievementModel)
    if category:
        query = query.filter(AchievementModel.frequency.ilike(f"%{category}%"))
    total_count = query.count()
    achievements_from_db = query.offset(skip).limit(limit).all()
    return {
        "achievements": achievements_from_db,
        "total": total_count,
        "category_filter": category
    }

@router.get("/achievements/categories", response_model=dict)
async def get_achievement_categories(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        categories_query = db.query(AchievementModel.frequency, func.count(AchievementModel.id)).group_by(AchievementModel.frequency).all()
        category_stats = {category: count for category, count in categories_query if category}
        return {
            "categories": category_stats,
            "total_achievements": sum(category_stats.values())
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get categories: {str(e)}")

@router.get("/achievements/recent", response_model=dict)
async def get_recent_achievements(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        achievements = GoalCRUD.get_recent_completed_achievements(db, current_user.id)
        return {
            "achievements": achievements,
            "total": len(achievements)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get recent achievements: {str(e)}")

@router.get("/achievements/{achievement_id}", response_model=Achievement)
async def get_achievement(
    achievement_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    achievement = db.query(AchievementModel).filter(AchievementModel.id == achievement_id).first()
    if not achievement:
        raise HTTPException(status_code=404, detail="Achievement not found")
    return achievement

@router.post("/achievements/{achievement_id}/complete", response_model=dict)
async def complete_achievement(
    achievement_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        result = GoalCRUD.complete_achievement(db, current_user.id, achievement_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/progress/")
async def get_user_progress(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    try:
        progress = GoalCRUD.get_user_progress(db, user_id)
        return JSONResponse(content=progress)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get user progress: {str(e)}")

@router.get("/users/stats")
async def get_user_stats(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    try:
        progress = GoalCRUD.get_user_progress(db, user_id)
        response_data = {
            "total_points": progress.get("total_points", 0),
            "completed_today": progress.get("daily", {}).get("completed", 0),
            "weekly_streak": 0,
            "rank": "-"
        }
        return JSONResponse(content=response_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get user stats: {str(e)}")