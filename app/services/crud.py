from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta, timezone
from app.models.users import User
from app.schemas.schemas import UserCreate, UserUpdate, UserLogin
from app.api.authentication import (
    PasswordHasher, PasswordValidator, SecurityValidator, 
    AuthError, InvalidCredentialsError, WeakPasswordError, AccountLockedError
)

class UserCRUD:
    @staticmethod
    def get_user(db: Session, user_id: int) -> Optional[User]:
        return db.query(User).filter(User.id == user_id).first()
    
    @staticmethod
    def get_user_by_username(db: Session, username: str) -> Optional[User]:
        return db.query(User).filter(User.username == username).first()
    
    @staticmethod
    def get_user_by_email(db: Session, email: str) -> Optional[User]:
        return db.query(User).filter(User.email == email).first()
    
    @staticmethod
    def get_users(db: Session, skip: int = 0, limit: int = 100) -> List[User]:
        return db.query(User).offset(skip).limit(limit).all()
    
    @staticmethod
    def create_user(db: Session, user: UserCreate) -> User:
        username_valid, username_msg = SecurityValidator.validate_username(user.username)
        if not username_valid:
            raise AuthError(username_msg)
        
        if user.full_name:
            name_valid, name_msg = SecurityValidator.validate_full_name(user.full_name)
            if not name_valid:
                raise AuthError(name_msg)
        
        password_valid, password_msg = PasswordValidator.validate_password(user.password)
        if not password_valid:
            raise WeakPasswordError(password_msg)
        
        password_hash, salt = PasswordHasher.hash_password(user.password)
        
        db_user = User(
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            password_hash=password_hash,
            salt=salt,
            is_active=True,
            is_verified=False,
            failed_login_attempts=0
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
    
    @staticmethod
    def update_user(db: Session, user_id: int, user_update: UserUpdate) -> Optional[User]:
        db_user = db.query(User).filter(User.id == user_id).first()
        if db_user:
            update_data = user_update.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(db_user, field, value)
            db.commit()
            db.refresh(db_user)
        return db_user
    
    @staticmethod
    def delete_user(db: Session, user_id: int) -> bool:
        db_user = db.query(User).filter(User.id == user_id).first()
        if db_user:
            db.delete(db_user)
            db.commit()
            return True
        return False
    
    @staticmethod
    def authenticate_user(db: Session, email: str, password: str) -> User:
        """Authenticate user with email and password"""
        user = UserCRUD.get_user_by_email(db, email)
        if not user:
            raise InvalidCredentialsError("Invalid email or password")
        
        if SecurityValidator.is_account_locked(user):
            raise AccountLockedError("Account is temporarily locked due to multiple failed login attempts")
        
        if not user.is_active:
            raise AuthError("Account is inactive")
        
        if not PasswordHasher.verify_password(password, user.password_hash, user.salt):
            UserCRUD.update_failed_login_attempt(db, user.id)
            raise InvalidCredentialsError("Invalid email or password")
        
        UserCRUD.update_successful_login(db, user.id)
        return user
    
    @staticmethod
    def update_failed_login_attempt(db: Session, user_id: int):
        """Update failed login attempts and potentially lock account"""
        db_user = db.query(User).filter(User.id == user_id).first()
        if db_user:
            db_user.failed_login_attempts += 1
            
            if SecurityValidator.should_lock_account(db_user.failed_login_attempts):
                db_user.locked_until = datetime.now(timezone.utc) + timedelta(minutes=30)
            
            db.commit()
    
    @staticmethod
    def update_successful_login(db: Session, user_id: int):
        """Update user after successful login"""
        db_user = db.query(User).filter(User.id == user_id).first()
        if db_user:
            db_user.last_login = datetime.now(timezone.utc)
            db_user.failed_login_attempts = 0
            db_user.locked_until = None
            db.commit()
    
    @staticmethod
    def update_password(db: Session, user_id: int, new_password: str) -> bool:
        """Update user password with new hash"""
        password_valid, password_msg = PasswordValidator.validate_password(new_password)
        if not password_valid:
            raise WeakPasswordError(password_msg)
        
        db_user = db.query(User).filter(User.id == user_id).first()
        if db_user:
            password_hash, salt = PasswordHasher.hash_password(new_password)
            db_user.password_hash = password_hash
            db_user.salt = salt
            db.commit()
            return True
        return False

