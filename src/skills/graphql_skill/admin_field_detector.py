from typing import Dict, Any, List

class AdminFieldDetector:
    """
    Analyzes the GraphQL schema to identify sensitive or admin-only fields and objects.
    """
    def __init__(self):
        self.sensitive_keywords = ["admin", "role", "password", "token", "ssn", "secret", "private", "internal", "permissions"]

    def analyze_schema(self, schema: dict) -> Dict[str, Any]:
        """
        Parses the introspection schema and extracts high-value targets.
        """
        print("Analyzing schema for admin fields...")
        sensitive_fields = []
        sensitive_mutations = []
        
        if not schema or "data" not in schema or "__schema" not in schema["data"]:
            return {"sensitive_fields": [], "sensitive_mutations": []}

        types = schema["data"]["__schema"].get("types", [])
        
        for t in types:
            type_name = t.get("name", "")
            # Ignore built-in GraphQL types
            if type_name.startswith("__"): continue
            
            # Check fields in object types
            if t.get("kind") == "OBJECT" and t.get("fields"):
                for field in t["fields"]:
                    field_name = field.get("name", "")
                    if any(k in field_name.lower() for k in self.sensitive_keywords):
                        sensitive_fields.append({
                            "object": type_name,
                            "field": field_name,
                            "type": field.get("type", {}).get("name", "Unknown")
                        })
            
            # Check Mutations
            if type_name == "Mutation" and t.get("fields"):
                for mut in t["fields"]:
                    mut_name = mut.get("name", "")
                    if any(k in mut_name.lower() for k in self.sensitive_keywords):
                        sensitive_mutations.append({
                            "mutation": mut_name,
                            "description": mut.get("description", "")
                        })

        return {
            "sensitive_fields": sensitive_fields,
            "sensitive_mutations": sensitive_mutations,
            "count": len(sensitive_fields) + len(sensitive_mutations)
        }

admin_detector = AdminFieldDetector()
