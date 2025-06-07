from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
import shutil
import os
import tempfile
from app.core.database import get_db
from app.services.archievements_import import parse_excel, bulk_insert_achievements
from app.api.routes import get_current_user  # or wherever your auth dependency is

router = APIRouter()

# ------------------
# Upload Endpoint
# ------------------
@router.post("/upload")
async def upload_excel(
    background_tasks: BackgroundTasks,  # Fixed: Removed Depends()
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Invalid file type")

    # Create temp directory if it doesn't exist (cross-platform)
    temp_dir = tempfile.gettempdir()
    file_path = os.path.join(temp_dir, file.filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    def process_file():
        data = parse_excel(file_path)
        result = bulk_insert_achievements(data, db)
        print(result)
        os.remove(file_path)

    background_tasks.add_task(process_file)
    return {"message": "File is being processed", "filename": file.filename}

# ------------------
# Preview Endpoint
# ------------------
@router.post("/preview")
async def preview_excel(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)  # Changed from get_current_admin_user
):
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Invalid file type")

    temp_dir = tempfile.gettempdir()
    file_path = os.path.join(temp_dir, f"preview_{file.filename}")
    
    with open(file_path, "wb") as f:
        f.write(await file.read())

    data = parse_excel(file_path)
    os.remove(file_path)
    return {"preview": [item.dict() for item in data[:10]]}
