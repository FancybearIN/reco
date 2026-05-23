import os
import subprocess
import shlex
from typing import List, Optional
from pydantic import BaseModel
import structlog

logger = structlog.get_logger(__name__)

# --- SCOPE GUARD ---
class ScopeGuard:
    """Ensures that all targets and actions remain within the authorized scope."""
    def __init__(self, authorized_domains: List[str]):
        self.authorized_domains = [d.lower() for d in authorized_domains]

    def is_in_scope(self, target: str) -> bool:
        target = target.lower()
        for domain in self.authorized_domains:
            if target == domain or target.endswith(f".{domain}"):
                return True
        return False

# --- SUBPROCESS ALLOWLIST & SAFETY ---
ALLOWED_TOOLS = {
    "subfinder": "/usr/bin/subfinder",
    "nuclei": "/usr/bin/nuclei",
    "httpx": "/usr/bin/httpx",
    "nmap": "/usr/bin/nmap",
    "curl": "/usr/bin/curl",
    "dig": "/usr/bin/dig",
    "whois": "/usr/bin/whois"
}

class SecurityGuard:
    """Safely executes local system tools with sanitization and allowlisting."""
    
    @staticmethod
    def run_tool(tool_name: str, args: List[str], timeout: int = 300) -> Optional[str]:
        if tool_name not in ALLOWED_TOOLS:
            logger.error("Unauthorized tool execution attempt", tool=tool_name)
            return None

        executable = ALLOWED_TOOLS[tool_name]
        # Sanitization: Ensure args are strings and shell-safe
        safe_args = [shlex.quote(str(a)) for a in args]
        command = [executable] + safe_args

        try:
            logger.info("Executing native tool", command=" ".join(command))
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False
            )
            return result.stdout
        except subprocess.TimeoutExpired:
            logger.error("Tool execution timed out", tool=tool_name)
            return None
        except Exception as e:
            logger.error("Tool execution error", tool=tool_name, error=str(e))
            return None
