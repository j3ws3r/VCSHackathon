from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.database import create_tables
from app.api.routes import router
from app.api.achievements import router as achievements_router
from app.services.archievements_import import router as import_router

from app.models import User, Achievement

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

# Create tables after all models are imported!!!!
create_tables()

app.include_router(router, prefix="/api/v1", tags=["api"])
app.include_router(achievements_router, prefix="/api/v1/achievements", tags=["achievements"])
app.include_router(import_router, prefix="/api/v1", tags=["import"])

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