# Graph Schema (Neo4j)

The graph database maps infrastructural and logical relationships to reveal weak clusters and attack paths.

## Nodes
- `Organization` (name, h1_handle)
- `Domain` (name, is_wildcard)
- `Subdomain` (name, status_code, priority_score)
- `IP_Address` (ip, asn, provider)
- `Port` (number, service, protocol)
- `Technology` (name, category, version)
- `API_Endpoint` (url, method, params)
- `Vulnerability` (name, severity, cve)
- `JS_File` (url, hash)

## Edges (Relationships)
- `(Organization)-[:OWNS]->(Domain)`
- `(Domain)-[:HAS_SUBDOMAIN]->(Subdomain)`
- `(Subdomain)-[:RESOLVES_TO]->(IP_Address)`
- `(IP_Address)-[:EXPOSES]->(Port)`
- `(Port)-[:RUNS]->(Technology)`
- `(Subdomain)-[:HOSTS]->(API_Endpoint)`
- `(Subdomain)-[:INCLUDES]->(JS_File)`
- `(JS_File)-[:REFERENCES]->(API_Endpoint)`
- `(Subdomain)-[:AFFECTED_BY]->(Vulnerability)`

## Usage
- **Querying Attack Paths**: "Find all subdomains resolving to an IP in ASN X that run an outdated Technology Y."
- **Visual Mapping**: Rendering the target infrastructure via Cytoscape.js.
