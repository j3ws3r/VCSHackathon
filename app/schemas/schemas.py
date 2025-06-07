<<<<<<< HEAD
from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime
=======
from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional, Literal
from datetime import datetime
from enum import Enum

class UserRole(str, Enum):
    PATIENT = "patient"
    THERAPIST = "therapist" 
    ADMIN = "admin"
>>>>>>> fa20ba1 (Authenification file created, depentancies updated)

class UserBase(BaseModel):
    username: str
    email: EmailStr
<<<<<<< HEAD

class UserCreate(UserBase):
    pass
=======
    full_name: Optional[str] = None
    role: UserRole = UserRole.PATIENT

class UserCreate(UserBase):
    password: str = Field(..., min_length=12, description="Password must be at least 12 characters")
>>>>>>> fa20ba1 (Authenification file created, depentancies updated)

class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
<<<<<<< HEAD
=======
    full_name: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
>>>>>>> fa20ba1 (Authenification file created, depentancies updated)

class User(UserBase):
    id: int
    created_at: datetime
<<<<<<< HEAD
=======
    is_active: bool
    is_verified: bool
    last_login: Optional[datetime] = None
    failed_login_attempts: int
    locked_until: Optional[datetime] = None
>>>>>>> fa20ba1 (Authenification file created, depentancies updated)
    items: List['Item'] = []
    
    class Config:
        from_attributes = True

<<<<<<< HEAD
=======
# Authentication-specific schemas
class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int

class TokenData(BaseModel):
    user_id: Optional[int] = None
    email: Optional[str] = None
    role: Optional[str] = None

class UserResponse(BaseModel):
    id: int
    username: str
    email: EmailStr
    full_name: Optional[str] = None
    role: UserRole
    is_active: bool
    is_verified: bool
    created_at: datetime
    last_login: Optional[datetime] = None
    
    class Config:
        from_attributes = True

>>>>>>> fa20ba1 (Authenification file created, depentancies updated)
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