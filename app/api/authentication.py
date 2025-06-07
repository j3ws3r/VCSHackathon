import os
import re
import secrets
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, Tuple
from enum import Enum

try:
    from jose import JWTError, jwt
except ImportError:
    import jwt
    from jwt.exceptions import InvalidTokenError as JWTError

from passlib.context import CryptContext

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# JWT Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production-mental-health-app")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

# Password hashing configuration
password_context = CryptContext(
    schemes=["argon2", "bcrypt"],
    deprecated="auto",
    argon2__memory_cost=65536,
    argon2__time_cost=3,
    argon2__parallelism=1,
)

class UserRole(Enum):
    """User roles for authorization"""
    USER = "user"

class AuthError(Exception):
    """Base exception for authentication errors"""
    pass

class InvalidCredentialsError(AuthError):
    """Raised when login credentials are invalid"""
    pass

class WeakPasswordError(AuthError):
    """Raised when password doesn't meet security requirements"""
    pass

class AccountLockedError(AuthError):
    """Raised when account is temporarily locked"""
    pass

class UserExistsError(AuthError):
    """Raised when trying to register an existing user"""
    pass

class PasswordValidator:
    """Validates password strength and security requirements"""

    MIN_LENGTH = 12
    MAX_LENGTH = 128

    @staticmethod
    def validate(password: str) -> Tuple[bool, str]:
        """Validate password meets security requirements"""
        if not password:
            return False, "Password is required"
            
        if not (PasswordValidator.MIN_LENGTH <= len(password) <= PasswordValidator.MAX_LENGTH):
            return False, f"Password must be between {PasswordValidator.MIN_LENGTH} and {PasswordValidator.MAX_LENGTH} characters"

        if not re.search(r"[A-Z]", password):
            return False, "Password must contain at least one uppercase letter"

        if not re.search(r"[a-z]", password):
            return False, "Password must contain at least one lowercase letter"

        if not re.search(r"\d", password):
            return False, "Password must contain at least one digit"

        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
            return False, "Password must contain at least one special character"

        # Common pattern checks
        patterns = [
            (r"(.)\1{2,}", "Password contains repeated characters"),
            (r"(012|123|234|345|456|567|678|789|890)", "Password contains sequential numbers"),
            (r"(abc|bcd|cde|def|efg|fgh|ghi|hij|ijk|jkl|klm|lmn|mno|nop|opq|pqr|qrs|rst|stu|tuv|uvw|vwx|wxy|xyz)", "Password contains sequential letters"),
        ]
        
        password_lower = password.lower()
        for pattern, message in patterns:
            if re.search(pattern, password_lower):
                return False, message

        return True, "Password is valid"

    @staticmethod
    def validate_password(password: str) -> Tuple[bool, str]:
        """Alias for validate method to match existing interface"""
        return PasswordValidator.validate(password)

class PasswordHasher:
    """Handles secure password hashing using Argon2"""

    @staticmethod
    def generate_salt() -> str:
        """Generate cryptographically secure salt"""
        return secrets.token_hex(16)

    @staticmethod
    def hash_password(password: str) -> Tuple[str, str]:
        """Hash password with salt using Argon2"""
        salt = PasswordHasher.generate_salt()
        salted_password = password + salt
        hashed = password_context.hash(salted_password)
        return hashed, salt

    @staticmethod
    def verify_password(password: str, hashed_password: str, salt: str) -> bool:
        """Verify password against hash"""
        try:
            salted_password = password + salt
            return password_context.verify(salted_password, hashed_password)
        except Exception as e:
            logger.error(f"Password verification error: {e}")
            return False

class JWTManager:
    """Handles JWT token generation and validation"""

    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "type": "access",
            "jti": secrets.token_hex(16)
        })
        return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    @staticmethod
    def create_refresh_token(data: dict) -> str:
        """Create JWT refresh token"""
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        to_encode.update({
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "type": "refresh",
            "jti": secrets.token_hex(16)
        })
        return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    @staticmethod
    def verify_token(token: str) -> Dict[str, Any]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except JWTError as e:
            logger.error(f"JWT verification error: {e}")
            raise AuthError("Invalid token")

class SecurityValidator:
    """Additional security validations"""
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    @staticmethod
    def validate_username(username: str) -> Tuple[bool, str]:
        """Validate username requirements"""
        if not username:
            return False, "Username is required"
        if len(username) < 3 or len(username) > 50:
            return False, "Username must be between 3 and 50 characters"
        if not re.match(r'^[a-zA-Z0-9_-]+$', username):
            return False, "Username can only contain letters, numbers, hyphens, and underscores"
        return True, "Username is valid"
    
    @staticmethod
    def validate_full_name(full_name: str) -> Tuple[bool, str]:
        """Validate full name"""
        if not full_name:
            return False, "Full name is required"
        if len(full_name.strip()) < 2 or len(full_name.strip()) > 100:
            return False, "Full name must be between 2 and 100 characters"
        if not re.match(r"^[a-zA-Z\s\-'.]+$", full_name.strip()):
            return False, "Full name contains invalid characters"
        return True, "Full name is valid"
    
    @staticmethod
    def is_account_locked(user) -> bool:
        """Check if user account is locked"""
        if hasattr(user, 'locked_until') and user.locked_until and user.locked_until > datetime.now(timezone.utc):
            return True
        return False
    
    @staticmethod
    def should_lock_account(failed_attempts: int) -> bool:
        """Determine if account should be locked after failed attempts"""
        return failed_attempts >= 5

# For backwards compatibility, create instances
password_validator = PasswordValidator()
password_hasher = PasswordHasher()
jwt_manager = JWTManager()
security_validator = SecurityValidator()
