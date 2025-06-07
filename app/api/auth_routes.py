"""
Authentication related routes: login, register, logout, password management, profile
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.schemas import (
    UserCreate, UserUpdate, UserResponse, UserLogin, Token
)
from app.services.crud import UserCRUD 
from app.api.authentication import (
    JWTManager, AuthError, InvalidCredentialsError, 
    WeakPasswordError, AccountLockedError, ACCESS_TOKEN_EXPIRE_MINUTES
)
from app.api.dependencies import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(user: UserCreate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """Register a new user (Admin only - creates user within their customer)"""
    try:
        if current_user.role not in ["admin", "moderator"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admins can register new users"
            )
        
        new_user = UserCRUD.create_user_for_customer(db=db, user=user, customer_id=current_user.customer_id)
        return new_user
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except WeakPasswordError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except AuthError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/login", response_model=Token)
def login_user(user_credentials: UserLogin, db: Session = Depends(get_db)):
    """Authenticate user and return JWT tokens"""
    try:
        user = UserCRUD.authenticate_user_for_customer(db, user_credentials.email, user_credentials.password)
        
        access_token = JWTManager.create_access_token(
            data={
                "user_id": user.id, 
                "email": user.email, 
                "role": user.role,
                "customer_id": user.customer_id 
            }
        )
        refresh_token = JWTManager.create_refresh_token(
            data={"user_id": user.id, "customer_id": user.customer_id}
        )
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
        }
        
    except (InvalidCredentialsError, AccountLockedError) as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except AuthError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/logout")
def logout_user(current_user = Depends(get_current_user)):
    """Logout user (client should remove tokens)"""
    # TODO: Implement token blacklisting
    # 1. Add the tokens to a blacklist
    # 2. Remove refresh tokens from database
    # For now, we rely on client-side token removal
    return {"message": "Successfully logged out"}

@router.post("/refresh", response_model=Token)
def refresh_access_token(refresh_token: str, db: Session = Depends(get_db)):
    """Refresh access token using refresh token"""
    try:
        payload = JWTManager.verify_token(refresh_token)
        
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        user_id = payload.get("user_id")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        user = UserCRUD.get_user(db, user_id=user_id)
        if user is None or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )
        
        new_access_token = JWTManager.create_access_token(
            data={"user_id": user.id, "email": user.email, "role": user.role}
        )
        
        return {
            "access_token": new_access_token,
            "refresh_token": refresh_token, 
            "token_type": "bearer",
            "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
        }
        
    except AuthError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

@router.get("/me", response_model=UserResponse)
def get_current_user_profile(current_user = Depends(get_current_user)):
    """Get current user profile information"""
    return current_user

@router.put("/profile", response_model=UserResponse)
def update_profile(
    profile_update: UserUpdate,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update current user's profile information"""
    db_user = UserCRUD.update_user(db, user_id=current_user.id, user_update=profile_update)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

@router.post("/change-password")
def change_password(
    old_password: str,
    new_password: str,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Change user password"""
    try:
        if not UserCRUD.verify_password(db, current_user.id, old_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid current password"
            )
        
        success = UserCRUD.update_password(db, current_user.id, new_password)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update password"
            )
        
        return {"message": "Password updated successfully"}
        
    except WeakPasswordError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except AuthError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )