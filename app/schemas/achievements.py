from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class AchievementBase(BaseModel):
    title: str
    description: Optional[str] = None
    point_value: int 
    duration: int
    frequency: str

class AchievementCreate(AchievementBase):
    pass

class AchievementResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    points: int 
    duration: int
    category: str
    message: Optional[str] = None
    
    class Config:
        from_attributes = True

class Achievement(AchievementBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True