#!/usr/bin/env python3
import sys
import re
import json
from pathlib import Path

if len(sys.argv) < 3:
    print("Usage: shodan_parse.py <out_dir> <target> [--report]")
    sys.exit(1)

OUT = Path(sys.argv[1])
TARGET = sys.argv[2].lower()
REPORT_MODE = "--report" in sys.argv

SHODAN_DIR = OUT / "shodan"
EXTRACTED = OUT / "extracted"
HTTPX_DIR = OUT / "httpx"
NUCLEI_DIR = OUT / "nuclei"

EXTRACTED.mkdir(exist_ok=True)

ip_re = re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}\b')
cve_re = re.compile(r'CVE-\d{4}-\d{4,7}', re.I)
sub_re = re.compile(r'([a-zA-Z0-9_.-]+\.' + re.escape(TARGET) + r')', re.I)

def write_list(path, items):
    clean = sorted(set(x.strip() for x in items if x and x.strip()))
    path.write_text("\n".join(clean) + ("\n" if clean else ""))

def parse_loose_text():
    ips = set()
    subs = set()
    cves = set()
    ip_ports = set()
    products = set()

    for file in SHODAN_DIR.glob("*"):
        if file.is_dir():
            continue

        try:
            text = file.read_text(errors="ignore")
        except Exception:
            continue

        for ip in ip_re.findall(text):
            ips.add(ip)

        for sub in sub_re.findall(text):
            subs.add(sub.lower().strip("."))

        for cve in cve_re.findall(text):
            cves.add(cve.upper())

        for line in text.splitlines():
            line_ips = ip_re.findall(line)
            if not line_ips:
                continue

            parts = re.split(r'[\s,\t]+', line)
            ports = []
            for p in parts:
                if p.isdigit():
                    n = int(p)
                    if 1 <= n <= 65535:
                        ports.append(str(n))

            for ip in line_ips:
                for port in ports[:2]:
                    ip_ports.add(f"{ip}:{port}")

            for keyword in [
                "Jenkins", "Grafana", "Kibana", "MongoDB", "Redis",
                "Elasticsearch", "Kubernetes", "Docker", "nginx",
                "Apache", "OpenSSH", "Tomcat", "GitLab", "Nexus",
                "Artifactory", "WordPress", "Laravel", "SonarQube"
            ]:
                if keyword.lower() in line.lower():
                    products.add(keyword)

    return ips, subs, cves, ip_ports, products

def parse_httpx():
    rows = []
    f = HTTPX_DIR / "httpx.json"
    if not f.exists():
        return rows

    for line in f.read_text(errors="ignore").splitlines():
        try:
            rows.append(json.loads(line))
        except Exception:
            pass
    return rows

def parse_nuclei():
    rows = []
    for f in [NUCLEI_DIR / "nuclei-priority.jsonl", NUCLEI_DIR / "nuclei.jsonl"]:
        if not f.exists():
            continue
        for line in f.read_text(errors="ignore").splitlines():
            try:
                rows.append(json.loads(line))
            except Exception:
                pass
    return rows

