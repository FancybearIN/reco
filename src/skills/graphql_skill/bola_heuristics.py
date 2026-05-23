from typing import Dict, Any, List

class BOLAHeuristicsEngine:
    """
    Reasons about Broken Object Level Authorization (BOLA/IDOR) opportunities
    by analyzing object reference patterns in queries and mutations.
    """
    def __init__(self):
        pass

    def analyze_references(self, schema: dict) -> Dict[str, Any]:
        """
        Identifies queries/mutations that accept predictable IDs.
        """
        print("Analyzing schema for BOLA heuristics...")
        bola_candidates = []
        
        if not schema or "data" not in schema or "__schema" not in schema["data"]:
            return {"bola_candidates": []}

        types = schema["data"]["__schema"].get("types", [])
        
        for t in types:
            type_name = t.get("name", "")
            if type_name not in ["Query", "Mutation"]:
                continue
                
            if t.get("fields"):
                for field in t["fields"]:
                    op_name = field.get("name", "")
                    args = field.get("args", [])
                    
                    for arg in args:
                        arg_name = arg.get("name", "")
                        arg_type = arg.get("type", {})
                        
                        # Unwrap non-null/list types
                        while arg_type and arg_type.get("kind") in ["NON_NULL", "LIST"]:
                            arg_type = arg_type.get("ofType", {})
                            
                        type_str = arg_type.get("name", "")
                        
                        # Heuristic: If an operation takes an ID, Int, or String ending in 'id'
                        if type_str in ["ID", "Int"] or arg_name.lower().endswith("id"):
                            bola_candidates.append({
                                "operation_type": type_name,
                                "operation_name": op_name,
                                "target_argument": arg_name,
                                "argument_type": type_str,
                                "hypothesis": f"Test {op_name} by substituting {arg_name} with alternate user IDs."
                            })

        return {
            "bola_candidates": bola_candidates,
            "high_priority_count": len(bola_candidates)
        }

bola_engine = BOLAHeuristicsEngine()
