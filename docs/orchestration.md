# Orchestration Design

## Workflow Orchestrator (Celery)
The orchestration is task-driven. When a new asset is ingested, it triggers an event that cascades into subsequent tasks.

### Event-Driven Pipeline
1. `task_ingest_scope`: Ingests wildcard domain `*.example.com`.
2. `task_passive_recon`: Subfinder, Amass, GitHub dorks.
3. `task_active_recon`: DNS resolution (dnsx), port scanning (naabu).
4. `task_http_probing`: Live host detection (httpx).
5. `task_tech_fingerprinting`: Nuclei (tech detection), Wappalyzer.
6. `task_deep_crawl`: Katana, JS extraction.

### Recursive Dispatch
Each task yields *results*. The Orchestrator evaluates results and dispatches new tasks.
- Example: `task_http_probing` finds a live `api.example.com`.
- Orchestrator dispatches `task_api_enumeration` and `task_deep_crawl` for `api.example.com`.

### Concurrency and Rate Limiting
- Celery workers are segmented into queues:
  - `passive_queue`: High concurrency, non-intrusive.
  - `active_queue`: Rate-limited, intrusive (nuclei, fuzzing).
  - `agent_queue`: LLM processing, memory retrieval.
