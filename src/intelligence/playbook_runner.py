import requests
from pathlib import Path
from urllib.parse import urlparse

from core.artifacts import append_unique_json_list, evidence_record, write_json


PLAYBOOKS = {
    "CORS misconfiguration": {
        "steps": ["Send baseline request.", "Send request with Origin: https://evil.example.", "Confirm ACAO reflects origin and ACAC permits credentials before impact claim."],
        "checks": ["No report unless sensitive response is readable cross-origin.", "Verify wildcard without credentials is lower impact."],
    },
    "SQLi": {
        "steps": ["Identify injectable parameters.", "Compare baseline, quote, boolean, and time-delay probes.", "Use sqlmap only as supporting evidence after manual differential signal."],
        "checks": ["Confirm changes are parameter-specific.", "Avoid reporting generic 500s without SQL error or timing proof."],
    },
    "SSRF": {
        "steps": ["Find URL-like parameters.", "Use controlled collaborator/OOB endpoint.", "Try metadata IP only when program rules allow.", "Capture callback or internal-only response differential."],
        "checks": ["Rule out client-side fetches.", "Confirm server-side source via OOB logs or response evidence."],
    },
    "IDOR/BOLA/API authz": {
        "steps": ["Replay with account A.", "Replay with account B.", "Replay unauthenticated.", "Swap object IDs.", "Compare status, length, and sensitive fields."],
        "checks": ["Confirm ownership of both objects.", "Verify data is not public."],
    },
    "cache poisoning": {
        "steps": ["Identify cache headers and keys.", "Probe unkeyed headers/params safely.", "Confirm separate victim request receives poisoned benign marker."],
        "checks": ["Use harmless marker only.", "Confirm cache hit evidence."],
    },
    "HTTP request smuggling/desync": {
        "steps": ["Check front/back proxy indicators.", "Use safe timing probes.", "Escalate only with isolated benign prefix tests."],
        "checks": ["No destructive queue poisoning.", "Require reproducible timing or response-queue proof."],
    },
    "subdomain takeover": {
        "steps": ["Confirm dangling CNAME.", "Match provider fingerprint.", "Check provider claimability manually.", "Capture NXDOMAIN/service-not-found proof."],
        "checks": ["Do not claim without provider-specific dangling proof.", "Verify subdomain remains in scope."],
    },
    "broken-link hijacking": {
        "steps": ["Extract external links from pages/JS.", "Identify dead social/SaaS links.", "Check account/resource claimability without impersonation."],
        "checks": ["Confirm link is reachable from in-scope asset.", "Avoid taking over brand accounts."],
    },
    "exposed secrets": {
        "steps": ["Classify secret provider.", "Run read-only KeyHacks validation.", "Capture scopes/identity.", "Do not modify resources."],
        "checks": ["Verify key is not a test key.", "Verify source is in scope."],
    },
    "Swagger/OpenAPI/GraphQL abuse": {
        "steps": ["Fetch schema/spec.", "Enumerate routes/operations.", "Run auth matrix per operation.", "Check introspection and GraphQL batching/alias abuse."],
        "checks": ["Do not report public docs alone.", "Require sensitive operation/data impact."],
    },
    "upload abuse": {
        "steps": ["Identify accepted file types.", "Test benign polyglot/extension bypasses.", "Check storage location and execution/rendering context.", "Try SVG/metadata only within rules."],
        "checks": ["No webshell upload against third-party systems.", "Require executable/rendered impact or policy bypass."],
    },
    "OAuth redirect/callback abuse": {
        "steps": ["Locate redirect_uri/next/return parameters.", "Test strict allowlist and path confusion.", "Check token/code leakage to attacker-controlled redirect."],
        "checks": ["Require actual code/token leakage or account impact.", "Confirm state/PKCE behavior."],
    },
    "RCE/CVE exploitability validation": {
        "steps": ["Map exact product and version.", "Find matching CVE/template.", "Use harmless version or read-only proof endpoint.", "Capture deterministic exploitability evidence."],
        "checks": ["No report from fingerprint alone.", "Confirm target version and reachable vulnerable path."],
    },
    "WAF bypass retry strategy": {
        "steps": ["Record WAF/CDN fingerprint.", "Retry validation with method/header/path encoding variants.", "Compare block vs origin behavior."],
        "checks": ["Avoid rate-limit abuse.", "Require the underlying vuln proof, not just bypass."],
    },
    "sensitive file/content discovery": {
        "steps": ["Probe common sensitive paths.", "Confirm status/content length.", "Capture only minimal proof of sensitive content."],
        "checks": ["Avoid downloading bulk data.", "Verify content is not intentionally public."],
    },
    "admin panel exposure": {
        "steps": ["Fingerprint product/version.", "Check default paths and auth requirements.", "Search known CVEs/default credential policy without login spraying."],
        "checks": ["Panel exposure alone may be informational.", "Require weak auth, sensitive unauth access, or vulnerable version."],
    },
    "cloud metadata exposure": {
        "steps": ["Identify SSRF-capable inputs or direct metadata exposure.", "Probe metadata endpoints only through safe controlled paths.", "Capture role name/token metadata only when allowed."],
        "checks": ["Do not use cloud credentials to modify resources.", "Confirm server-side access path."],
    },
}

def _fetch_baseline(url: str) -> tuple:
    try:
        if not url.startswith('http'):
            url = f"https://{url}"
        response = requests.get(url, timeout=10, verify=False, allow_redirects=False)
        req_line = f"GET {url} HTTP/1.1\nHost: {urlparse(url).hostname}\n"
        resp_headers = "\n".join([f"{k}: {v}" for k, v in response.headers.items()])
        resp_proof = f"HTTP/1.1 {response.status_code} {response.reason}\n{resp_headers}\n\n{response.text[:1000]}"
        return req_line, resp_proof
    except requests.RequestException:
        return "", ""

def run_playbooks(target: str, hypotheses: list, base_dir: Path):
    print(f"[*] Building validation playbook tasks for {target}...")
    candidates = []
    
    # Optional: disable insecure request warnings for baseline collection
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    for hypothesis in hypotheses:
        endpoint = hypothesis["endpoint"]
        vuln_class = hypothesis["type"]
        playbook = PLAYBOOKS.get(vuln_class, PLAYBOOKS["sensitive file/content discovery"])
        
        req, resp = _fetch_baseline(endpoint)
        
        candidate = evidence_record(
            target=target,
            asset=urlparse(endpoint).hostname or target,
            endpoint=endpoint,
            vulnerability_class=vuln_class,
            finding_type=vuln_class,
            severity_guess="Medium",
            methodology_source=hypothesis.get("methodology_source", "local methodology corpus"),
            tool_source="hypothesis_engine",
            request=req,
            response=resp,
            curl=f"curl -i -k '{endpoint}'",
            proof=resp[:500] if resp else "",
            impact=f"Potential {vuln_class}; active validation required.",
            false_positive_checks=playbook["checks"],
            manual_validation_steps=playbook["steps"],
            next_pivots=[{"type": "active_validation", "value": endpoint, "playbook": vuln_class}],
            status="CANDIDATE",
            state="CANDIDATE",
        )
        candidates.append(candidate)
    append_unique_json_list(base_dir / "tasks" / "validation_tasks.json", candidates)
    append_unique_json_list(base_dir / "findings" / "candidates.json", candidates)
    write_json(base_dir / "playbooks" / "active_playbooks.json", PLAYBOOKS)
    return candidates
