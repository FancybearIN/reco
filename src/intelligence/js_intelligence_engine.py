import re
import math
import requests
from urllib.parse import urljoin
from src.memory.mem0_client import memory_client

class JSIntelligenceEngine:
    def __init__(self):
        self.endpoint_pattern = re.compile(r'(?:"|\')(((?:[a-zA-Z]{1,10}://|/)[^"\'\s]+|([a-zA-Z0-9_\-]+/)+[a-zA-Z0-9_\-]+))(?:"|\')')
        self.secret_pattern = re.compile(r'(?i)(?:api_key|apikey|secret|token|password|passwd|auth|bearer)[_-]?([a-zA-Z0-9_\-\.]{16,})')
        self.graphql_pattern = re.compile(r'(?i)(?:graphql|query|mutation)')

    def calculate_entropy(self, data: str) -> float:
        if not data: return 0
        entropy = 0
        for x in set(data):
            p_x = float(data.count(x)) / len(data)
            entropy += - p_x * math.log(p_x, 2)
        return entropy

    def analyze_js(self, js_url: str):
        print(f"Deep JS Analysis: {js_url}")
        try:
            # Native fetch
            response = requests.get(js_url, timeout=10)
            if response.status_code != 200:
                return
            
            content = response.text
            
            # 1. Endpoint Extraction

            endpoints = set()
            for match in self.endpoint_pattern.findall(content):
                ep = match[0]
                # Filter out obvious false positives like HTML tags
                if not ep.startswith("<") and not ep.endswith(">"):
                    endpoints.add(ep)

            # 2. Secret Extraction (Regex + Entropy validation)
            secrets = set()
            for match in self.secret_pattern.findall(content):
                secret_val = match
                # High entropy check to filter false positives
                if self.calculate_entropy(secret_val) > 3.5:
                    secrets.add(secret_val)

            # 3. Methodology Triggers
            has_graphql = bool(self.graphql_pattern.search(content))
            has_websockets = "wss://" in content or "ws://" in content
            
            # Persist Intelligence
            if secrets:
                memory_client.store_finding(
                    f"Found {len(secrets)} high-entropy secrets in JS: {js_url}",
                    metadata={"url": js_url, "type": "leaked_secret"}
                )
                
            for ep in endpoints:
                if "admin" in ep.lower():
                    memory_client.store_finding(
                        f"Admin route extracted from JS: {ep} in {js_url}",
                        metadata={"url": js_url, "endpoint": ep, "type": "admin_route"}
                    )

            return {
                "url": js_url,
                "endpoints": list(endpoints),
                "secrets_count": len(secrets),
                "has_graphql": has_graphql,
                "has_websockets": has_websockets
            }

        except Exception as e:
            print(f"Error analyzing JS {js_url}: {e}")
            return None

js_engine = JSIntelligenceEngine()
