import subprocess
import json
from src.graph.neo4j_client import neo4j_client

class InfraClusterEngine:
    """
    Uses native Kali tooling (httpx) to cluster infrastructure 
    by JARM, Favicon, and TLS hashes, revealing hidden relationships.
    """
    def __init__(self):
        self.graph = neo4j_client

    def cluster_targets(self, targets_file: str):
        print(f"Clustering infrastructure for targets in {targets_file}")
        
        # httpx -l targets_file -jarm -favicon -tls-imhash -json -silent
        command = [
            "httpx", "-l", targets_file, 
            "-jarm", "-favicon", "-tls-imhash", 
            "-json", "-silent"
        ]
        
        try:
            result = subprocess.run(command, capture_output=True, text=True, check=True)
            output = result.stdout
        except subprocess.CalledProcessError as e:
            print(f"Error running httpx clustering: {e.stderr}")
            return
            
        for line in output.split("\n"):
            if not line.strip(): continue
            try:
                data = json.loads(line)
                url = data.get("url")
                jarm = data.get("jarm")
                favicon = data.get("favicon")
                tls_hash = data.get("tls", {}).get("imhash")
                
                # Update Graph with Clusters
                with self.graph.driver.session() as session:
                    # Merge the Domain/URL node
                    session.run("MERGE (d:Domain {name: $url})", url=url)
                    
                    if jarm:
                        session.run("""
                        MERGE (c:Cluster {type: 'JARM', hash: $jarm})
                        MATCH (d:Domain {name: $url})
                        MERGE (d)-[:BELONGS_TO]->(c)
                        """, jarm=jarm, url=url)
                        
                    if favicon:
                        session.run("""
                        MERGE (c:Cluster {type: 'Favicon', hash: $favicon})
                        MATCH (d:Domain {name: $url})
                        MERGE (d)-[:BELONGS_TO]->(c)
                        """, favicon=favicon, url=url)
                        
                    if tls_hash:
                        session.run("""
                        MERGE (c:Cluster {type: 'TLS_imhash', hash: $tls_hash})
                        MATCH (d:Domain {name: $url})
                        MERGE (d)-[:BELONGS_TO]->(c)
                        """, tls_hash=tls_hash, url=url)
                        
            except json.JSONDecodeError:
                continue

    def get_hidden_infrastructure(self, public_domain: str):
        """
        Query the graph to find nodes that share the same cluster 
        (e.g., JARM/Favicon) as the public domain, potentially revealing staging IPs.
        """
        query = """
        MATCH (d1:Domain {name: $public_domain})-[:BELONGS_TO]->(c:Cluster)<-[:BELONGS_TO]-(d2:Domain)
        WHERE d1 <> d2
        RETURN c.type as ClusterType, d2.name as HiddenDomain
        """
        with self.graph.driver.session() as session:
            records = session.run(query, public_domain=public_domain)
            return [{"type": r["ClusterType"], "hidden_domain": r["HiddenDomain"]} for r in records]

infra_cluster = InfraClusterEngine()
