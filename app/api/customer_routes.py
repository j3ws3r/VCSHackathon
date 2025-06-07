"""
Customer registration and management routes
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import traceback

from app.core.database import get_db
from app.schemas.customer import CustomerCreate, CustomerResponse, CustomerRegistrationResponse

# Import with error handling
try:
    from app.services.customer_crud import CustomerCRUD
except ImportError as e:
    print(f"Warning: Could not import CustomerCRUD: {e}")
    CustomerCRUD = None

from app.api.authentication import AuthError, WeakPasswordError

router = APIRouter(prefix="/customers", tags=["Customer Registration"])

@router.post("/register", status_code=status.HTTP_201_CREATED)
def register_customer(customer_data: CustomerCreate, db: Session = Depends(get_db)):
    """
    Register a new customer company with admin user
    """
    try:

        if not customer_data.company_name or len(customer_data.company_name.strip()) < 2:
            raise ValueError("Company name must be at least 2 characters")
        
        if not customer_data.admin_password or len(customer_data.admin_password) < 8:
            raise ValueError("Admin password must be at least 8 characters")
        

        if CustomerCRUD is None:
            raise Exception("CustomerCRUD service not available")

        customer, admin_user = CustomerCRUD.create_customer_with_admin(db, customer_data)

        
        response_data = {
            "customer": {
                "id": customer.id,
                "company_name": customer.company_name,
                "company_email": customer.company_email,
                "company_phone": customer.company_phone,
                "company_address": customer.company_address,
                "subscription_plan": customer.subscription_plan,
                "max_users": customer.max_users,
                "is_active": customer.is_active,
                "is_verified": customer.is_verified,
                "admin_first_name": customer.admin_first_name,
                "admin_last_name": customer.admin_last_name,
                "admin_email": customer.admin_email,
                "admin_phone": customer.admin_phone,
                "created_at": customer.created_at,
                "user_count": customer.user_count,
                "can_add_users": customer.can_add_users,
                "is_subscription_active": customer.is_subscription_active
            },
            "admin_user": {
                "id": admin_user.id,
                "username": admin_user.username,
                "email": admin_user.email,
                "full_name": admin_user.full_name,
                "role": admin_user.role
            },
            "message": "Customer registration successful! Admin account created.",
            "next_steps": [
                "1. Log in with your admin credentials",
                "2. Start adding users to your organization",
                "3. Configure your company settings"
            ]
        }
        

        return response_data
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )

@router.get("/db-check")
def check_database_setup(db: Session = Depends(get_db)):
    """Check if customer table exists and can be accessed"""
    try:
        from app.models.customer import Customer
        
        result = db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='customers'")
        table_exists = result.fetchone() is not None
        
        customers_count = 0
        if table_exists:
            customers_count = db.query(Customer).count()
        
        return {
            "customers_table_exists": table_exists,
            "customers_count": customers_count,
            "database_accessible": True
        }
    except Exception as e:
        return {
            "customers_table_exists": False,
            "error": str(e),
            "database_accessible": False
        }
@router.get("/debug")
def debug_customer_setup():
    """Debug endpoint to check what's available"""
    debug_info = {
        "customer_crud_available": CustomerCRUD is not None,
        "customer_routes_loaded": True
    }
    
    try:
        from app.models.customer import Customer
        debug_info["customer_model_available"] = True
    except ImportError as e:
        debug_info["customer_model_available"] = False
        debug_info["customer_model_error"] = str(e)
    
    try:
        from app.models import User
        debug_info["user_model_available"] = True
    except ImportError as e:
        debug_info["user_model_available"] = False
        debug_info["user_model_error"] = str(e)
    
    try:
        from app.services.crud import UserCRUD
        debug_info["user_crud_available"] = True
    except ImportError as e:
        debug_info["user_crud_available"] = False
        debug_info["user_crud_error"] = str(e)
    
    return debug_info