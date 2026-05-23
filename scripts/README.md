# Reco Scripts

This folder contains all shell scripts used by the Reco system.

## Structure

- `recon/`: Scripts for reconnaissance and discovery (e.g., `subdomain_master.sh`).
- `install/`: Setup and installation scripts.
- `health/`: Tooling and environment health check scripts.
- `utils/`: Operational helpers (start API, workers, new targets).
- `archive/`: Old or deprecated scripts.

## Usage for Gemini CLI

- **Setup**: Use `scripts/install/setup_native.sh` for environment preparation.
- **Operations**: Use `scripts/utils/start_api.sh` and `start_worker.sh` to manage services.
- **Maintenance**: Use `python -m src.cli healthcheck` to verify tool status.

> ⚠️ **Warning**: Do not modify files in `recon/` or `utils/` unless specifically requested, as they are core to the pipeline execution.
