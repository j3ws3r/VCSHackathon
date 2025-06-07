from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, BackgroundTasks, Form
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import shutil
import os
import tempfile
import traceback
from datetime import datetime

from app.core.database import get_db, SessionLocal
from app.schemas.schemas import User, UserUpdate
from app.services.crud import UserCRUD 
from app.services.goal_crud import GoalCRUD
from app.api.dependencies import (
    get_current_admin_user, get_current_super_admin_user, 
    require_role, get_query_params, CommonQueryParams
)
from app.api.authentication import UserRole
from app.models.achievements import Achievement

router = APIRouter(prefix="/admin", tags=["Admin"])

@router.post("/goals/assign-daily-all", summary="Manually Assign Daily Goals")
def assign_daily_goals_all(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    try:
        result = GoalCRUD.assign_daily_goals(db)
        return {
            "message": "Daily goal assignment process triggered for all active users.",
            "result": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to assign daily goals: {str(e)}")

@router.post("/goals/assign-weekly-all", summary="Manually Assign Weekly Goals")
def assign_weekly_goals_all(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    try:
        result = GoalCRUD.assign_weekly_goals(db)
        return {
            "message": "Weekly goal assignment process triggered for all active users.",
            "result": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to assign weekly goals: {str(e)}")

@router.post("/goals/assign-monthly-all", summary="Manually Assign Monthly Goals")
def assign_monthly_goals_all(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    try:
        result = GoalCRUD.assign_monthly_goals(db)
        return {
            "message": "Monthly goal assignment process triggered for all active users.",
            "result": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to assign monthly goals: {str(e)}")
        
@router.post("/goals/reassign/{user_id}", summary="Re-assign All Goals for a User")
def reassign_goals_for_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    db_user = UserCRUD.get_user(db, user_id=user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    try:
        result = GoalCRUD.assign_goals_for_new_user(db, user_id)
        return {
            "message": f"All goals have been successfully reassigned to user {db_user.username} (ID: {user_id}).",
            "details": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reassign goals: {str(e)}")

@router.post("/users/{user_id}/activate")
def activate_user(
    user_id: int,
    current_user = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    db_user = UserCRUD.get_user(db, user_id=user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if db_user.customer_id != current_user.customer_id:
        raise HTTPException(status_code=403, detail="User not found in your organization")
    
    update_data = UserUpdate(is_active=True)
    updated_user = UserCRUD.update_user(db, user_id=user_id, user_update=update_data)
    
    return {"message": f"User {updated_user.username} activated successfully"}

@router.post("/users/{user_id}/deactivate")
def deactivate_user(
    user_id: int,
    current_user = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate your own account"
        )
    
    db_user = UserCRUD.get_user(db, user_id=user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if db_user.customer_id != current_user.customer_id:
        raise HTTPException(status_code=403, detail="User not found in your organization")
    
    update_data = UserUpdate(is_active=False)
    updated_user = UserCRUD.update_user(db, user_id=user_id, user_update=update_data)
    
    return {"message": f"User {updated_user.username} deactivated successfully"}

@router.post("/users/{user_id}/promote")
def promote_user_to_moderator(
    user_id: int,
    current_user = Depends(get_current_super_admin_user),
    db: Session = Depends(get_db)
):
    db_user = UserCRUD.get_user(db, user_id=user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if db_user.customer_id != current_user.customer_id:
        raise HTTPException(status_code=403, detail="User not found in your organization")
    
    if db_user.role == "admin":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot change admin role"
        )
    
    update_data = UserUpdate(role="moderator")
    updated_user = UserCRUD.update_user(db, user_id=user_id, user_update=update_data)
    
    return {"message": f"User {updated_user.username} promoted to moderator"}

@router.post("/users/{user_id}/demote")
def demote_user_to_regular(
    user_id: int,
    current_user = Depends(get_current_super_admin_user),
    db: Session = Depends(get_db)
):
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot demote yourself"
        )
    
    db_user = UserCRUD.get_user(db, user_id=user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if db_user.customer_id != current_user.customer_id:
        raise HTTPException(status_code=403, detail="User not found in your organization")
    
    if db_user.role == "admin":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot demote admin users"
        )
    
    update_data = UserUpdate(role="user")
    updated_user = UserCRUD.update_user(db, user_id=user_id, user_update=update_data)
    
    return {"message": f"User {updated_user.username} demoted to regular user"}

@router.post("/users/{user_id}/unlock")
def unlock_user_account(
    user_id: int,
    current_user = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    db_user = UserCRUD.get_user(db, user_id=user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if db_user.customer_id != current_user.customer_id:
        raise HTTPException(status_code=403, detail="User not found in your organization")
    
    update_data = UserUpdate(failed_login_attempts=0, locked_until=None)
    updated_user = UserCRUD.update_user(db, user_id=user_id, user_update=update_data)
    
    return {"message": f"User {updated_user.username} account unlocked"}

@router.get("/users/locked")
def get_locked_users(
    query_params: CommonQueryParams = Depends(get_query_params),
    current_user = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    return {"message": "Feature coming soon", "locked_users": []}

@router.post("/achievements/upload")
async def upload_achievements_excel(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    from app.services.archievements_import import parse_excel_from_memory, bulk_insert_achievements

    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload an Excel file.")

    try:
        data = parse_excel_from_memory(file.file)
        result = bulk_insert_achievements(data, db)
        
        return {
            "message": "Achievements processed successfully.",
            "filename": file.filename,
            "created": result.get("created", 0),
            "skipped": result.get("skipped", 0)
        }
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to process file: {str(e)}")

@router.post("/achievements/preview")
async def preview_achievements_excel(
    file: UploadFile = File(...),
    current_user = Depends(get_current_admin_user)
):
    from app.services.archievements_import import parse_excel
    
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Invalid file type")
    
    temp_dir = tempfile.gettempdir()
    file_path = os.path.join(temp_dir, f"preview_{current_user.id}_{file.filename}")
    
    try:
        with open(file_path, "wb") as f:
            f.write(await file.read())
        
        data = parse_excel(file_path)
        return {
            "preview": [item.dict() for item in data[:10]] if hasattr(data[0], 'dict') else data[:10],
            "total_rows": len(data),
            "filename": file.filename,
            "previewed_by": current_user.username,
            "preview_time": datetime.utcnow().isoformat()
        }
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to parse file: {str(e)}")
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

@router.post("/achievements/create")
async def create_achievement(
    title: str = Form(...),
    description: str = Form(...),
    category: str = Form(...),
    duration: str = Form(...),
    points: int = Form(...),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    try:
        duration_minutes = convert_duration_to_minutes(duration)
        
        achievement = Achievement(
            title=title,
            description=description,
            point_value=points, 
            duration=duration_minutes,
            frequency=category,
            created_at=datetime.utcnow()
        )
        
        db.add(achievement)
        db.commit()
        db.refresh(achievement)
        
        return {
            "id": achievement.id,
            "title": achievement.title,
            "description": achievement.description,
            "points": achievement.point_value,
            "duration": achievement.duration,
            "category": achievement.frequency,
            "message": f"Achievement '{title}' created successfully!",
            "created_by": current_user.username
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create achievement: {str(e)}")

@router.delete("/achievements/{achievement_id}")
async def delete_achievement(
    achievement_id: int,
    current_user = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    try:
        achievement = db.query(Achievement).filter(Achievement.id == achievement_id).first()
        if not achievement:
            raise HTTPException(status_code=404, detail="Achievement not found")
        
        achievement_title = achievement.title
        db.delete(achievement)
        db.commit()
        
        return {
            "message": f"Achievement '{achievement_title}' deleted successfully",
            "deleted_by": current_user.username,
            "deleted_at": datetime.utcnow().isoformat()
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete achievement: {str(e)}")

@router.get("/stats")
def get_admin_stats(
    current_user = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    try:
        total_users = len(UserCRUD.get_users_by_customer(db, current_user.customer_id, limit=1000))
        active_users = len([u for u in UserCRUD.get_users_by_customer(db, current_user.customer_id, limit=1000) if u.is_active])
        
        customer_users = UserCRUD.get_users_by_customer(db, current_user.customer_id, limit=1000)
        admin_count = len([u for u in customer_users if u.role == "admin"])
        moderator_count = len([u for u in customer_users if u.role == "moderator"])
        regular_count = len([u for u in customer_users if u.role == "user"])
        
        total_achievements = db.query(Achievement).count()
        daily_achievements = db.query(Achievement).filter(Achievement.frequency == "daily").count()
        weekly_achievements = db.query(Achievement).filter(Achievement.frequency == "weekly").count()
        monthly_achievements = db.query(Achievement).filter(Achievement.frequency == "monthly").count()
        
        achievement_stats = {
            "total_achievements": total_achievements,
            "daily_achievements": daily_achievements,
            "weekly_achievements": weekly_achievements,
            "monthly_achievements": monthly_achievements
        }
        
        return {
            "customer_id": current_user.customer_id,
            "company_name": current_user.customer.company_name if hasattr(current_user, 'customer') else "Unknown",
            "total_users": total_users,
            "active_users": active_users,
            "inactive_users": total_users - active_users,
            "user_roles": {
                "admins": admin_count,
                "moderators": moderator_count,
                "regular_users": regular_count
            },
            **achievement_stats
        }
    except Exception as e:
        return {
            "error": str(e),
            "message": "Some statistics may be unavailable"
        }

@router.get("/users/search")
def search_users(
    q: str,
    query_params: CommonQueryParams = Depends(get_query_params),
    current_user = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    if len(q.strip()) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Search query must be at least 2 characters"
        )

    all_users = UserCRUD.get_users_by_customer(db, current_user.customer_id, limit=1000)
    
    search_results = []
    q_lower = q.lower()
    
    for user in all_users:
        if (q_lower in user.username.lower() or 
            q_lower in user.email.lower() or 
            (user.full_name and q_lower in user.full_name.lower())):
            search_results.append(user)
    
    start = query_params.skip
    end = start + query_params.limit
    paginated_results = search_results[start:end]
    
    return {
        "results": paginated_results,
        "total_found": len(search_results),
        "query": q,
        "searched_by": current_user.username
    }

def convert_duration_to_minutes(duration_str: str) -> int:
    duration_map = {
        "1-day": 1440,
        "1-week": 10080,
        "1-month": 43200,
        "3-months": 129600,
        "6-months": 259200,
        "1-year": 525600,
        "ongoing": 0
    }
    return duration_map.get(duration_str, 60)


def process_achievements_file(file_path: str, admin_username: str):
    db: Session = SessionLocal() 
    try:
        from app.services.archievements_import import parse_excel, bulk_insert_achievements
        print(f"Background task started for file: {file_path}")
        data = parse_excel(file_path)
        result = bulk_insert_achievements(data, db)
        print(f"Achievements uploaded by admin {admin_username}: {result}")
    except Exception as e:
        print(f"Error processing achievements file by {admin_username}: {e}")
    finally:
        db.close() 
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"Cleaned up temp file: {file_path}")