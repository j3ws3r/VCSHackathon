from pydantic import BaseModel, Field, ValidationError
from sqlalchemy.orm import Session
from typing import List, IO
import openpyxl
from app.models.achievements import Achievement
from sqlalchemy import and_

class AchievementImport(BaseModel):
    title: str = Field(..., max_length=255)
    description: str
    frequency: str = Field(..., max_length=50)
    duration: int = Field(..., gt=0)
    point_value: int = Field(..., ge=0)

def parse_excel_from_memory(file: IO) -> List[AchievementImport]:
    """Parse an Excel file from an in-memory file-like object."""
    workbook = None
    try:
        workbook = openpyxl.load_workbook(file)
        sheet = workbook.active
        data = []
        
        for i, row in enumerate(sheet.iter_rows(min_row=2, values_only=True), start=2):
            try:
                if len(row) < 5 or row[0] is None:
                    print(f"Row {i} skipped: not enough data or title is missing.")
                    continue

                record = AchievementImport(
                    title=row[0],
                    description=row[1],
                    frequency=row[2],
                    duration=row[3],
                    point_value=row[4]
                )
                data.append(record)
            except ValidationError as e:
                print(f"Row {i} validation error: {e}")
            except Exception as e:
                print(f"Row {i} processing error: {e}")
        
        return data
    finally:
        if workbook:
            workbook.close()

def bulk_insert_achievements(data: List[AchievementImport], db: Session):
    """Bulk insert achievements into the database."""
    created, skipped = 0, 0
    
    for item in data:
        exists = db.query(Achievement).filter(
            and_(Achievement.title == item.title, Achievement.duration == item.duration)
        ).first()
        
        if exists:
            skipped += 1
            continue
        
        new_entry = Achievement(
            title=item.title,
            description=item.description,
            frequency=item.frequency,
            duration=item.duration,
            point_value=item.point_value 
        )
        
        db.add(new_entry)
        created += 1
    
    try:
        db.commit()
        return {"created": created, "skipped": skipped}
    except Exception as e:
        db.rollback()
        raise Exception(f"Database error: {str(e)}")