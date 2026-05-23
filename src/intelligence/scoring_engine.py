from src.graph.neo4j_client import neo4j_client

class ExploitabilityScoringEngine:
    def __init__(self):
        self.graph = neo4j_client

    def score_target(self, target_name: str, js_data: dict = None, httpx_data: dict = None):
        """
        Calculates a custom offensive priority score.
        """
        score = 0
        reasons = []

        # Name-based heuristics
        name_lower = target_name.lower()
        if any(x in name_lower for x in ["admin", "corp", "internal", "intranet"]):
            score += 30
            reasons.append("Internal/Admin naming")
        if any(x in name_lower for x in ["dev", "staging", "uat", "test"]):
            score += 20
            reasons.append("Staging/Dev naming")
        if any(x in name_lower for x in ["api", "graphql", "gw"]):
            score += 15
            reasons.append("API endpoint")

        # JS Intelligence based heuristics
        if js_data:
            if js_data.get("secrets_count", 0) > 0:
                score += 40
                reasons.append("Leaked JS secrets")
            if js_data.get("has_graphql"):
                score += 25
                reasons.append("GraphQL exposure")
            if js_data.get("has_websockets"):
                score += 10
                reasons.append("WebSocket exposure")

        # HTTPx based heuristics
        if httpx_data:
            status = httpx_data.get("status_code", 0)
            if status in [401, 403]:
                score += 10 # Interesting bypass targets
                reasons.append("Auth required (Bypass potential)")
            if status == 500:
                score += 15
                reasons.append("Server error (Fuzzing potential)")
            
            tech = str(httpx_data.get("tech", [])).lower()
            if "swagger" in tech or "openapi" in tech:
                score += 25
                reasons.append("Swagger/OpenAPI documentation")
            if "waf" not in tech and "cloudflare" not in tech:
                score += 15
                reasons.append("No WAF detected")

        # Save to graph
        self._update_graph_score(target_name, score, reasons)
        return {"score": score, "reasons": reasons}

    def _update_graph_score(self, target: str, score: int, reasons: list):
        query = """
        MATCH (d:Domain {name: $target})
        SET d.priority_score = $score, d.priority_reasons = $reasons
        RETURN d
        """
        with self.graph.driver.session() as session:
            session.run(query, target=target, score=score, reasons=reasons)

scoring_engine = ExploitabilityScoringEngine()
