import asyncio
from celery import Celery
from apps.backend.app.services.worker_manager import WorkerManager

# Initialize Celery app (loads configs from env/Redis)
celery_app = Celery(
    "webguardian",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0"
)

# Optional config overrides
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

@celery_app.task(name="tasks.run_collector")
def run_collector_task(run_id: str):
    """
    Production Celery wrapper task executing the async collector pipeline.
    """
    loop = asyncio.get_event_loop()
    if loop.is_running():
        import nest_asyncio
        nest_asyncio.apply()
        return asyncio.run(WorkerManager.process_collector_run(run_id))
    else:
        return asyncio.run(WorkerManager.process_collector_run(run_id))
