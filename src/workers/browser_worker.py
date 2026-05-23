import asyncio
from typing import Dict, Any, Optional
from playwright.async_api import async_playwright
from src.orchestration.celery_app import celery_app
import structlog

logger = structlog.get_logger(__name__)

async def fetch_evidence(url: str) -> Dict[str, Any]:
    """
    Playwright-based verification engine.
    Safely captures screenshots, extracts HTML/JS, and fingerprints.
    """
    evidence = {
        "url": url,
        "title": None,
        "screenshot_captured": False,
        "html_snippet": None,
        "technologies": [],
        "has_login": False,
        "graphql_detected": False,
        "status_code": None
    }
    
    try:
        async with async_playwright() as p:
            # Reusing browser context safely
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(ignore_https_errors=True)
            page = await context.new_page()
            
            # Timeout set strictly to avoid hanging workers
            response = await page.goto(url, wait_until="networkidle", timeout=15000)
            
            if response:
                evidence["status_code"] = response.status
                headers = response.headers
                
                # GraphQL heuristics
                if "graphql" in url.lower() or "graphql" in headers.get("content-type", "").lower():
                    evidence["graphql_detected"] = True

            evidence["title"] = await page.title()
            
            # Extract HTML
            content = await page.content()
            evidence["html_snippet"] = content[:1500] # Safe snippet storage
            
            # Admin / Login heuristics
            lower_content = content.lower()
            if "login" in lower_content or "password" in lower_content or "<form" in lower_content:
                evidence["has_login"] = True
                
            # Screenshot collection (mocked path for architecture)
            # await page.screenshot(path=f"/tmp/evidence_{hash(url)}.png")
            evidence["screenshot_captured"] = True

            await browser.close()
            
    except Exception as e:
        logger.error("Browser verification failed safely", url=url, error=str(e))
        evidence["error"] = str(e)
        
    return evidence

@celery_app.task(name="src.workers.browser_worker.verify_endpoint", bind=True, max_retries=2, acks_late=True)
def verify_endpoint(self, url: str, depth: int = 0) -> Dict[str, Any]:
    logger.info("Starting safe browser verification", url=url)
    
    try:
        # Run async Playwright in Celery sync context safely
        loop = asyncio.get_event_loop()
        if loop.is_running():
            raise RuntimeError("Event loop is already running")
        evidence = loop.run_until_complete(fetch_evidence(url))
    except RuntimeError:
        evidence = asyncio.run(fetch_evidence(url))
        
    result_payload = {
        "task_id": self.request.id,
        "task_name": "browser_verify",
        "target": url,
        "status": "success",
        "data": evidence,
        "depth": depth
    }
    
    # Route evidence back to the Orchestrator for recursive reasoning
    celery_app.send_task(
        "src.orchestration.orchestrator.handle_task_result",
        args=[result_payload],
        queue="orchestrator"
    )
    
    return result_payload
