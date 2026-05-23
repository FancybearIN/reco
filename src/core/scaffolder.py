import os
from src.core.config import settings
import structlog

logger = structlog.get_logger(__name__)

def scaffold_target(target_name: str):
    """
    Creates the standardized folder structure for a new target in /home/kali/bugbounty/
    """
    base_path = settings.get_target_path(target_name)
    subfolders = [
        "00_scope",
        "01_raw",
        "02_recon",
        "03_visuals",
        "04_findings",
        "05_reports"
    ]
    
    try:
        if not os.path.exists(settings.OUTPUT_ROOT):
            os.makedirs(settings.OUTPUT_ROOT)
            
        for folder in subfolders:
            path = os.path.join(base_path, folder)
            os.makedirs(path, exist_ok=True)
            
        logger.info("Target directory structure scaffolded", target=target_name, path=base_path)
        return base_path
    except Exception as e:
        logger.error("Failed to scaffold target directory", target=target_name, error=str(e))
        return None
