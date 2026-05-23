# Methodology Ingestion System

## Goal
Map findings to offensive methodologies dynamically using HackTricks, HowToHunt, and nuclei-templates as knowledge bases.

## Workflow
1. **Trigger**: A new technology, parameter, or endpoint structure is identified (e.g., `?url=...` parameter found).
2. **Contextual Retrieval**: 
   - The System queries the Methodology Database for keywords: "open redirect", "SSRF", "url parameter".
   - Retrieves methodologies from HackTricks (e.g., SSRF bypasses).
3. **Agent Evaluation**:
   - The Vulnerability Heuristic Agent evaluates the endpoint against the retrieved methodologies.
   - Example: The Agent creates an attack task: `task_ssrf_probing` utilizing specific payloads (e.g., cloud metadata IPs) based on the target's hosted environment.
4. **Actionable Output**: If automated checks fail but the endpoint looks highly suspicious, the system adds it to the Dashboard with a high priority score and notes: "Human review needed: SSRF candidate on AWS infrastructure."
