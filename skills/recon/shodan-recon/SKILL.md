---
name: shodan-recon
description: Shodan-based asset discovery and vulnerability scanning. Uses a "Double Verification" workflow to ensure high-signal bug bounty leads. Integrates Shodan, httpx, Nuclei, and custom Python probes.
---

# Shodan Recon (Professional Edition)

This skill provides a rigorous, professional-grade workflow for identifying and **confirming** vulnerabilities. To ensure high-quality reports that get paid, this skill implements the **Double Verification Protocol**.

## 🚨 Core Mandate: NO POC = NO REPORT (The "No Theory" Rule)
Bug bounty programs like HackerOne **do not accept theoretical vulnerabilities**. You must never generate a report based solely on a version banner (e.g., "The server is running PHP 7.3, therefore it is vulnerable to RCE CVE-X"). 

**If you cannot execute a safe, working Proof of Concept (PoC) that demonstrates the exact impact (e.g., retrieving `/etc/passwd`, showing `hostname` output, or proving a lack of rate limiting), the finding is NOT reportable.**

## Workflow & Verification

1.  **Asset Discovery**: Run `scripts/shodan_recon.sh <target.com>` to map the infrastructure.
2.  **Service Probing**: Identify live services and technologies using `httpx`.
3.  **Vulnerability Scanning**: Run `nuclei` with priority tags (exposure, misconfig, cve).
4.  **Targeted Confirmation (MANDATORY)**: 
    - **For CVEs (e.g., HTTP/2, SSRF)**: You MUST run a script or curl command that safely proves the flaw exists (e.g., `scripts/http2_rapid_reset_checker.py`). Matching a version header is strictly insufficient.
    - **For Admin Panels**: Use `curl` to prove the panel loads without authentication and exposes sensitive application logic.
    - **For Information Disclosure**: Retrieve and display the leaked secrets/configuration.

## Usage

### 1. Full Scan
```bash
./scripts/shodan_recon.sh <target.com>
```

### 2. Verify HTTP/2 Rapid Reset (CVE-2023-44487) - Example of a Valid PoC
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
