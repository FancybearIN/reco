---
name: bounty-hunter
description: Specialized bug bounty workflow for finding high-impact, payable vulnerabilities on platforms like HackerOne/Bugcrowd. Supports multi-agent orchestration (Copilot) and parallel execution for maximum efficiency.
---

# Bounty Hunter Skill (High-Performance Edition)

This skill provides a professional-grade workflow for identifying vulnerabilities that have real-world impact. It is optimized for speed and token efficiency using **Multi-Agent Orchestration** and **Parallel Execution**.

## 🚨 Core Mandate: NO POC = NO REPORT
Theoretical vulnerabilities are NOT reportable. You MUST execute a safe, working PoC (e.g., retrieving `/etc/passwd`, showing `hostname`, or proving lack of rate limiting) to confirm a bug.

## ⚡ Performance Optimization

### 1. Multi-Agent Orchestration (Copilot Integration)
To save time and tokens, delegate specialized tasks to GitHub Copilot while you perform recon:
- **Code Analysis**: `copilot -p "Analyze this JS bundle for hidden API keys: [file]"`
- **Payload Generation**: `copilot -p "Generate a safe SSRF payload for an Apache server targeting 127.0.0.1"`
- **Exploit Research**: `copilot -p "What are the known unauthenticated exploit paths for Cisco ISE 2.x?"`

### 2. Parallel Execution Strategy
Execute independent tasks in parallel to reduce "Time to Bounty":
- **Recon + Fuzzing**: Run `shodan_recon.sh` in the background while manually probing the top leads.
- **Bulk Probing**: Use parallel `curl` or `httpx` calls to verify multiple admin panels at once.
- **Background Tasks**: Set `is_background: true` for long-running Nuclei or Shodan scans.

## Workflow

1.  **Mass Discovery**: Run `scripts/shodan_recon.sh <target.com>` (Set `is_background: true`).
2.  **Parallel Analysis**: While the scan runs, use `copilot` to analyze existing technical artifacts (headers, JS bundles).
3.  **Triage & Filter**: Identify the top 5 high-impact leads (Admin panels, EOL software, unauthenticated APIs).
4.  **Double Verification**:
    - *Discovery*: Shodan/Nuclei flag.
    - *Confirmation*: Custom PoC script (e.g., `http2_rapid_reset_checker.py`) or manual probe.
5.  **PoC Execution**: Generate and run a safe PoC. **NO POC = NO REPORT.**

## High-Impact Focus Areas
1. **Broken Access Control**: Unauthenticated Admin Panels (Integration Servers, Strapi, Jenkins).
2. **Sensitive Information Disclosure**: Exposed `.env`, `.git`, or cloud metadata.
3. **Critical Misconfigurations**: Unauthenticated Docker, Redis, or Elasticsearch.
4. **Parameter Vulnerabilities**: `?url=`, `?file=`, `?id=` (SSRF, LFI, IDOR).

## Useful Scripts
- `scripts/check_admin_exposure.sh`: Safely probes identified panels.
- `scripts/http2_rapid_reset_checker.py`: Safe PoC for CVE-2023-44487.

## Safety Rules
- **Non-Destructive Only**: No data deletion or service disruption.
- **Authorized Targets Only**: Verify scope before testing.
