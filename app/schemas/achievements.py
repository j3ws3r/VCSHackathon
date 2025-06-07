from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class AchievementBase(BaseModel):
    title: str
    description: Optional[str] = None
    point_value: int 
    duration: int
    frequency: str

class AchievementCreate(AchievementBase):
    pass

class Achievement(AchievementBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class ProgressCategory(BaseModel):
    completed: int
    total: int
    assigned: int

class UserProgress(BaseModel):
    daily: ProgressCategory
    weekly: ProgressCategory
    monthly: ProgressCategory
    total_points: int

class UserStats(BaseModel):
    total_points: int
    completed_today: int
    weekly_streak: int
    rank: str

class AchievementListResponse(BaseModel):
    achievements: List[Achievement]
    total: int
    category_filter: Optional[str] = None