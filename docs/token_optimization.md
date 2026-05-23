# Token Optimization Layer

## Problem
Dumping raw tool output (like a 10MB subfinder text file or an extensive Katana crawl JSON) into an LLM context window will waste tokens, cause hallucination, and hit rate limits.

## Optimization Strategies

1. **Pre-Processing (Deduplication)**:
   - Use standard command-line tools (`sort -u`) or Python sets before data ever reaches the LLM.
   - Aggregate similar endpoints: `/api/users/1`, `/api/users/2` -> `/api/users/{id}`.

2. **Diffing and State Management**:
   - The OS only sends *new* information to the Agent.
   - Instead of "Here is the subdomain list," it sends: "15 new subdomains were found today. 14 resolve to known CDNs. 1 resolves to a new AWS IP: dev-staging.api.example.com."

3. **Contextual Retrieval (Mem0)**:
   - When analyzing `dev-staging.api.example.com`, the Agent queries Mem0 for "What do we know about the main api.example.com?". 
   - Mem0 returns only the most relevant summaries (e.g., "The main API uses GraphQL and JWTs for auth."), keeping the prompt small and highly focused.

4. **Structured JSON Output**:
   - The LLM outputs strict JSON to be parsed and inserted directly into Postgres/Neo4j, avoiding conversational filler that wastes tokens.
