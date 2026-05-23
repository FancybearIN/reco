from src.graph.neo4j_client import neo4j_client

class AttackGraph:
    def __init__(self):
        self.client = neo4j_client

    def query_high_signal_targets(self):
        """
        Finds targets that are highly likely to be vulnerable based on 
        the intersection of clusters, intelligence findings, and priority scores.
        """
        query = """
        MATCH (d:Domain)
        OPTIONAL MATCH (d)-[:BELONGS_TO]->(c:Cluster)
        OPTIONAL MATCH (d)-[:VULNERABLE_TO_CHAIN]->(a:AttackChain)
        WITH d, count(c) as cluster_count, count(a) as chain_count
        WHERE d.priority_score > 50 OR chain_count > 0
        RETURN d.name as Target, 
               d.priority_score as Score, 
               d.priority_reasons as Reasons,
               cluster_count as InfrastructureClusters,
               chain_count as PotentialAttackChains
        ORDER BY d.priority_score DESC, chain_count DESC
        """
        results = []
        try:
            with self.client.driver.session() as session:
                records = session.run(query)
                for record in records:
                    results.append(record.data())
        except Exception as e:
            print(f"Graph query error: {e}")
        return results

    def discover_shared_infrastructure_risks(self):
        """
        Identifies staging/internal domains that share a signature (JARM/Favicon)
        with a domain that has a confirmed high-severity finding.
        """
        query = """
        MATCH (vulnerable:Domain)-[:BELONGS_TO]->(c:Cluster)<-[:BELONGS_TO]-(staging:Domain)
        WHERE vulnerable.priority_score > 70 AND vulnerable <> staging
        RETURN vulnerable.name as KnownVulnerable,
               c.type as SharedSignature,
               staging.name as StagingTarget,
               staging.priority_score as StagingScore
        """
        results = []
        try:
            with self.client.driver.session() as session:
                records = session.run(query)
                for record in records:
                    results.append(record.data())
        except Exception as e:
            print(f"Graph query error: {e}")
        return results

attack_graph = AttackGraph()
