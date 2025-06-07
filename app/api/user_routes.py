"""
User management routes: CRUD operations for users
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.schemas.schemas import User, UserCreate, UserUpdate
from app.services.crud import UserCRUD 
from app.api.dependencies import (
    get_current_user, get_current_admin_user, get_query_params, 
    CommonQueryParams, require_role
)
from app.api.authentication import UserRole

router = APIRouter(prefix="/users", tags=["User Management"])

@router.post("/", response_model=User)
def create_user(
    user: UserCreate, 
    db: Session = Depends(get_db),
    current_user = Depends(require_role("admin"))
):
    """Create a new user (Admin only)"""
    db_user = UserCRUD.get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    db_user = UserCRUD.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    return UserCRUD.create_user(db=db, user=user)

@router.get("/", response_model=List[User])
def read_users(
    query_params: CommonQueryParams = Depends(get_query_params),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """Get list of users for current customer (Admin/Moderator only)"""
    users = UserCRUD.get_users_by_customer(
        db, 
        customer_id=current_user.customer_id,
        skip=query_params.skip, 
        limit=query_params.limit
    )
    return users

@router.get("/{user_id}", response_model=User)
def read_user(
    user_id: int, 
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get user by ID (Users can view their own profile, admins can view any within their customer)"""
    if current_user.role not in ["admin", "moderator"]:
        if current_user.id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view this user"
            )
    
    db_user = UserCRUD.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    if db_user.customer_id != current_user.customer_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User not found in your organization"
        )
    
    return db_user

@router.put("/{user_id}", response_model=User)
def update_user(
    user_id: int, 
    user_update: UserUpdate, 
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Update user information (Users can update their own profile, admins can update any)"""
    if current_user.role not in ["admin", "moderator"]:
        if current_user.id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this user"
            )
        
        if hasattr(user_update, 'role') and user_update.role is not None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot change user role"
            )
    
    db_user = UserCRUD.update_user(db, user_id=user_id, user_update=user_update)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

@router.delete("/{user_id}")
def delete_user(
    user_id: int, 
    db: Session = Depends(get_db),
    current_user = Depends(require_role("admin"))
):
    """Delete user (Admin only)"""
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )
    
    success = UserCRUD.delete_user(db, user_id=user_id)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User deleted successfully"}