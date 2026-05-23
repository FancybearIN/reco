import asyncio
from typing import Dict, Any, List
from src.orchestration.celery_app import celery_app
from src.orchestration.schemas import TaskResult
from src.memory.memory_agent import MemoryAgent
import structlog

logger = structlog.get_logger(__name__)
MAX_RECURSION_DEPTH = 5

class Orchestrator:
    """
    The Reasoning Layer / Orchestrator.
    Evaluates findings recursively and routes follow-up tasks safely.
    """
    def __init__(self):
        self.memory = MemoryAgent()

    async def evaluate_and_route(self, result: TaskResult):
        if result.depth >= MAX_RECURSION_DEPTH:
            logger.warning("Max recursion depth reached. Stopping expansion.", target=result.target)
            return

        logger.info("Evaluating task result", task_name=result.task_name, target=result.target, depth=result.depth)
        
        # 1. Enrich with historical context
        context = await self.memory.get_historical_context(result.target)
        logger.info("Retrieved historical context", target=result.target, context=context)
        
        # 2. Update Graph Memory
        await self._update_graph(result)

        # 3. Classify and route (The "Reasoning" step)
        new_tasks = self._determine_next_tasks(result)
        
        # 4. Enqueue new tasks safely
        for task_def in new_tasks:
            self._dispatch_task(task_def)
            
        await self.memory.close()

    async def _update_graph(self, result: TaskResult):
        # Specific logic based on task_name to build relationships
        if result.task_name == "subdomain_enum":
            for sub in result.data.get("subdomains", []):
                await self.memory.add_subdomain(result.target, sub)
        elif result.task_name == "browser_verify":
            await self.memory.add_finding(result.target, result.data)
            # Add technology relationships based on browser hints
            for tech in result.data.get("technologies", []):
                await self.memory.add_technology(result.target, tech)

    def _determine_next_tasks(self, result: TaskResult) -> List[Dict[str, Any]]:
        """
        Determines the follow-up tasks based on recursive intelligence rules.
        """
        tasks = []
        if result.task_name == "subdomain_enum":
            for sub in result.data.get("subdomains", []):
                # Trigger HTTP verification for each discovered subdomain
                tasks.append({
                    "name": "src.workers.browser_worker.verify_endpoint",
                    "args": [f"https://{sub}"],
                    "kwargs": {"depth": result.depth + 1},
                    "queue": "browser"
                })
        
        elif result.task_name == "browser_verify":
            # Example heuristic: if a login panel is detected, we could route to an auth-worker
            if result.data.get("has_login"):
                logger.info("Login form detected! Would route to auth inspection...", target=result.target)
                
            if result.data.get("graphql_detected"):
                logger.info("GraphQL detected! Would route to introspection worker...", target=result.target)

        return tasks

    def _dispatch_task(self, task_def: Dict[str, Any]):
        celery_app.send_task(
            task_def["name"],
            args=task_def.get("args", []),
            kwargs=task_def.get("kwargs", {}),
            queue=task_def.get("queue", "default")
        )
        logger.info("Dispatched new recursive task", next_task=task_def["name"])

@celery_app.task(name="src.orchestration.orchestrator.handle_task_result", bind=True, max_retries=3)
def handle_task_result(self, result_dict: Dict[str, Any]):
    """
    Celery task that acts as the entrypoint for the async orchestrator loop.
    Workers call this task upon successful completion.
    """
    try:
        result = TaskResult(**result_dict)
        orchestrator = Orchestrator()
        
        # Safely run async orchestrator inside Celery's sync worker
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.ensure_future(orchestrator.evaluate_and_route(result))
            else:
                loop.run_until_complete(orchestrator.evaluate_and_route(result))
        except RuntimeError:
            asyncio.run(orchestrator.evaluate_and_route(result))
            
    except Exception as exc:
        logger.error("Failed to process orchestration event", error=str(exc))
        raise self.retry(exc=exc, countdown=5)
