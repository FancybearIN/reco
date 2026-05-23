from typing import List, Dict, Any
from src.graph.neo4j_client import neo4j_client
from src.intelligence.confidence_engine import confidence_engine

class ChainVerifier:
    """
    Builds probability-weighted attack chains.
    Does NOT assume exploitation; tracks missing evidence required to progress the chain.
    """
    def __init__(self):
        self.graph = neo4j_client

    def verify_chain(self, target_url: str, steps: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Takes a proposed attack chain (sequence of steps/findings) and weights it.
        E.g., Step 1: JS Secret (Confidence 0.9) -> Step 2: Internal API (Confidence 0.8) -> Step 3: BOLA (Missing)
        """
        print(f"Verifying attack chain for {target_url}")
        
        chain_probability = 1.0
        missing_evidence = []
        confirmed_steps = []

        for step in steps:
            confidence = step.get("confidence", 0.0)
            finding_type = step.get("type", "Unknown")
            
            if confidence >= 0.7:
                confirmed_steps.append(step)
                chain_probability *= confidence
            else:
                missing_evidence.append({
                    "step": finding_type,
                    "required_evidence": step.get("required_evidence", "Reproduction payload needed"),
                    "current_confidence": confidence
                })
                # Chain breaks or becomes highly improbable if a core step is missing
                chain_probability *= (confidence * 0.1)

        # Update Graph with the weighted chain
        self._update_graph_chain(target_url, confirmed_steps, missing_evidence, chain_probability)

        return {
            "chain_probability": chain_probability,
            "is_viable": chain_probability > 0.4 and len(missing_evidence) <= 1,
            "confirmed_steps": [s["type"] for s in confirmed_steps],
            "missing_evidence": missing_evidence
        }

    def _update_graph_chain(self, target: str, confirmed: list, missing: list, probability: float):
        """
        Updates the Neo4j Evidence Graph with the attack chain state.
        """
        query = """
        MATCH (d:Domain {name: $target})
        MERGE (ac:AttackChain {id: $chain_id})
        SET ac.probability = $probability,
            ac.confirmed_steps = $confirmed_steps,
            ac.missing_evidence = $missing_evidence
        MERGE (d)-[:HAS_PROBABLE_CHAIN]->(ac)
        """
        # Create a deterministic ID for the chain based on target and steps
        chain_id = f"{target}_chain_{len(confirmed)}"
        
        with self.graph.driver.session() as session:
            session.run(query, 
                        target=target, 
                        chain_id=chain_id,
                        probability=probability, 
                        confirmed_steps=[s["type"] for s in confirmed],
                        missing_evidence=[m["step"] for m in missing])

chain_verifier = ChainVerifier()
