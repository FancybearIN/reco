---
name: bounty-hunter
description: Specialized bug bounty workflow for finding high-impact, payable vulnerabilities on platforms like HackerOne/Bugcrowd. Focuses on Shodan-based asset discovery, sensitive interface exposure, and intelligent parameter fuzzing.
---

# Bounty Hunter Skill

This skill provides a professional-grade workflow for identifying vulnerabilities that have real-world impact and are highly likely to be accepted by Bug Bounty programs.

## High-Impact Focus Areas

To get paid, focus on these "Gold Mine" findings:
1. **Broken Access Control**: Administrative panels (Integration Servers, Strapi, Jenkins, SAP) accessible without authentication.
2. **Sensitive Information Exposure**: Exposed `.env` files, `.git` directories, or cloud metadata endpoints.
3. **Critical Misconfigurations**: Unauthenticated Docker APIs, Redis instances, or Elasticsearch clusters.
4. **Parameter Vulnerabilities**: Identifying interesting parameters (`url=`, `file=`, `redirect=`) for SSRF, LFI, or Open Redirects.

## Workflow

### 1. Shodan Asset Discovery
Use Shodan to find the "forgotten" infrastructure of a target.
- **Search Dorks**:
  - `ssl.cert.subject.cn:target.com`
  - `hostname:target.com port:80,443,8080,8443,9000`
  - `http.title:"Dashboard" target.com`
  - `product:"Jenkins" target.com`

### 2. Intelligent Port Analysis
Don't just look at 80/443. Check for services that shouldn't be public:
- **Port 2375/2376**: Docker API (Check for unauthenticated access)
- **Port 6379**: Redis (Check for `INFO` command)
- **Port 9200**: Elasticsearch (Check for `/_cat/indices`)
- **Port 8080/8443**: Alternative management ports.

### 3. Parameter Discovery & Fuzzing
Find parameters that lead to high-impact bugs:
- **Tools**: Use `gau` or `waybackurls` to find historical parameters.
- **Patterns**:
  - `?url=`, `?dest=`, `?next=` -> **SSRF / Open Redirect**
  - `?file=`, `?path=`, `?include=` -> **LFI / RCE**
  - `?id=`, `?user_id=` -> **IDOR** (Test if you can access other users' data)

### 4. Validation & Reporting
A bug is only payable if it's reproducible.
- **Capture Proof**: Take screenshots of the administrative panel or sensitive data.
- **Impact Description**: Clearly explain *why* it matters (e.g., "This allows an attacker to control internal middleware").
- **HackerOne Standards**: Follow the [VDP/Bug Bounty policies](https://hackerone.com/directory) for the specific target.

## Safety Rules
- **Non-Destructive Only**: Never delete data or disrupt services.
- **No Brute Force**: Avoid automated credential stuffing unless explicitly allowed.
- **Data Privacy**: If you find sensitive user data, stop immediately and report the exposure without downloading the data.

## Useful Scripts
- `scripts/check_admin_exposure.sh`: Safely probes identified panels.
- `scripts/param_finder.py`: Extracts and categorizes parameters for fuzzing.
