from neo4j import AsyncGraphDatabase
from typing import Dict, Any, List, Optional
from src.core.config import settings
import structlog

logger = structlog.get_logger(__name__)

class MemoryAgent:
    """
    Memory Abstraction Layer linking Neo4j (Graph) and Vector context.
    Provides merge-safe queries to build the attack surface graph.
    """
    def __init__(self):
        self.driver = AsyncGraphDatabase.driver(
            settings.NEO4J_URI, 
            auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
        )

    async def close(self):
        await self.driver.close()

    async def add_target(self, domain: str):
        query = """
        MERGE (t:Target {name: $domain})
        RETURN t
        """
        async with self.driver.session() as session:
            await session.run(query, domain=domain)
            logger.info("Added target to graph", domain=domain)

    async def add_subdomain(self, target: str, subdomain: str):
        query = """
        MATCH (t:Target {name: $target})
        MERGE (s:Subdomain {name: $subdomain})
        MERGE (t)-[:RESOLVES_TO]->(s)
        RETURN s
        """
        async with self.driver.session() as session:
            await session.run(query, target=target, subdomain=subdomain)
            logger.debug("Added subdomain to graph", target=target, subdomain=subdomain)

    async def add_technology(self, target: str, tech: str):
        query = """
        MATCH (t:Target {name: $target})
        MERGE (tc:Technology {name: $tech})
        MERGE (t)-[:USES_TECH]->(tc)
        """
        async with self.driver.session() as session:
            await session.run(query, target=target, tech=tech)
            
    async def add_finding(self, target: str, finding_data: Dict[str, Any]):
        query = """
        MATCH (t:Target {name: $target})
        MERGE (f:Finding {id: $finding_id})
        SET f += $finding_properties
        MERGE (t)-[:EXPOSES]->(f)
        """
        finding_id = finding_data.get("url", str(hash(str(finding_data))))
        
        # Clean dict to only primitive properties for Neo4j
        properties = {k: v for k, v in finding_data.items() if isinstance(v, (str, int, float, bool))}
        
        async with self.driver.session() as session:
            await session.run(query, target=target, finding_id=finding_id, finding_properties=properties)
            logger.info("Added finding to graph", finding_id=finding_id)

    async def get_target_graph(self, domain: str) -> Dict[str, Any]:
        """
        Graph traversal query to fetch all linked assets for a target.
        """
        query = """
        MATCH (t:Target {name: $domain})-[r]-(n)
        RETURN type(r) as relationship, labels(n) as labels, properties(n) as properties
        """
        result_data = []
        async with self.driver.session() as session:
            result = await session.run(query, domain=domain)
            async for record in result:
                result_data.append({
                    "relationship": record["relationship"],
                    "node_labels": record["labels"],
                    "node_properties": record["properties"]
                })
        return {"domain": domain, "relationships": result_data}

    async def store_learned_method(self, method_data: Dict[str, Any]):
        """
        Stores a learned methodology into the Vector Memory (Mem0)
        so the reco agent can recall it during task planning.
        """
        logger.info("Storing learned methodology in Vector Memory", source=method_data["source"])
        # Integration logic for Mem0/Qdrant would go here
        # For now, we simulate the 'intelligence' growth
        pass
