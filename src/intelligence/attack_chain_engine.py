from src.graph.neo4j_client import neo4j_client
from src.memory.mem0_client import memory_client
from src.intelligence.methodology_parser import MethodologyEngine

class AttackChainEngine:
    def __init__(self):
        self.graph = neo4j_client
        self.methodology = MethodologyEngine()

    def evaluate_chains(self, target_domain: str):
        """
        Evaluates discrete findings for a target to construct escalation paths.
        E.g., JS Secret + Internal API = BOLA candidate.
        """
        print(f"Evaluating attack chains for {target_domain}")
        
        # Pull discrete facts from Memory
        context = memory_client.retrieve_context(f"What findings exist for {target_domain}?", user_id="recon_agent")
        
        has_secret = any("secret" in c.get('text', '').lower() for c in context)
        has_graphql = any("graphql" in c.get('text', '').lower() for c in context)
        has_admin = any("admin" in c.get('text', '').lower() for c in context)
        
        chains = []
        
        if has_secret and has_graphql:
            chain = "JS Secret + GraphQL -> Privilege Escalation via authenticated introspection/mutations"
            chains.append(chain)
            self._write_chain_to_graph(target_domain, "Privilege Escalation", "GraphQL_Auth_Bypass")
            
        if has_admin:
            chain = "Admin Route exposed -> High priority auth bypass testing required"
            chains.append(chain)
            self._write_chain_to_graph(target_domain, "Auth Bypass", "Admin_Panel_Exposure")
            
            # Fetch semantic methodology
            methods = self.methodology.retrieve_methodologies("admin panel authentication bypass")
            if methods:
                memory_client.store_finding(
                    f"Methodology mapped for Attack Chain on {target_domain}: {methods[0]['topic']}",
                    metadata={"target": target_domain, "type": "attack_chain_methodology"}
                )

        return chains

    def _write_chain_to_graph(self, target: str, impact: str, technique: str):
        query = """
        MATCH (d:Domain {name: $target})
        MERGE (a:AttackChain {impact: $impact, technique: $technique})
        MERGE (d)-[:VULNERABLE_TO_CHAIN]->(a)
        """
        with self.graph.driver.session() as session:
            session.run(query, target=target, impact=impact, technique=technique)

chain_engine = AttackChainEngine()
