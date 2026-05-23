import os
import requests
from src.core.config import settings

class MemoryClient:
    def __init__(self):
        self.api_key = os.getenv("MEM0_API_KEY") or settings.MEM0_API_KEY
        self.base_url = "https://api.mem0.ai/v1"

    def store_finding(self, finding: str, user_id: str = "recon_agent", metadata: dict = None):
        url = f"{self.base_url}/memories/"
        headers = {
            "Authorization": f"Token {self.api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "messages": [{"role": "user", "content": finding}],
            "user_id": user_id,
            "metadata": metadata
        }
        response = requests.post(url, headers=headers, json=data)
        return response.json()
        
    def retrieve_context(self, query: str, user_id: str = "recon_agent"):
        url = f"{self.base_url}/search/"
        headers = {
            "Authorization": f"Token {self.api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "query": query,
            "user_id": user_id
        }
        response = requests.post(url, headers=headers, json=data)
        return response.json()

memory_client = MemoryClient()