def generate_report():
    ips, subs, cves, ip_ports, products = parse_loose_text()
    httpx_rows = parse_httpx()
    nuclei_rows = parse_nuclei()

    live_urls = sorted(set(r.get("url", "") for r in httpx_rows if r.get("url")))

    report = []
    report.append(f"# Shodan Recon Report: {TARGET}\n")

    report.append("## Summary\n")
    report.append(f"- Subdomains found: {len(subs)}")
    report.append(f"- IPs found: {len(ips)}")
    report.append(f"- IP:port pairs found: {len(ip_ports)}")
    report.append(f"- Live HTTP services: {len(live_urls)}")
    report.append(f"- Shodan CVE strings found: {len(cves)}")
    report.append(f"- Nuclei findings: {len(nuclei_rows)}")
    report.append(f"- Products detected: {', '.join(sorted(products)) if products else 'None parsed'}\n")

    report.append("## Top Bug Bounty Leads\n")
    report.append("| Priority | Asset | Source | Evidence | Risk | Confidence | Safe Next Step |")
    report.append("|---:|---|---|---|---|---|---|")

    priority = 1

    for n in nuclei_rows:
        info = n.get("info", {})
        sev = str(info.get("severity", "")).lower()
        if sev in ["critical", "high", "medium"]:
            matched = n.get("matched-at", n.get("host", ""))
            name = info.get("name", n.get("template-id", "nuclei finding"))
            report.append(f"| {priority} | `{matched}` | nuclei | {name} | {sev.upper()} | Medium/High | Verify manually without exploitation |")
            priority += 1

    interesting = ["jenkins", "grafana", "kibana", "gitlab", "nexus", "artifactory", "swagger", "actuator", "admin", "sonarqube"]
    for r in httpx_rows:
        blob = json.dumps(r).lower()
        if any(x in blob for x in interesting):
            url = r.get("url", "")
            title = str(r.get("title", "")).replace("|", " ")
            report.append(f"| {priority} | `{url}` | httpx/shodan | Interesting panel/tech: {title} | Medium | Medium | Visit public page only, confirm auth/version/exposure |")
            priority += 1

    if priority == 1:
        report.append("| 1 | None | parser | No strong leads parsed | Info | Low | Review raw Shodan/httpx manually |")

    report.append("")

    report.append("## Subdomains\n")
    report.append("| Subdomain |")
    report.append("|---|")
    for s in sorted(subs):
        report.append(f"| `{s}` |")
    report.append("")

    report.append("## IPs\n")
    report.append("| IP |")
    report.append("|---|")
    for ip in sorted(ips):
        report.append(f"| `{ip}` |")
    report.append("")

    report.append("## IP:Port Pairs\n")
    report.append("| IP:Port |")
    report.append("|---|")
    for x in sorted(ip_ports):
        report.append(f"| `{x}` |")
    report.append("")

    report.append("## Shodan CVE Matches\n")
    report.append("| CVE | Notes |")
    report.append("|---|---|")
    for cve in sorted(cves):
        report.append(f"| `{cve}` | Shodan-reported only. Validate product/version before claiming. |")
    report.append("")

    report.append("## Live HTTP Services from httpx\n")
    report.append("| URL | Status | Title | Tech | IP/CDN |")
    report.append("|---|---:|---|---|---|")
    for r in httpx_rows:
        url = r.get("url", "")
        status = r.get("status_code", "")
        title = str(r.get("title", "")).replace("|", " ")
        tech = ",".join(r.get("tech", [])) if isinstance(r.get("tech"), list) else str(r.get("tech", ""))
        ip = r.get("host", "") or r.get("a", "")
        cdn = r.get("cdn", "")
        report.append(f"| `{url}` | {status} | {title} | {tech} | {ip} {cdn} |")
    report.append("")

    report.append("## Nuclei Findings\n")
    report.append("| Severity | Template | URL | Matcher/Info |")
    report.append("|---|---|---|---|")
    for n in nuclei_rows:
        info = n.get("info", {})
        sev = info.get("severity", n.get("severity", ""))
        name = info.get("name", "")
        tid = n.get("template-id", "")
        matched = n.get("matched-at", n.get("host", ""))
        matcher = n.get("matcher-name", "")
        label = tid or name
        report.append(f"| {sev} | `{label}` | `{matched}` | {matcher} |")
    report.append("")

    report.append("## Notes\n")
    report.append("- Shodan CVEs are not proof. Confirm actual product/version before reporting.")
    report.append("- Nuclei results need manual verification.")
    report.append("- Do not brute force login panels.")
    report.append("- Do not access private data.")
    report.append("- Confirm scope and ownership before active testing.")
    report.append("")

    (OUT / "report.md").write_text("\n".join(report))

def main():
    ips, subs, cves, ip_ports, products = parse_loose_text()

    write_list(EXTRACTED / "ips.txt", ips)
    write_list(EXTRACTED / "subdomains.txt", subs)
    write_list(EXTRACTED / "cves.txt", cves)
    write_list(EXTRACTED / "ip_ports.txt", ip_ports)
    write_list(EXTRACTED / "products.txt", products)

    urls = set()
    for s in subs:
        urls.add(f"https://{s}")
        urls.add(f"http://{s}")
    write_list(EXTRACTED / "urls.txt", urls)

    if REPORT_MODE:
        generate_report()

if __name__ == "__main__":
    main()
