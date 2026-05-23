---
name: shodan-recon
description: Shodan-based asset discovery and vulnerability scanning. Use this skill to perform reconnaissance on a domain using Shodan, probe for live services with httpx, and scan for vulnerabilities with Nuclei.
---

# Shodan Recon

This skill provides a workflow for automated reconnaissance and vulnerability scanning using Shodan, httpx, and Nuclei.

## Workflow

1. **Asset Discovery**: Use `shodan_recon.sh` to query Shodan for subdomains, IPs, and open ports related to a target domain.
2. **Service Probing**: The script automatically uses `httpx` to identify live HTTP services.
3. **Vulnerability Scanning**: The script runs `nuclei` against discovered live targets using priority templates.
4. **Reporting**: Results are parsed by `shodan_parse.py` to generate a markdown report.

## Usage

To start the reconnaissance process, run the `shodan_recon.sh` script with the target domain:

```bash
./scripts/shodan_recon.sh <target.com>
```

### Script Details

- `scripts/shodan_recon.sh`: The main orchestrator. It performs Shodan queries, runs `httpx`, and initiates `nuclei`.
- `scripts/shodan_parse.py`: A helper script to parse Shodan results and generate the final report.
- `scripts/nuclei_runner.sh`: A dedicated script for running Nuclei with specific templates and severity levels.

## Safety & Ethics

- Only scan targets you are authorized to test.
- Follow the rules of engagement and bug bounty policies.
- This skill performs active probing (`httpx`, `nuclei`). Ensure you have permission for these activities.

## Requirements

- Shodan CLI (configured with `shodan init <API_KEY>`)
- `jq`
- `httpx`
- `nuclei`
- Python 3
