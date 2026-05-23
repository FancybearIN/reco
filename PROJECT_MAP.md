# Reco Project Map

## Entrypoints
- `reco`: Primary CLI entrypoint (Python wrapper).
- `hunt/main.py`: Legacy/Core entrypoint.

## Core Modules (`src/`)
- `core/pipeline.py`: Main execution orchestrator.
- `recon/`: URL collection, Dorking, Exposure, and Port discovery.
- `intelligence/`: GF analysis, JS analysis, Hypothesis engine, and Nuclei parsing.
- `orchestration/`: Celery and Redis event routing.
- `memory/`: Neo4j and Mem0 integration.

## Configuration
- `config/reco.yaml`: Scan profiles and rate limits.
- `config/wordlists.yaml`: Wordlist definitions.

## Scripts & Skills
- `scripts/`: Operational bash scripts organized by function.
- `skills/`: Gemini CLI expertise files.

## Output Structure (`runs/<target>/`)
- `recon/`: Resolved subdomains and status.
- `urls/`: Collected and filtered URLs.
- `shodan/`, `fofa/`, `censys/`: Exposure results.
- `findings/`: Candidate and reportable findings.
- `reports/`: Evidence packs and summaries.

## Recommended Gemini Workflow
1. **Health Check**: Run `python -m src.cli healthcheck`.
2. **Recon**: Start with `reco hunt --target <domain> --profile safe`.
3. **Analyze**: Review `findings/candidates.json`.
4. **Report**: Check `reports/evidence_pack.md`.
