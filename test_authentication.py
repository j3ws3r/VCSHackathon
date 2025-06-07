#!/usr/bin/env python3
"""
Test script for authentication.py functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.api.authentication import (
    PasswordValidator, PasswordHasher, JWTManager, SecurityValidator,
    AuthError, InvalidCredentialsError, WeakPasswordError, UserRole
)

def test_password_validation():
    """Test password validation functionality"""
    print("🔐 Testing Password Validation...")
    
    # Test valid password
    valid_password = "StrongPass123!"
    is_valid, message = PasswordValidator.validate(valid_password)
    print(f"  ✅ Valid password: {is_valid} - {message}")
    
    # Test weak passwords
    weak_passwords = [
        ("weak", "Too short"),
        ("nouppercase123!", "No uppercase"),
        ("NOLOWERCASE123!", "No lowercase"),
        ("NoNumbers!", "No numbers"),
        ("NoSpecialChars123", "No special chars"),
        ("aaa111AAA!!!", "Repeated characters")
    ]
    
    for password, description in weak_passwords:
        is_valid, message = PasswordValidator.validate(password)
        print(f"  ❌ {description}: {is_valid} - {message}")

def test_password_hashing():
    """Test password hashing and verification"""
    print("\n🔒 Testing Password Hashing...")
    
    password = "TestPassword123!"
    
    # Hash password
    hashed, salt = PasswordHasher.hash_password(password)
    print(f"  ✅ Password hashed successfully")
    print(f"  Salt: {salt[:10]}...")
    print(f"  Hash: {hashed[:20]}...")
    
    # Verify correct password
    is_correct = PasswordHasher.verify_password(password, hashed, salt)
    print(f"  ✅ Correct password verification: {is_correct}")
    
    # Verify wrong password
    is_wrong = PasswordHasher.verify_password("WrongPassword123!", hashed, salt)
    print(f"  ❌ Wrong password verification: {is_wrong}")

def test_jwt_tokens():
    """Test JWT token creation and verification"""
    print("\n🎟️ Testing JWT Tokens...")
    
    # Test data
    user_data = {
        "user_id": 123,
        "email": "test@example.com",
        "role": "user"
    }
    
    # Create access token
    access_token = JWTManager.create_access_token(user_data)
    print(f"  ✅ Access token created: {access_token[:30]}...")
    
    # Create refresh token
    refresh_token = JWTManager.create_refresh_token({"user_id": 123})
    print(f"  ✅ Refresh token created: {refresh_token[:30]}...")
    
    # Verify access token
    try:
        payload = JWTManager.verify_token(access_token)
        print(f"  ✅ Token verification successful:")
        print(f"    User ID: {payload.get('user_id')}")
        print(f"    Email: {payload.get('email')}")
        print(f"    Role: {payload.get('role')}")
    except AuthError as e:
        print(f"  ❌ Token verification failed: {e}")
    
    # Test invalid token
    try:
        JWTManager.verify_token("invalid.token.here")
        print("  ❌ Invalid token should have failed!")
    except AuthError:
        print("  ✅ Invalid token correctly rejected")

def test_security_validation():
    """Test security validation functions"""
    print("\n🛡️ Testing Security Validation...")
    
    # Test email validation
    valid_emails = ["test@example.com", "user.name@domain.co.uk"]
    invalid_emails = ["invalid-email", "test@", "@domain.com", "test..test@domain.com"]
    
    for email in valid_emails:
        is_valid = SecurityValidator.validate_email(email)
        print(f"  ✅ Valid email '{email}': {is_valid}")
    
    for email in invalid_emails:
        is_valid = SecurityValidator.validate_email(email)
        print(f"  ❌ Invalid email '{email}': {is_valid}")
    
    # Test username validation
    valid_usernames = ["testuser", "user123", "test-user", "test_user"]
    invalid_usernames = ["ab", "a" * 51, "test user", "test@user"]
    
    for username in valid_usernames:
        is_valid, message = SecurityValidator.validate_username(username)
        print(f"  ✅ Valid username '{username}': {is_valid}")
    
    for username in invalid_usernames:
        is_valid, message = SecurityValidator.validate_username(username)
        print(f"  ❌ Invalid username '{username}': {is_valid} - {message}")

def test_user_role():
    """Test UserRole enum"""
    print("\n👤 Testing User Role...")
    print(f"  ✅ Available role: {UserRole.USER.value}")

def main():
    """Run all authentication tests"""
    print("🚀 Testing Authentication System")
    print("=" * 50)
    
    try:
        test_password_validation()
        test_password_hashing()
        test_jwt_tokens()
        test_security_validation()
        test_user_role()
        
        print("\n" + "=" * 50)
        print("🎉 All Authentication Tests Completed Successfully!")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 