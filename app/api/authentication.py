import os
import re
import secrets
import logging
import sqlite3
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, Tuple
from contextlib import contextmanager

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, HashingError


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Default database schema
_DEFAULT_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    full_name TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    salt TEXT NOT NULL,
    role TEXT DEFAULT 'patient',
    is_active BOOLEAN DEFAULT 1,
    is_verified BOOLEAN DEFAULT 0,
    created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP NULL,
    failed_login_attempts INTEGER DEFAULT 0,
    locked_until TIMESTAMP NULL
);

CREATE TABLE IF NOT EXISTS security_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    event_type TEXT NOT NULL,
    ip_address TEXT,
    user_agent TEXT,
    details TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id)
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_security_logs_user_id ON security_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_security_logs_timestamp ON security_logs(timestamp);
"""

class UserRole(Enum):
    """User roles for authorization"""
    PATIENT = "patient"
    THERAPIST = "therapist"
    ADMIN = "admin"


class AuthError(Exception):
    """Base exception for authentication errors"""
    pass


class InvalidCredentialsError(AuthError):
    """Raised when login credentials are invalid"""
    pass


class UserExistsError(AuthError):
    """Raised when trying to register an existing user"""
    pass


class WeakPasswordError(AuthError):
    """Raised when password doesn't meet security requirements"""
    pass


@dataclass
class User:
    """User data model"""
    id: Optional[int] = None
    email: str = ""
    full_name: str = ""
    password_hash: str = ""
    salt: str = ""
    role: UserRole = UserRole.PATIENT
    is_active: bool = True
    is_verified: bool = False
    created: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_login: Optional[datetime] = None
    failed_login_attempts: int = 0
    locked_until: Optional[datetime] = None


def _row_to_user(row) -> User:
    """Convert SQLite row to User object"""
    if not row:
        return None
    
    # Parse datetime fields
    created = datetime.fromisoformat(row['created']) if row['created'] else datetime.now(timezone.utc)
    last_login = datetime.fromisoformat(row['last_login']) if row['last_login'] else None
    locked_until = datetime.fromisoformat(row['locked_until']) if row['locked_until'] else None
    
    return User(
        id=row['id'],
        email=row['email'],
        full_name=row['full_name'],
        password_hash=row['password_hash'],
        salt=row['salt'],
        role=UserRole(row['role']),
        is_active=bool(row['is_active']),
        is_verified=bool(row['is_verified']),
        created=created,
        last_login=last_login,
        failed_login_attempts=row['failed_login_attempts'],
        locked_until=locked_until
    )


class PasswordValidator:
    """Validates password strength and security requirements"""

    MIN_LENGTH = 12
    MAX_LENGTH = 128

    @staticmethod
    def validate(password: str) -> Tuple[bool, str]:
        if not (PasswordValidator.MIN_LENGTH <= len(password) <= PasswordValidator.MAX_LENGTH):
            return False, f"Password length must be between {PasswordValidator.MIN_LENGTH} and {PasswordValidator.MAX_LENGTH} characters"

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
            r"(.)\1{2,}",
            r"(012|123|234|345|456|567|678|789|890)",
            r"(abc|bcd|cde|def|efg|fgh|ghi|hij|ijk|jkl|klm|lmn|mno|nop|opq|pqr|qrs|rst|stu|tuv|uvw|vwx|wxy|xyz)",
        ]
        low = password.lower()
        for pat in patterns:
            if re.search(pat, low):
                return False, "Password contains predictable patterns"

        return True, ""


class SecurePasswordHasher:
    """Handles secure password hashing using Argon2id"""

    def __init__(self):
        self.hasher = PasswordHasher(
            time_cost=3,
            memory_cost=65536,
            parallelism=1,
            hash_len=32,
            salt_len=16,
        )

    @staticmethod
    def generate_salt() -> str:
        return secrets.token_hex(16)

    def hash(self, password: str, salt: Optional[str] = None) -> Tuple[str, str]:
        salt = salt or self.generate_salt()
        try:
            hashed = self.hasher.hash(password + salt)
            return hashed, salt
        except HashingError as e:
            logger.error("Hashing failed: %s", e)
            raise AuthError("Password hashing failed")

    def verify(self, password: str, hashed: str, salt: str) -> bool:
        try:
            return self.hasher.verify(hashed, password + salt)
        except VerifyMismatchError:
            return False
        except Exception as e:
            logger.error("Verification error: %s", e)
            return False


class JWTManager:
    """Handles JWT token generation and validation"""

    def __init__(self, secret: Optional[str] = None):
        self.secret = secret or os.environ.get("JWT_SECRET_KEY", secrets.token_urlsafe(32))
        self.alg = "HS256"
        self.access_expires = timedelta(minutes=30)
        self.refresh_expires = timedelta(days=7)

    def create(self, user: User) -> Dict[str, str]:
        now = datetime.now(timezone.utc)
        access_payload = {
            "user_id": user.id,
            "email": user.email,
            "role": user.role.value,
            "type": "access",
            "iat": now,
            "exp": now + self.access_expires,
            "jti": secrets.token_hex(16),
        }
        refresh_payload = {
            "user_id": user.id,
            "type": "refresh",
            "iat": now,
            "exp": now + self.refresh_expires,
            "jti": secrets.token_hex(16),
        }
        return {
            "access_token": jwt.encode(access_payload, self.secret, algorithm=self.alg),
            "refresh_token": jwt.encode(refresh_payload, self.secret, algorithm=self.alg),
            "token_type": "bearer",
            "expires_in": int(self.access_expires.total_seconds()),
        }

    def decode(self, token: str) -> Dict[str, Any]:
        try:
            return jwt.decode(token, self.secret, algorithms=[self.alg])
        except jwt.ExpiredSignatureError:
            raise AuthError("Token expired")
        except jwt.InvalidTokenError:
            raise AuthError("Invalid token")


