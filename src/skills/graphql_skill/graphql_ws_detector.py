import re
from typing import Dict, Any

class GraphQLWSDetector:
    """
    Detects if GraphQL Subscriptions via WebSockets are supported.
    """
    def __init__(self):
        pass

    def detect_ws(self, js_content: str) -> Dict[str, Any]:
        """
        Analyzes JS content for GraphQL WebSocket clients (e.g., subscriptions-transport-ws or graphql-ws).
        """
        ws_indicators = [
            "subscriptions-transport-ws",
            "graphql-ws",
            "SubscriptionClient",
            "createClient",
            "ws://"
        ]
        
        for indicator in ws_indicators:
            if indicator in js_content:
                return {
                    "ws_supported": True,
                    "evidence": f"Found '{indicator}' in JS.",
                    "confidence": 0.8
                }
                
        return {"ws_supported": False, "confidence": 0.0}

ws_detector = GraphQLWSDetector()
