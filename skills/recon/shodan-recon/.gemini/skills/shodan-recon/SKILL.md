---
name: shodan-recon
description: Shodan-based asset discovery and vulnerability scanning. Uses a "Double Verification" workflow to ensure high-signal bug bounty leads. Integrates Shodan, httpx, Nuclei, and custom Python probes.
---

# Shodan Recon (Professional Edition)

This skill provides a rigorous, professional-grade workflow for identifying and **confirming** vulnerabilities. To ensure high-quality reports that get paid, this skill implements the **Double Verification Protocol**.

## Core Mandate: Double Verification Protocol
Never report a vulnerability based on a single tool's output. Every bug must be confirmed at least twice using independent methods:

1.  **Source A (Initial Discovery)**: Shodan flags a CVE, Nuclei finds a match, or `httpx` identifies an exposed admin panel.
2.  **Source B (Confirmation)**: A targeted Python probe, a manual `curl` command to verify headers/paths, or cross-referencing version strings with known exploit databases.

**Example**:
- *Discovery*: Shodan reports CVE-2023-44487 on an asset.
- *Confirmation*: Run `scripts/http2_rapid_reset_checker.py` to prove the server lacks stream reset rate-limiting.

## Workflow

1.  **Asset Discovery**: Run `scripts/shodan_recon.sh <target.com>` to map the infrastructure.
2.  **Service Probing**: Identify live services and technologies using `httpx`.
3.  **Vulnerability Scanning**: Run `nuclei` with priority tags (exposure, misconfig, cve).
4.  **Targeted Confirmation**: 
    - For HTTP/2 bugs: Use `scripts/http2_rapid_reset_checker.py`.
    - For Admin Panels: Use `curl` to check for unauthenticated access or specific JS markers.
    - For CVEs: Match the reported version with the `Server:` header or technical artifacts.

## Usage

### 1. Full Scan
```bash
./scripts/shodan_recon.sh <target.com>
```

### 2. Verify HTTP/2 Rapid Reset (CVE-2023-44487)
```bash
python3 scripts/http2_rapid_reset_checker.py <target_domain>
```

### 3. Verify Admin Panel Exposure
```bash
curl -s -k -L --max-time 10 <url> | grep -iE "<app-root|<app-|<script|login|admin"
```

## Available Scripts

- `scripts/shodan_recon.sh`: The main orchestrator for discovery and initial scanning.
- `scripts/http2_rapid_reset_checker.py`: Safe PoC for CVE-2023-44487.
- `scripts/shodan_parse.py`: Generates the consolidated Markdown report.
- `scripts/nuclei_runner.sh`: Dedicated runner for high-signal Nuclei templates.

## Safety & Ethics
- **Safe PoCs Only**: Use low-volume probes that do not disrupt service.
- **Data Privacy**: Stop testing immediately if sensitive user data is accessed.
- **Authorized Targets**: Only scan domains within the scope of a Bug Bounty or VAPT engagement.
