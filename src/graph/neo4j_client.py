# Mock Neo4j Client for environment without native Neo4j installed

class Neo4jClient:
    def __init__(self):
        self.driver = self

    def session(self):
        return self

    def __enter__(self):
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def run(self, query, **kwargs):
        # Mock execution, just return empty records
        class Record:
            def __init__(self, data):
                self._data = data
            def data(self):
                return self._data
            def values(self):
                return list(self._data.values())
        return []

    def close(self):
        pass

    def create_domain_node(self, domain_name: str, is_wildcard: bool = False):
        print(f"[GRAPH] Created Domain Node: {domain_name} (Wildcard: {is_wildcard})")
        return {"name": domain_name}

    def create_evidence_node(self, target: str, request_data: dict, observation: str, validation_state: str, impact_score: float):
        print(f"[GRAPH] Evidence Node: {target} | State: {validation_state} | Impact: {impact_score}")

neo4j_client = Neo4jClient()
