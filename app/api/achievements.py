from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, BackgroundTasks, Form
from sqlalchemy.orm import Session
from typing import Optional
import shutil
import os
import tempfile
from app.core.database import get_db
from app.services.archievements_import import parse_excel, bulk_insert_achievements
from app.api.routes import get_current_user
from app.models.achievements import Achievement
from app.schemas.achievements import AchievementCreate, AchievementResponse
from datetime import datetime

router = APIRouter()

@router.post("/create-achievement", response_model=AchievementResponse)
async def create_achievement(
    title: str = Form(...),
    description: str = Form(...),
    category: str = Form(...),
    duration: str = Form(...),
    points: int = Form(...),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Create a new achievement from the web form"""
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
            "message": f"Achievement '{title}' created successfully!"
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create achievement: {str(e)}")

def convert_duration_to_minutes(duration_str: str) -> int:
    """Convert duration string to minutes"""
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

@router.get("/achievements/")
async def get_achievements(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get all achievements"""
    achievements = db.query(Achievement).offset(skip).limit(limit).all()
    return {
        "achievements": [
            {
                "id": ach.id,
                "title": ach.title,
                "description": ach.description,
                "points": ach.point_value,  
                "duration": ach.duration,
                "category": ach.frequency,
                "created_at": ach.created_at
            }
            for ach in achievements
        ]
    }

@router.post("/upload")
async def upload_excel(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Upload Excel file with achievements"""
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Invalid file type")
    
    temp_dir = tempfile.gettempdir()
    file_path = os.path.join(temp_dir, file.filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    def process_file():
        try:
            data = parse_excel(file_path)
            result = bulk_insert_achievements(data, db)
            print(result)
        except Exception as e:
            print(f"Error processing file: {e}")
        finally:
            if os.path.exists(file_path):
                os.remove(file_path)
    
    background_tasks.add_task(process_file)
    return {"message": "File is being processed", "filename": file.filename}

@router.post("/preview")
async def preview_excel(
    file: UploadFile = File(...),
    current_user = Depends(get_current_user)
):
    """Preview Excel file contents"""
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Invalid file type")
    
    temp_dir = tempfile.gettempdir()
    file_path = os.path.join(temp_dir, f"preview_{file.filename}")
    
    with open(file_path, "wb") as f:
        f.write(await file.read())
    
    try:
        data = parse_excel(file_path)
        return {"preview": [item.dict() for item in data[:10]]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse file: {str(e)}")
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)