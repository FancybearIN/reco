import requests
from typing import Dict, Any

class PersistedQueryAnalyzer:
    """
    Detects if APQ (Automatic Persisted Queries) is enabled, which can be abused for DoS or cache poisoning.
    """
    def __init__(self):
        pass

    def detect_apq(self, endpoint: str) -> Dict[str, Any]:
        print(f"Testing for Automatic Persisted Queries on {endpoint}")
        
        # Send a query with an invalid SHA256 hash to trigger APQ response
        payload = {
            "extensions": {
                "persistedQuery": {
                    "version": 1,
                    "sha256Hash": "invalid_hash_to_trigger_apq_error_message"
                }
            }
        }
        
        headers = {"Content-Type": "application/json"}
        
        try:
            resp = requests.post(endpoint, json=payload, headers=headers, timeout=10)
            if "PersistedQueryNotFound" in resp.text or "Provided sha does not match query" in resp.text:
                return {
                    "apq_enabled": True,
                    "evidence": "Server responded with PersistedQueryNotFound.",
                    "confidence": 0.9
                }
        except Exception:
            pass
            
        return {"apq_enabled": False, "confidence": 0.0}

apq_engine = PersistedQueryAnalyzer()
