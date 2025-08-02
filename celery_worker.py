from app.workers.tasks import celery

celery.worker_main()
