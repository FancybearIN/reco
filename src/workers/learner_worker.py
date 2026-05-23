import os
import subprocess
from typing import Dict, Any
from src.orchestration.celery_app import celery_app
from src.memory.memory_agent import MemoryAgent
import structlog

logger = structlog.get_logger(__name__)

class MethodologyLearner:
    """
    The Learning Engine for reco agent.
    Clones external repos, analyzes their methodology, and stores them in Vector Memory.
    """
    def __init__(self):
        self.memory = MemoryAgent()
        self.learning_dir = "/home/kali/reco/knowledge_base"
        os.makedirs(self.learning_dir, exist_ok=True)

    async def ingest_repository(self, repo_url: str):
        repo_name = repo_url.split("/")[-1].replace(".git", "")
        target_dir = os.path.join(self.learning_dir, repo_name)

        logger.info("Starting knowledge ingestion", repo=repo_url)

        # 1. Clone the repository
        if not os.path.exists(target_dir):
            subprocess.run(["git", "clone", "--depth", "1", repo_url, target_dir], check=True)
        else:
            subprocess.run(["git", "-C", target_dir, "pull"], check=True)

        # 2. Extract Knowledge (Analyze MD and Script files)
        learned_data = self._analyze_repo(target_dir)

        # 3. Store in Vector Memory (Mem0)
        # This allows the reco agent to retrieve these methods during live scans
        for method in learned_data:
            await self.memory.store_learned_method(method)
            
        logger.info("Knowledge base updated with new methods", repo=repo_name, methods_found=len(learned_data))

    def _analyze_repo(self, path: str) -> list:
        """
        Walks through the repo to find .md guides and .sh/.py tools.
        In a real scenario, we'd pass these snippets to the LLM to 'summarize' into a skill.
        """
        methods = []
        for root, _, files in os.walk(path):
            for file in files:
                if file.endswith((".md", ".sh", ".py")):
                    with open(os.path.join(root, file), 'r', errors='ignore') as f:
                        content = f.read()
                        if "workflow" in content.lower() or "recon" in content.lower():
                            methods.append({
                                "source": f"{root}/{file}",
                                "content": content[:2000] # Snippet for the LLM to learn from
                            })
        return methods

@celery_app.task(name="src.workers.learner_worker.learn_from_repo")
def learn_from_repo(repo_url: str):
    import asyncio
    learner = MethodologyLearner()
    asyncio.run(learner.ingest_repository(repo_url))
    return {"status": "success", "repo": repo_url}
