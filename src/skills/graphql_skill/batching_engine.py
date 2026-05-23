import requests
import time
from typing import Dict, Any

class BatchingEngine:
    """
    Tests for Array-based query batching vulnerabilities (often leading to DoS or Auth bypass).
    """
    def __init__(self):
        pass

    def test_array_batching(self, endpoint: str, auth_headers: dict = None) -> Dict[str, Any]:
        """
        Sends an array of queries instead of a single object.
        """
        print(f"Testing array batching on {endpoint}")
        
        # Array of 10 simple queries
        payload = [{"query": "query { __typename }"} for _ in range(10)]
        
        headers = {"Content-Type": "application/json"}
        if auth_headers: headers.update(auth_headers)

        try:
            start_payload = time.time()
            resp = requests.post(endpoint, json=payload, headers=headers, timeout=15)
            payload_time = time.time() - start_payload
            
            if resp.status_code == 200:
                try:
                    data = resp.json()
                    # If it returns a list of responses, array batching is enabled
                    if isinstance(data, list) and len(data) == 10:
                        return {
                            "vulnerable": True,
                            "evidence": "Server processed an array of 10 queries.",
                            "confidence": 0.95
                        }
                except ValueError:
                    pass
        except Exception:
            pass
            
        return {"vulnerable": False, "confidence": 0.0}

batching_engine = BatchingEngine()
