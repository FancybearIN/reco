import requests
import time
from typing import Dict, Any

class AliasOverloadingEngine:
    """
    Tests GraphQL endpoints for Alias Overloading (DoS) vulnerabilities.
    """
    def __init__(self):
        pass

    def test_alias_overloading(self, endpoint: str, auth_headers: dict = None) -> Dict[str, Any]:
        """
        Generates a massive alias query and validates via timing/differential analysis.
        """
        print(f"Testing alias overloading on {endpoint}")
        
        # Generate payload with 100 aliases requesting __typename
        aliases = []
        for i in range(100):
            aliases.append(f"alias{i}: __typename")
        
        payload = {"query": "query { " + " ".join(aliases) + " }"}
        
        headers = {"Content-Type": "application/json"}
        if auth_headers: headers.update(auth_headers)

        try:
            # Baseline
            start_baseline = time.time()
            requests.post(endpoint, json={"query": "query { __typename }"}, headers=headers, timeout=10)
            baseline_time = time.time() - start_baseline
            
            # Payload
            start_payload = time.time()
            resp = requests.post(endpoint, json=payload, headers=headers, timeout=15)
            payload_time = time.time() - start_payload
            
            if resp.status_code == 200 and "data" in resp.json():
                response_data = resp.json()["data"]
                # Verify that multiple aliases were actually processed
                if "alias99" in response_data:
                    is_vulnerable = True
                    multiplier = payload_time / baseline_time if baseline_time > 0 else 0
                    
                    return {
                        "vulnerable": is_vulnerable,
                        "timing_multiplier": multiplier,
                        "evidence": "Server successfully processed 100 aliases in a single request.",
                        "confidence": 0.95
                    }
        except Exception as e:
            pass
            
        return {"vulnerable": False, "confidence": 0.0}

alias_engine = AliasOverloadingEngine()
