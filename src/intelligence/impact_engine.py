from typing import Dict, Any

class ImpactEngine:
    """
    Estimates real-world organizational and user impact.
    Differentiates between theoretical exposure and high-risk exploitability.
    """
    def __init__(self):
        pass

    def calculate_impact(self, target_context: Dict[str, Any], finding_type: str, evidence: str) -> Dict[str, Any]:
        """
        Calculates impact based on privileges, data exposure, and internet exposure.
        """
        org_impact = 0.0
        user_impact = 0.0
        chainability = 0.0
        
        is_admin = "admin" in target_context.get("url", "").lower() or "admin" in target_context.get("title", "").lower()
        is_internal = "internal" in target_context.get("url", "").lower()
        
        # Heuristics for finding types
        if finding_type == "XSS":
            user_impact = 0.8 if is_admin else 0.4
            chainability = 0.7 if is_admin else 0.2
            org_impact = 0.5 if is_admin else 0.1
            
        elif finding_type == "SSRF":
            if "169.254.169.254" in evidence or "metadata" in evidence.lower():
                org_impact = 1.0 # Cloud metadata extraction
                chainability = 0.9 # RCE/Pivoting
            else:
                org_impact = 0.4 # Blind/Internal port scan
                chainability = 0.5
                
        elif finding_type == "GraphQL Exposure":
            if is_admin:
                org_impact = 0.9
                chainability = 0.8
            else:
                org_impact = 0.3
                chainability = 0.4

        # Final Impact Rating
        total_score = (org_impact * 0.5) + (user_impact * 0.3) + (chainability * 0.2)
        
        rating = "Low"
        if total_score > 0.8: rating = "Critical"
        elif total_score > 0.6: rating = "High"
        elif total_score > 0.4: rating = "Medium"

        return {
            "organization_impact": org_impact,
            "user_impact": user_impact,
            "chainability": chainability,
            "total_score": total_score,
            "rating": rating
        }

impact_engine = ImpactEngine()
