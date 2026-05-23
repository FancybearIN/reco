#!/usr/bin/env python3
"""Rank subdomains by presence of high‑value keywords.

Input: a file (one subdomain per line) – default path
       target-research/urls/raw/subdomains.txt
Output: ranked list written to target-research/urls/processed/interesting-subdomains.txt
"""
import sys, os, pathlib, re

BASE = pathlib.Path(__file__).resolve().parents[3] / "target-research"
RAW = BASE / "urls" / "raw" / "subdomains.txt"
OUT = BASE / "urls" / "processed" / "interesting-subdomains.txt"
KEYWORDS = [
    "admin", "api", "app", "auth", "sso", "oauth", "saml", "login", "dashboard",
    "console", "portal", "internal", "dev", "staging", "test", "qa", "uat", "beta",
    "demo", "sandbox", "old", "legacy", "backup", "cdn", "assets", "static",
    "files", "upload", "download", "media", "docs", "developer", "support",
    "billing", "payments", "invoice", "webhook", "hooks", "graphql", "mobile",
    "partner", "staff", "employee", "jira", "gitlab", "jenkins", "grafana",
    "kibana", "prometheus", "status"
]

def score(domain: str) -> int:
    return sum(1 for kw in KEYWORDS if kw in domain.lower())

def main():
    if not RAW.is_file():
        sys.stderr.write(f"[!] Subdomain list not found: {RAW}\n")
        sys.exit(1)
    domains = [d.strip() for d in RAW.read_text().splitlines() if d.strip()]
    ranked = sorted(domains, key=score, reverse=True)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(ranked) + "\n")
    print(f"[+] Ranked {len(ranked)} subdomains → {OUT}")

if __name__ == "__main__":
    main()