class DatabaseManager:
    """Handles SQLite operations for user and session storage"""

    def __init__(self, path: str = "auth_system.db"):
        self.path = path
        self._init_db()

    @contextmanager
    def connection(self):
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def _init_db(self):
        schema = os.path.join(os.path.dirname(__file__), "schema.sql")
        with self.connection() as conn:
            conn.executescript(_DEFAULT_SCHEMA)
            conn.commit()

    def create_user(self, user: User) -> int:
        sql = """
        INSERT INTO users (email, full_name, password_hash, salt, role,
                           is_active, is_verified)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        with self.connection() as conn:
            cur = conn.execute(sql, (
                user.email, user.full_name, user.password_hash,
                user.salt, user.role.value, user.is_active, user.is_verified
            ))
            conn.commit()
            return cur.lastrowid

    def get_user_by_email(self, email: str) -> Optional[User]:
        with self.connection() as conn:
            row = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
            return _row_to_user(row) if row else None

    def update_login(self, user: User, success: bool):
        now = datetime.now(timezone.utc).isoformat()
        with self.connection() as conn:
            if success:
                conn.execute(
                    "UPDATE users SET last_login=?, \
                     failed_login_attempts=0, locked_until=NULL WHERE id=?",
                    (now, user.id)
                )
            else:
                conn.execute(
                    "UPDATE users SET failed_login_attempts=failed_login_attempts+1 WHERE id=?",
                    (user.id,)
                )
                conn.execute(
                    "UPDATE users SET locked_until=datetime('now', '+30 minutes') \
                     WHERE id=? AND failed_login_attempts>=5",
                    (user.id,)
                )
            conn.commit()

    def log_event(self, user_id: Optional[int], event: str,
                  ip: Optional[str] = None, agent: Optional[str] = None,
                  details: Optional[str] = None):
        sql = "INSERT INTO security_logs (user_id, event_type, ip_address, user_agent, details) VALUES (?, ?, ?, ?, ?)"
        with self.connection() as conn:
            conn.execute(sql, (user_id, event, ip, agent, details))
            conn.commit()


class AuthenticationSystem:
    """Main class orchestrating registration, login, and token validation"""

    def __init__(self, db_path: str = "auth_system.db"):
        self.db = DatabaseManager(db_path)
        self.hasher = SecurePasswordHasher()
        self.jwt = JWTManager()
        self.validator = PasswordValidator()

    def register(self, email: str, full_name: str, password: str,
                 role: UserRole = UserRole.PATIENT) -> Dict[str, Any]:
        if not re.match(r"^[\w\.-]+@[\w\.-]+\.\w{2,}$", email):
            raise AuthError("Invalid email format")
        if not (2 <= len(full_name.strip()) <= 100):
            raise AuthError("Full name must be 2-100 characters")
        if not re.match(r"^[A-Za-z\s\-'.]+$", full_name):
            raise AuthError("Full name contains invalid characters")

        valid, msg = self.validator.validate(password)
        if not valid:
            raise WeakPasswordError(msg)
        if self.db.get_user_by_email(email):
            raise UserExistsError("Email already registered")

        hashed, salt = self.hasher.hash(password)
        user = User(
            email=email,
            full_name=full_name.strip(),
            password_hash=hashed,
            salt=salt,
            role=role,
        )
        user.id = self.db.create_user(user)
        self.db.log_event(user.id, "USER_REGISTERED", details=f"{email}")
        logger.info("Registered user %s", email)
        return {"user_id": user.id, "message": "Registration successful"}

    def login(self, email: str, password: str,
              ip: Optional[str] = None, agent: Optional[str] = None) -> Dict[str, Any]:
        user = self.db.get_user_by_email(email)
        if not user:
            self.db.log_event(None, "LOGIN_FAILED", ip, agent, f"{email} not found")
            raise InvalidCredentialsError()

        now = datetime.now(timezone.utc)
        if user.locked_until and user.locked_until > now:
            raise AuthError("Account temporarily locked")
        if not user.is_active:
            raise AuthError("Account inactive")

        if not self.hasher.verify(password, user.password_hash, user.salt):
            self.db.update_login(user, False)
            self.db.log_event(user.id, "LOGIN_FAILED", ip, agent, "Wrong password")
            raise InvalidCredentialsError()

        self.db.update_login(user, True)
        self.db.log_event(user.id, "LOGIN_SUCCESS", ip, agent)
        tokens = self.jwt.create(user)
        logger.info("User %s logged in", email)
        return {"user": {"id": user.id, "email": user.email, "role": user.role.value}, **tokens}

    def validate_token(self, token: str) -> Dict[str, Any]:
        return self.jwt.decode(token)


if __name__ == "__main__":
    auth = AuthenticationSystem()
    # Example usage here...
