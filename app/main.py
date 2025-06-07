from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.core.database import create_tables
from app.api.routes import router
from app.models import User, Achievement
import os
import logging

logger = logging.getLogger("uvicorn.error")

app = FastAPI(
    title="Mental Health FastAPI App",
    description="A mental health application with user authentication and achievements",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files if directory exists
STATIC_DIR = "app/static"  # or "static" if static is in root

if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
else:
    logger.warning(f"Static directory '{STATIC_DIR}' not found. Static files will not be served.")

# Create tables after all models are imported!
create_tables()

# Routers
app.include_router(router, prefix="/api/v1", tags=["api"])

@app.get("/")
def read_root():
    return {
        "message": "Welcome to Mental Health FastAPI App",
        "docs": "/docs",
        "redoc": "/redoc"
    }

@app.get("/health")
def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
