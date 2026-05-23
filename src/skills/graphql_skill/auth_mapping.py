from typing import Dict, Any, List

class AuthMappingEngine:
    """
    Analyzes queries and mutations to map required authorization boundaries.
    """
    def __init__(self):
        pass

    def map_boundaries(self, schema: dict) -> Dict[str, Any]:
        """
        Infers authorization boundaries based on operation names and types.
        """
        print("Mapping GraphQL authorization boundaries...")
        auth_boundaries = []
        
        if not schema or "data" not in schema or "__schema" not in schema["data"]:
            return {"auth_boundaries": []}

        types = schema["data"]["__schema"].get("types", [])
        
        for t in types:
            type_name = t.get("name", "")
            if type_name == "Mutation" and t.get("fields"):
                for mut in t["fields"]:
                    mut_name = mut.get("name", "")
                    # Heuristics for operations that SHOULD require auth
                    if any(k in mut_name.lower() for k in ["update", "delete", "create", "add", "remove", "set"]):
                        auth_boundaries.append({
                            "operation": mut_name,
                            "type": "Mutation",
                            "hypothesis": f"Verify that {mut_name} enforces authentication and authorization."
                        })

        return {
            "auth_boundaries": auth_boundaries,
            "count": len(auth_boundaries)
        }

auth_mapping_engine = AuthMappingEngine()
