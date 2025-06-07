from pydantic import BaseModel, EmailStr, validator
from typing import Optional
from datetime import datetime

class CustomerCreate(BaseModel):
    company_name: str
    company_email: EmailStr
    company_phone: Optional[str] = None
    company_address: Optional[str] = None
    
    admin_first_name: str
    admin_last_name: str
    admin_email: EmailStr
    admin_password: str
    admin_phone: Optional[str] = None
    
    subscription_plan: str = "basic"
    
    @validator('company_name')
    def validate_company_name(cls, v):
        if len(v.strip()) < 2:
            raise ValueError('Company name must be at least 2 characters long')
        return v.strip()
    
    @validator('admin_first_name', 'admin_last_name')
    def validate_names(cls, v):
        if len(v.strip()) < 1:
            raise ValueError('Name fields cannot be empty')
        return v.strip()
    
    @validator('subscription_plan')
    def validate_subscription_plan(cls, v):
        allowed_plans = ['basic', 'premium', 'enterprise']
        if v not in allowed_plans:
            raise ValueError(f'Subscription plan must be one of: {allowed_plans}')
        return v

class CustomerResponse(BaseModel):
    id: int
    company_name: str
    company_email: str
    company_phone: Optional[str]
    company_address: Optional[str]
    subscription_plan: str
    max_users: int
    is_active: bool
    is_verified: bool
    admin_first_name: str
    admin_last_name: str
    admin_email: str
    admin_phone: Optional[str]
    created_at: datetime
    user_count: int
    can_add_users: bool
    is_subscription_active: bool
    
    class Config:
        from_attributes = True

class CustomerUpdate(BaseModel):
    company_name: Optional[str] = None
    company_email: Optional[EmailStr] = None
    company_phone: Optional[str] = None
    company_address: Optional[str] = None
    subscription_plan: Optional[str] = None
    max_users: Optional[int] = None
    is_active: Optional[bool] = None
    billing_email: Optional[EmailStr] = None
    
    @validator('subscription_plan')
    def validate_subscription_plan(cls, v):
        if v is not None:
            allowed_plans = ['basic', 'premium', 'enterprise']
            if v not in allowed_plans:
                raise ValueError(f'Subscription plan must be one of: {allowed_plans}')
        return v

class CustomerRegistrationResponse(BaseModel):
    customer: CustomerResponse
    admin_user: dict
    message: str
    next_steps: list