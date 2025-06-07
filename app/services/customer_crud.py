from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Optional
from datetime import datetime, timedelta

# Import models using your existing structure
from app.models.customer import Customer  # This will be the new file
from app.models import User  # Using your existing import pattern
from app.schemas.customer import CustomerCreate, CustomerUpdate
from app.schemas.schemas import UserCreate
from app.services.crud import UserCRUD
from app.api.authentication import (
    PasswordHasher, PasswordValidator, SecurityValidator, 
    WeakPasswordError, InvalidCredentialsError, AccountLockedError
)
from datetime import timezone

class CustomerCRUD:
    
    @staticmethod
    def create_customer_with_admin(db: Session, customer_data: CustomerCreate) -> tuple[Customer, User]:
        """Create a new customer and their admin user in a transaction"""
        try:
            # Validate admin password
            is_valid, error_msg = PasswordValidator.validate(customer_data.admin_password)
            if not is_valid:
                raise ValueError(f"Invalid admin password: {error_msg}")
            
            # Check if company already exists
            existing_customer = CustomerCRUD.get_customer_by_email(db, customer_data.company_email)
            if existing_customer:
                raise ValueError("Company email already registered")
            
            existing_customer = CustomerCRUD.get_customer_by_name(db, customer_data.company_name)
            if existing_customer:
                raise ValueError("Company name already registered")
            
            # Determine max users based on subscription plan
            max_users_map = {
                'basic': 50,
                'premium': 200,
                'enterprise': 1000
            }
            
            # Create customer
            customer = Customer(
                company_name=customer_data.company_name,
                company_email=customer_data.company_email,
                company_phone=customer_data.company_phone,
                company_address=customer_data.company_address,
                subscription_plan=customer_data.subscription_plan,
                max_users=max_users_map.get(customer_data.subscription_plan, 50),
                admin_first_name=customer_data.admin_first_name,
                admin_last_name=customer_data.admin_last_name,
                admin_email=customer_data.admin_email,
                admin_phone=customer_data.admin_phone,
                billing_email=customer_data.admin_email,  # Default to admin email
                subscription_expires_at=datetime.utcnow() + timedelta(days=30)  # 30-day trial
            )
            
            db.add(customer)
            db.flush()  # Get the customer ID without committing
            
            # Create admin user for the customer
            admin_username = f"admin_{customer.company_name.lower().replace(' ', '_')}"
            admin_full_name = f"{customer_data.admin_first_name} {customer_data.admin_last_name}"
            
            admin_user_data = UserCreate(
                username=admin_username,
                email=customer_data.admin_email,
                password=customer_data.admin_password,
                full_name=admin_full_name,
                role="admin"
            )
            
            # Create the admin user with customer_id
            admin_user = UserCRUD.create_user_for_customer(db, admin_user_data, customer.id)
            
            db.commit()
            db.refresh(customer)
            db.refresh(admin_user)
            
            return customer, admin_user
            
        except Exception as e:
            db.rollback()
            raise e
    
    @staticmethod
    def get_customer(db: Session, customer_id: int) -> Optional[Customer]:
        """Get customer by ID"""
        return db.query(Customer).filter(Customer.id == customer_id).first()
    
    @staticmethod
    def get_customer_by_email(db: Session, email: str) -> Optional[Customer]:
        """Get customer by company email"""
        return db.query(Customer).filter(Customer.company_email == email).first()
    
    @staticmethod
    def get_customer_by_name(db: Session, company_name: str) -> Optional[Customer]:
        """Get customer by company name"""
        return db.query(Customer).filter(Customer.company_name == company_name).first()
    
    @staticmethod
    def get_customers(db: Session, skip: int = 0, limit: int = 100) -> List[Customer]:
        """Get list of customers"""
        return db.query(Customer).offset(skip).limit(limit).all()
    
    @staticmethod
    def update_customer(db: Session, customer_id: int, customer_update: CustomerUpdate) -> Optional[Customer]:
        """Update customer information"""
        customer = CustomerCRUD.get_customer(db, customer_id)
        if not customer:
            return None
        
        update_data = customer_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(customer, field, value)
        
        customer.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(customer)
        return customer
    
    @staticmethod
    def deactivate_customer(db: Session, customer_id: int) -> bool:
        """Deactivate customer and all their users"""
        customer = CustomerCRUD.get_customer(db, customer_id)
        if not customer:
            return False
        
        try:
            customer.is_active = False
            customer.updated_at = datetime.utcnow()
            
            db.query(User).filter(User.customer_id == customer_id).update({
                User.is_active: False
            })
            
            db.commit()
            return True
        except Exception:
            db.rollback()
            return False
    
    @staticmethod
    def get_customer_stats(db: Session, customer_id: int) -> dict:
        """Get statistics for a specific customer"""
        customer = CustomerCRUD.get_customer(db, customer_id)
        if not customer:
            return {}
        
        total_users = db.query(User).filter(User.customer_id == customer_id).count()
        active_users = db.query(User).filter(
            and_(User.customer_id == customer_id, User.is_active == True)
        ).count()
        admin_users = db.query(User).filter(
            and_(User.customer_id == customer_id, User.role == "admin")
        ).count()
        
        return {
            "customer_id": customer_id,
            "company_name": customer.company_name,
            "total_users": total_users,
            "active_users": active_users,
            "inactive_users": total_users - active_users,
            "admin_users": admin_users,
            "max_users": customer.max_users,
            "users_remaining": customer.max_users - total_users,
            "subscription_plan": customer.subscription_plan,
            "subscription_active": customer.is_subscription_active
        }