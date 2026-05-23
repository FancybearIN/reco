from typing import Dict, Any, List

class ObjectReferenceAnalysis:
    """
    Analyzes how objects relate to each other to detect deep BOLA.
    E.g. Organization -> User -> Document.
    """
    def __init__(self):
        pass

    def analyze_references(self, schema: dict) -> Dict[str, Any]:
        """
        Maps object nesting to find authorization bypass chains.
        """
        print("Analyzing object references...")
        nested_objects = []
        
        if not schema or "data" not in schema or "__schema" not in schema["data"]:
            return {"nested_objects": []}

        types = schema["data"]["__schema"].get("types", [])
        
        for t in types:
            type_name = t.get("name", "")
            if t.get("kind") == "OBJECT" and not type_name.startswith("__"):
                if t.get("fields"):
                    for field in t["fields"]:
                        field_name = field.get("name", "")
                        # Check if a field returns another custom object type
                        field_type = field.get("type", {})
                        while field_type and field_type.get("kind") in ["NON_NULL", "LIST"]:
                            field_type = field_type.get("ofType", {})
                            
                        type_str = field_type.get("name", "")
                        
                        if type_str and not type_str.startswith("__") and type_str not in ["String", "Int", "Boolean", "ID", "Float"]:
                            nested_objects.append({
                                "parent": type_name,
                                "field": field_name,
                                "returns": type_str,
                                "hypothesis": f"If {type_name} is accessible, does it implicitly grant access to {type_str}?"
                            })

        return {
            "nested_objects": nested_objects,
            "count": len(nested_objects)
        }

object_ref_engine = ObjectReferenceAnalysis()
