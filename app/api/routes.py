from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from fastapi.responses import FileResponse, JSONResponse
from app.workers.tasks import validate_csv_task, celery
import shutil
import uuid
import os
from typing import Optional

router = APIRouter()

@router.post("/upload/")
async def upload_file(
    file: UploadFile = File(...),
    detailed: bool = Query(False, description="Include detailed validation results")
):
    """
    Upload CSV file for email validation
    
    Args:
        file: CSV file containing email addresses
        detailed: Whether to include detailed validation results
    """
    # Validate file type
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are supported")
    
    # Validate file size (max 10MB)
    if file.size and file.size > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File size must be less than 10MB")
    
    job_id = str(uuid.uuid4())
    file_location = f"/tmp/{job_id}.csv"

    try:
        with open(file_location, "wb") as f:
            shutil.copyfileobj(file.file, f)
        
        # Start validation task
        task = validate_csv_task.delay(file_location, job_id, detailed)
        
        return {
            "job_id": job_id,
            "task_id": task.id,
            "status": "processing",
            "message": "File uploaded successfully. Validation in progress."
        }
    except Exception as e:
        # Clean up file on error
        if os.path.exists(file_location):
            os.remove(file_location)
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

@router.get("/results/{job_id}")
async def get_results(job_id: str):
    """
    Get validation results for a job
    """
    # Check for both simple and detailed results
    simple_file = f"/tmp/{job_id}_validated.csv"
    detailed_file = f"/tmp/{job_id}_detailed_validated.csv"
    
    if os.path.exists(detailed_file):
        return FileResponse(
            path=detailed_file, 
            filename=f"{job_id}_detailed_validated.csv", 
            media_type='text/csv'
        )
    elif os.path.exists(simple_file):
        return FileResponse(
            path=simple_file, 
            filename=f"{job_id}_validated.csv", 
            media_type='text/csv'
        )
    else:
        raise HTTPException(status_code=404, detail="Results not found. Job may still be processing.")

@router.get("/status/{task_id}")
async def get_task_status(task_id: str):
    """
    Get the status of a validation task
    """
    task = celery.AsyncResult(task_id)
    
    if task.state == 'PENDING':
        response = {
            'state': task.state,
            'status': 'Task is pending...'
        }
    elif task.state == 'PROGRESS':
        response = {
            'state': task.state,
            'status': task.info.get('status', ''),
            'current': task.info.get('current', 0),
            'total': task.info.get('total', 0),
            'progress': f"{task.info.get('current', 0)}/{task.info.get('total', 0)}"
        }
    elif task.state == 'SUCCESS':
        response = {
            'state': task.state,
            'status': 'Task completed successfully',
            'result': task.info
        }
    else:
        response = {
            'state': task.state,
            'status': str(task.info)
        }
    
    return response

@router.get("/health")
async def health_check():
    """
    Health check endpoint
    """
    return {"status": "healthy", "service": "email_validator"}
