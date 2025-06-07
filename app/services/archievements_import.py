from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field, ValidationError
from sqlalchemy.orm import Session
from typing import List
import openpyxl
import shutil
import os

from app.api.routes import get_current_user  # Use existing auth dependency
from app.core.database import get_db
from app.models.achievements import Achievement  # Fixed path
from app.core.database import Base
from sqlalchemy import and_

router = APIRouter(prefix="/admin/import", tags=["Import"])

# ------------------
# Pydantic Schema
# ------------------
class AchievementImport(BaseModel):
    title: str = Field(..., max_length=255)
    description: str
    frequency: str
    duration: int = Field(..., gt=0)
    points_value: int = Field(..., ge=0)

# ------------------
# Parse Excel
# ------------------
def parse_excel(file_path: str) -> List[AchievementImport]:
    workbook = openpyxl.load_workbook(file_path)
    sheet = workbook.active
    data = []
    for i, row in enumerate(sheet.iter_rows(min_row=2, values_only=True), start=2):
        try:
            record = AchievementImport(
                title=row[0],
                description=row[1],
                frequency=row[2],
                duration=row[3],
                points_value=row[4]
            )
            data.append(record)
        except ValidationError as e:
            print(f"Row {i} validation error: {e}")
    return data

# ------------------
# DB Insert
# ------------------
def bulk_insert_achievements(data: List[AchievementImport], db: Session):
    created, skipped = 0, 0
    for item in data:
        exists = db.query(Achievement).filter(
            and_(Achievement.title == item.title, Achievement.duration == item.duration)
        ).first()
        if exists:
            skipped += 1
            continue
        # Create achievement with explicit field mapping
        new_entry = Achievement(
            title=item.title,
            description=item.description,
            frequency=item.frequency,
            duration=item.duration,
            points_value=item.points_value,
            point_value=item.points_value  # For backward compatibility
        )
        db.add(new_entry)
        created += 1
    db.commit()
    return {"created": created, "skipped": skipped}