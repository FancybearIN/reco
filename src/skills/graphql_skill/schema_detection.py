import requests
from typing import Dict, Any, List

class SchemaDetectionEngine:
    """
    Reliably detects GraphQL endpoints.
    Checks common paths and verifies if the endpoint actually speaks GraphQL.
    """
    def __init__(self):
        self.common_paths = [
            "/graphql", "/api/graphql", "/v1/graphql", "/v2/graphql", 
            "/graphql/v1", "/graphql/console", "/graphiql", "/api"
        ]

    def detect_endpoint(self, base_url: str) -> Dict[str, Any]:
        print(f"Detecting GraphQL endpoint for {base_url}")
        
        detected_endpoints = []
        
        for path in self.common_paths:
            target = f"{base_url.rstrip('/')}{path}"
            if self._verify_graphql_endpoint(target):
                detected_endpoints.append(target)
                
        return {
            "found": len(detected_endpoints) > 0,
            "endpoints": detected_endpoints
        }
        
    def _verify_graphql_endpoint(self, url: str) -> bool:
        """
        Sends an empty query or invalid query to verify the GraphQL error format.
        """
        try:
            # Send an invalid query. A real GraphQL server usually returns 200/400 with a specific JSON structure.
            resp = requests.post(url, json={"query": "{ __typename }"}, timeout=5)
            if "data" in resp.text or "errors" in resp.text or "graphql" in resp.headers.get("Content-Type", "").lower():
                # Double check with a syntax error
                err_resp = requests.post(url, json={"query": "invalid_query"}, timeout=5)
                if "Syntax Error" in err_resp.text or "GRAPHQL_PARSE_FAILED" in err_resp.text:
                    return True
        except requests.exceptions.RequestException:
            pass
        return False

schema_detector = SchemaDetectionEngine()
