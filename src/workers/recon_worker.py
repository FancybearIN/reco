import json
from src.orchestration.celery_app import celery_app
from src.core.security import SecurityGuard
import structlog

logger = structlog.get_logger(__name__)

@celery_app.task(name="src.workers.recon_worker.run_subdomain_enum", bind=True)
def run_subdomain_enum(self, domain: str, depth: int = 0):
    """
    Native Recon Worker: Runs subfinder directly on Kali.
    """
    logger.info("Starting native subdomain enumeration", target=domain)
    
    # Use SecurityGuard to run native subfinder
    output = SecurityGuard.run_tool("subfinder", ["-d", domain, "-silent", "-j"])
    
    subdomains = []
    if output:
        for line in output.splitlines():
            try:
                data = json.loads(line)
                subdomains.append(data.get("host"))
            except:
                continue

    result_payload = {
        "task_id": self.request.id,
        "task_name": "subdomain_enum",
        "target": domain,
        "status": "success",
        "data": {"subdomains": list(set(subdomains))},
        "depth": depth
    }
    
    # Route back to orchestrator
    celery_app.send_task(
        "src.orchestration.orchestrator.handle_task_result",
        args=[result_payload],
        queue="orchestrator"
    )
    
    return result_payload
