# Recon OS Architecture

## Core Components
The system is built as a distributed, microservice-like agent architecture.

1. **API Layer (FastAPI)**: Serves as the control plane for the OS. It ingests HackerOne scope, triggers root task execution, and provides endpoints for the frontend dashboard.
2. **Orchestration Layer (Celery + Redis)**: Manages the distributed task queue. Recon tools and recursive scans are dispatched as background jobs to prevent blocking.
3. **Agent Layer**:
   - **Planner Agent**: Analyzes scope and orchestrates the sequence of high-level tasks.
   - **Recon Agent**: Wraps tools (subfinder, httpx, nuclei) and handles the actual execution.
   - **Correlation Agent**: Correlates IPs, CNAMEs, favicons, and ASNs.
   - **Crawling Agent**: Deep crawling, JS extraction, endpoint mining.
   - **Memory Agent**: Interfaces with Mem0 to manage persistent intelligence, suppress duplicates, and fetch historical context.
   - **Prioritization Agent**: Scores targets based on heuristics (e.g., exposed admin, unusual ports).
   - **Vulnerability/Exploitation Heuristic Agents**: Maps findings to HackTricks/methodologies and suggests exploitation paths.
   - **Reporting Agent**: Formats high-signal findings for human review.
4. **Data Layer**:
   - **PostgreSQL**: Relational data, configuration, tool state, basic asset inventory.
   - **Neo4j**: Graph database to map relationships between organizations, domains, IPs, APIs, and vulnerabilities.
   - **Mem0**: Vector-based memory for context, hypothesis tracking, and token-optimized retrieval.

## Tech Stack
- Backend: Python 3.11+, FastAPI
- Queue: Celery, Redis
- Databases: PostgreSQL, Neo4j, Qdrant/Milvus (via Mem0)
- Frontend: React + Cytoscape.js (Phase 5)
- Containerization: Docker & Docker Compose
