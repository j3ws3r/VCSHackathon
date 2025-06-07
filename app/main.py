from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.core.database import create_tables
from app.api.routes import router as api_router
from app.api.page_routes import router as page_router 
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

STATIC_DIR = "app/static"
if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
else:
    logger.warning(f"Static directory '{STATIC_DIR}' not found. Static files will not be served.")

create_tables()

app.include_router(api_router, prefix="/api/v1", tags=["api"])
app.include_router(page_router, tags=["pages"])

@app.get("/")
def read_root():
    return {
        "message": "Welcome to Mental Health FastAPI App",
        "docs": "/docs",
        "redoc": "/redoc"
    }

@app.get("/create")
def redirect_to_create():
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/api/v1/auth/create")

@app.get("/health")
def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)