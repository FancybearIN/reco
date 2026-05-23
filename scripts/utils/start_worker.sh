#!/bin/bash
# Wait for DB to be ready if needed
python -m src.core.init_db
celery -A src.orchestration.celery_app worker --loglevel=info
