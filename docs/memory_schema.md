# Memory Schema (Mem0)

Mem0 will be used to store persistent intelligence, reducing duplicate scans and optimizing token usage by providing relevant historical context to the LLM.

## Schema Types

### Entity Context
- `type`: "asset_context"
- `asset_id`: (domain/ip string)
- `content`: Summary of technologies, state, WAF presence, and known endpoints.
- `metadata`: { "last_scanned": timestamp, "is_live": boolean, "tech_stack": list }

### Hypotheses
- `type`: "attack_hypothesis"
- `target`: (URL/Endpoint)
- `content`: "GraphQL introspection is open, potential for alias overloading."
- `methodology`: "graphql_abuse"

### Recon Timelines
- `type`: "recon_event"
- `content`: "Discovered new staging domain staging.api.example.com via cert-san on IP 1.2.3.4"
- `timestamp`: timestamp

## Memory Agent Role
Before passing a large recon result (e.g., Katana crawl output) to an LLM, the Memory Agent:
1. Queries Mem0 for similar previously processed endpoints.
2. Filters out known duplicates.
3. Retrieves relevant Attack Hypotheses to inform the LLM's next steps.
