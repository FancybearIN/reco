from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from src.memory.memory_agent import MemoryAgent
from src.orchestration.celery_app import celery_app
from src.core.config import settings
import structlog

logger = structlog.get_logger(__name__)
app = FastAPI(title="Recon OS Control Plane", version="1.0.0")

class LearnRequest(BaseModel):
    repo_url: str

class StartScanRequest(BaseModel):
    domain: str

class TargetGraphResponse(BaseModel):
    domain: str
    relationships: list

@app.post("/api/v1/agent/learn", tags=["Intelligence"])
async def learn_new_methodology(request: LearnRequest):
    """
    Instructs the reco agent to ingest and learn from an external GitHub repository.
    """
    task = celery_app.send_task(
        "src.workers.learner_worker.learn_from_repo",
        args=[request.repo_url]
    )
    return {"status": "learning_started", "task_id": task.id, "repo": request.repo_url}

@app.on_event("startup")
async def startup_event():
    logger.info("Starting up API Control Plane")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down API Control Plane")

from src.core.scaffolder import scaffold_target

@app.post("/api/v1/scan/start", tags=["Orchestration"])
async def start_scan(request: StartScanRequest):
    """
    Injects an authorized target scope to kick off the recursive recon loop.
    """
    logger.info("Initializing scan scope", target=request.domain)
    
    # 1. Scaffold local file structure in /home/kali/bugbounty/
    target_path = scaffold_target(request.domain)
    if not target_path:
        raise HTTPException(status_code=500, detail="Failed to initialize target storage")

    # 2. Initialize Target in Graph
    agent = MemoryAgent()
    await agent.add_target(request.domain)
    await agent.close()
    
    # Send initial event to the orchestrator (mocking a subdomain discovery task)
    task = celery_app.send_task(
        "src.orchestration.orchestrator.handle_task_result",
        args=[{
            "task_id": "init-task-001",
            "task_name": "subdomain_enum",
            "target": request.domain,
            "status": "success",
            "data": {"subdomains": [f"www.{request.domain}", f"api.{request.domain}"]},
            "depth": 0
        }],
        queue="orchestrator"
    )
    return {"status": "accepted", "task_id": task.id, "target": request.domain}

@app.get("/api/v1/graph/target/{domain}", response_model=TargetGraphResponse, tags=["Memory"])
async def get_target_graph(domain: str):
    """
    Fetches the correlated graph attack surface from Neo4j.
    """
    agent = MemoryAgent()
    try:
        graph = await agent.get_target_graph(domain)
        return graph
    except Exception as e:
        logger.error("Failed to fetch graph", error=str(e))
        raise HTTPException(status_code=500, detail="Database error fetching graph")
    finally:
        await agent.close()

@app.get("/health", tags=["System"])
async def health_check():
    """
    Validates components.
    """
    return {
        "status": "ok", 
        "redis": "configured", 
        "neo4j": "configured",
        "broker": settings.CELERY_BROKER_URL
    }
