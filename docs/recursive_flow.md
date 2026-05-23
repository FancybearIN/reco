# Recursive Recon Flow

## Principle
Every finding generates a new event, which the Orchestrator evaluates against known data (via Memory/Graph) to determine if new tasks should be spawned.

## Examples of Recursive Chains

### Chain 1: Infrastructure Expansion
1. Input: `company.com`
2. Task: Subdomain Enum -> Output: `dev.company.com`
3. Event: `new_subdomain` -> Triggers DNS Resolution
4. Task: Resolve DNS -> Output: `104.18.2.1` (CDN), CNAME: `company.aws.com`
5. Event: `new_cname` -> Triggers Cloud Bucket Enum on `company.aws.com`

### Chain 2: Application Deep Dive
1. Input: `https://api.company.com`
2. Task: Tech Fingerprint -> Output: `GraphQL`
3. Event: `tech_discovered:graphql` -> Triggers Introspection Check
4. Task: Introspection Enum -> Output: `Schema extracted, mutation createUser found`
5. Event: `new_api_route` -> Triggers Hypothesis Generation (e.g. Broken Object Level Authorization)

### Chain 3: JS Analysis
1. Input: `https://app.company.com`
2. Task: Deep Crawl -> Output: `main.js` found
3. Event: `new_js_file` -> Triggers Extract Secrets & Endpoints
4. Task: Extract Endpoints -> Output: `/api/v2/internal/stats`
5. Event: `new_endpoint` -> Triggers Auth Bypass heuristics.
