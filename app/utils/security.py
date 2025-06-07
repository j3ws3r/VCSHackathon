"""
Security utility functions that can be used across the application.
These are helper functions that don't belong to specific classes.
"""

import re
import secrets
import string
from typing import Optional
from datetime import datetime, timezone

def generate_secure_token(length: int = 32) -> str:
    """Generate a cryptographically secure random token"""
    return secrets.token_urlsafe(length)

def generate_random_password(length: int = 12) -> str:
    """Generate a random password with mixed characters"""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    password = ''.join(secrets.choice(alphabet) for _ in range(length))
    return password

def sanitize_input(input_string: str) -> str:
    """Basic input sanitization - remove potentially harmful characters"""
    if not input_string:
        return ""
    
    input_string = re.sub(r'<[^>]*>', '', input_string)
    
    dangerous_patterns = [
        r'(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION)\b)',
        r'(--|#|/\*|\*/)',
        r'(\bOR\b.*=.*\bOR\b)',
        r'(\bAND\b.*=.*\bAND\b)'
    ]
    
    for pattern in dangerous_patterns:
        input_string = re.sub(pattern, '', input_string, flags=re.IGNORECASE)
    
    return input_string.strip()

def mask_email(email: str) -> str:
    """Mask email address for logging/display purposes"""
    if not email or '@' not in email:
        return "invalid_email"
    
    local, domain = email.split('@', 1)
    if len(local) <= 2:
        masked_local = '*' * len(local)
    else:
        masked_local = local[0] + '*' * (len(local) - 2) + local[-1]
    
    return f"{masked_local}@{domain}"

def is_valid_uuid(uuid_string: str) -> bool:
    """Check if a string is a valid UUID"""
    uuid_pattern = re.compile(
        r'^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$',
        re.IGNORECASE
    )
    return bool(uuid_pattern.match(uuid_string))

def calculate_password_strength(password: str) -> dict:
    """Calculate password strength score and provide feedback"""
    score = 0
    feedback = []
    
    if len(password) >= 8:
        score += 1
    else:
        feedback.append("Use at least 8 characters")
    
    if re.search(r'[a-z]', password):
        score += 1
    else:
        feedback.append("Include lowercase letters")
    
    if re.search(r'[A-Z]', password):
        score += 1
    else:
        feedback.append("Include uppercase letters")
    
    if re.search(r'\d', password):
        score += 1
    else:
        feedback.append("Include numbers")
    
    if re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        score += 1
    else:
        feedback.append("Include special characters")
    
    strength_levels = {
        0: "Very Weak",
        1: "Weak",
        2: "Fair",
        3: "Good",
        4: "Strong",
        5: "Very Strong"
    }
    
    return {
        "score": score,
        "strength": strength_levels.get(score, "Unknown"),
        "feedback": feedback
    }

def is_rate_limited(last_attempt: Optional[datetime], min_interval_seconds: int = 60) -> bool:
    """Check if an action is rate limited based on last attempt time"""
    if last_attempt is None:
        return False
    
    time_diff = datetime.now(timezone.utc) - last_attempt
    return time_diff.total_seconds() < min_interval_seconds

def get_client_ip(request) -> str:
    """Extract client IP address from request, considering proxies"""
    forwarded_ips = request.headers.get("X-Forwarded-For")
    if forwarded_ips:
        return forwarded_ips.split(",")[0].strip()
    
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    return request.client.host if hasattr(request, 'client') else "unknown"

def normalize_phone_number(phone: str) -> Optional[str]:
    """Normalize phone number format"""
    if not phone:
        return None
    
    digits_only = re.sub(r'\D', '', phone)
    
    if len(digits_only) < 10 or len(digits_only) > 15:
        return None
    
    return digits_only