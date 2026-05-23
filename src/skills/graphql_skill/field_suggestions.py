import requests
from typing import Dict, Any

class FieldSuggestionsEngine:
    """
    Tests if the GraphQL server leaks valid field/type names via 'Did you mean X?' suggestions,
    allowing schema enumeration even if introspection is disabled.
    """
    def __init__(self):
        pass

    def test_suggestions(self, endpoint: str, auth_headers: dict = None) -> Dict[str, Any]:
        """
        Intentionally misspell a common type to check for suggestions.
        """
        print(f"Testing field suggestions on {endpoint}")
        
        payload = {"query": "query { userr { id } }"} # Intentional typo
        
        headers = {"Content-Type": "application/json"}
        if auth_headers: headers.update(auth_headers)

        try:
            resp = requests.post(endpoint, json=payload, headers=headers, timeout=10)
            if "Did you mean" in resp.text or "Cannot query field" in resp.text:
                if "user" in resp.text.lower():
                    return {
                        "vulnerable": True,
                        "evidence": "Server leaked valid field name via error suggestion.",
                        "confidence": 0.9
                    }
        except Exception:
            pass
            
        return {"vulnerable": False, "confidence": 0.0}

suggestions_engine = FieldSuggestionsEngine()
