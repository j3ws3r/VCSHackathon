"""
Main API router that combines all route modules
"""

from fastapi import APIRouter

router = APIRouter()

try:
    from app.api.customer_routes import router as customer_router
    router.include_router(customer_router)
    print("Loaded customer_routes")
except ImportError as e:
    print(f"Warning: Could not import customer_routes: {e}")

try:
    from app.api.auth_routes import router as auth_router
    router.include_router(auth_router)
    print("Loaded auth_routes")
except ImportError as e:
    print(f"Warning: Could not import auth_routes: {e}")

try:
    from app.api.user_routes import router as user_router
    router.include_router(user_router)
    print("Loaded user_routes")
except ImportError as e:
    print(f"Warning: Could not import user_routes: {e}")

try:
    from app.api.admin_routes import router as admin_router
    router.include_router(admin_router)
    print("Loaded admin_routes")
except ImportError as e:
    print(f"Warning: Could not import admin_routes: {e}")

@router.get("/health", tags=["System"])
def health_check():
    """API health check endpoint"""
    return {
        "status": "healthy",
        "message": "Mental Health API is running",
        "version": "2.0.0"
    }