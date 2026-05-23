#!/bin/bash
python -m src.core.init_db
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
