from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime

class UserBase(BaseModel):
    username: str
    email: EmailStr

class UserCreate(UserBase):
    pass

class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None

class User(UserBase):
    id: int
    created_at: datetime
    items: List['Item'] = []
    
    class Config:
        from_attributes = True

class ItemBase(BaseModel):
    title: str
    description: Optional[str] = None

class ItemCreate(ItemBase):
    user_id: Optional[int] = None

class ItemUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None

class Item(ItemBase):
    id: int
    user_id: Optional[int] = None
    created_at: datetime
    owner: Optional[User] = None
    
    class Config:
        from_attributes = True

User.model_rebuild()