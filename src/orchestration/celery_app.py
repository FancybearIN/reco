from celery import Celery
from src.core.config import settings

celery_app = Celery(
    "reco",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "src.workers.browser_worker",
        "src.workers.recon_worker",
        "src.workers.learner_worker",
        "src.orchestration.orchestrator"
    ]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    
    # --- CONCURRENCY CONTROL (OMEN 16GB OPTIMIZED) ---
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    
    # Strict Queue Routing
    task_routes={
        "src.workers.browser_worker.*": {"queue": "browser"},
        "src.workers.recon_worker.*": {"queue": "recon"},
        "src.orchestration.orchestrator.*": {"queue": "orchestrator"},
    },
)

# Individual Worker settings are handled via CLI flags (-c)
# Browser: -c 1
# Recon: -c 2
# Orchestrator: -c 2
