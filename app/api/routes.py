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

from fastapi import HTTPException
import logging

logger = logging.getLogger(__name__)

@router.get("/status/{task_id}")
async def get_task_status(task_id: str):
    """
    Get the status of a validation task
    """
    try:
        # Validate task_id format (basic UUID check)
        if not task_id or len(task_id) < 10:
            raise HTTPException(status_code=400, detail="Invalid task ID format")
        
        task = celery.AsyncResult(task_id)
        
        # Log the task state for debugging
        logger.info(f"Task {task_id} state: {task.state}")
        
        if task.state == 'PENDING':
            # Check if task actually exists or is truly pending
            response = {
                'task_id': task_id,
                'state': task.state,
                'status': 'Task is pending or does not exist',
                'current': 0,
                'total': 0
            }
        elif task.state == 'PROGRESS':
            # Safely get info with defaults
            info = task.info or {}
            response = {
                'task_id': task_id,
                'state': task.state,
                'status': info.get('status', 'In progress...'),
                'current': info.get('current', 0),
                'total': info.get('total', 0),
                'progress': f"{info.get('current', 0)}/{info.get('total', 0)}",
                'percentage': round((info.get('current', 0) / max(info.get('total', 1), 1)) * 100, 2)
            }
        elif task.state == 'SUCCESS':
            response = {
                'task_id': task_id,
                'state': task.state,
                'status': 'Task completed successfully',
                'result': task.result,  # Use task.result instead of task.info for SUCCESS
                'current': task.info.get('total', 0) if task.info else 0,
                'total': task.info.get('total', 0) if task.info else 0
            }
        elif task.state == 'FAILURE':
            response = {
                'task_id': task_id,
                'state': task.state,
                'status': 'Task failed',
                'error': str(task.info) if task.info else 'Unknown error',
                'traceback': task.traceback if hasattr(task, 'traceback') else None
            }
        elif task.state == 'RETRY':
            response = {
                'task_id': task_id,
                'state': task.state,
                'status': 'Task is being retried',
                'error': str(task.info) if task.info else 'Retrying...'
            }
        elif task.state == 'REVOKED':
            response = {
                'task_id': task_id,
                'state': task.state,
                'status': 'Task was cancelled'
            }
        else:
            # Handle any other states
            response = {
                'task_id': task_id,
                'state': task.state,
                'status': str(task.info) if task.info else f'Unknown state: {task.state}',
                'info': task.info
            }
        
        return response
        
    except Exception as e:
        logger.error(f"Error checking task status for {task_id}: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Error retrieving task status: {str(e)}"
        )


# Optional: Add a health check endpoint for Celery connection
@router.get("/celery-health")
async def celery_health():
    """
    Check if Celery is properly connected
    """
    try:
        # Try to inspect active tasks
        inspect = celery.control.inspect()
        stats = inspect.stats()
        
        if stats:
            return {
                "status": "healthy",
                "workers": len(stats),
                "worker_nodes": list(stats.keys()) if stats else []
            }
        else:
            return {
                "status": "no_workers",
                "message": "Celery is running but no workers are active"
            }
    except Exception as e:
        logger.error(f"Celery health check failed: {str(e)}")
        raise HTTPException(
            status_code=503,
            detail=f"Celery connection error: {str(e)}"
        )

@router.get("/health")
async def health_check():
    return {"status": "healthy", "service": "email_validator"}
