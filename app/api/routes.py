from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from fastapi.responses import FileResponse
from app.workers.tasks import validate_csv_task, celery
import shutil
import uuid
import os
from typing import Optional

router = APIRouter()

UPLOAD_DIR = "/tmp"
OUTPUT_DIR = "./output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

@router.post("/upload/")
async def upload_file(
    file: UploadFile = File(...),
    detailed: bool = Query(False, description="Include detailed validation results")
):
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are supported")

    job_id = str(uuid.uuid4())
    file_location = os.path.join(UPLOAD_DIR, f"{job_id}.csv")

    try:
        with open(file_location, "wb") as f:
            shutil.copyfileobj(file.file, f)

        task = validate_csv_task.delay(file_location, job_id, detailed)

        return {
            "job_id": job_id,
            "task_id": task.id,
            "status": "processing",
            "message": "File uploaded successfully. Validation in progress."
        }
    except Exception as e:
        if os.path.exists(file_location):
            os.remove(file_location)
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

@router.get("/results/{job_id}")
async def get_results(job_id: str):
    """
    Download validated CSV results from the output folder
    """
    simple_file = os.path.join(OUTPUT_DIR, f"{job_id}_validated.csv")
    detailed_file = os.path.join(OUTPUT_DIR, f"{job_id}_detailed_validated.csv")

    if os.path.exists(detailed_file):
        return FileResponse(
            path=detailed_file,
            filename=os.path.basename(detailed_file),
            media_type='text/csv'
        )
    elif os.path.exists(simple_file):
        return FileResponse(
            path=simple_file,
            filename=os.path.basename(simple_file),
            media_type='text/csv'
        )
    else:
        raise HTTPException(status_code=404, detail="Results not found. Job may still be processing.")

@router.get("/status/{task_id}")
async def get_task_status(task_id: str):
    task = celery.AsyncResult(task_id)

    if task.state == 'PENDING':
        return {'state': task.state, 'status': 'Task is pending...'}
    elif task.state == 'PROGRESS':
        return {
            'state': task.state,
            'status': task.info.get('status', ''),
            'current': task.info.get('current', 0),
            'total': task.info.get('total', 0),
            'progress': f"{task.info.get('current', 0)}/{task.info.get('total', 0)}"
        }
    elif task.state == 'SUCCESS':
        return {
            'state': task.state,
            'status': 'Task completed successfully',
            'result': task.info
        }
    else:
        return {'state': task.state, 'status': str(task.info)}

@router.get("/health")
async def health_check():
    return {"status": "healthy", "service": "email_validator"}
