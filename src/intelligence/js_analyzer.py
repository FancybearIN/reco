import json
import re
from pathlib import Path
from typing import Dict, Iterable, List, Set
from urllib.parse import urljoin, urlparse

import requests

from core.artifacts import append_unique_json_list, evidence_record, stable_id, write_json, write_lines


SECRET_PATTERNS = {
    "aws_access_key_id": r"\bAKIA[0-9A-Z]{16}\b",
    "google_api_key": r"\bAIza[0-9A-Za-z_\-]{35}\b",
    "github_token": r"\bgh[pousr]_[A-Za-z0-9_]{36,255}\b",
    "slack_token": r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b",
    "stripe_live_key": r"\bsk_live_[0-9a-zA-Z]{20,}\b",
    "firebase_url": r"https://[a-zA-Z0-9-]+\.firebaseio\.com",
    "generic_api_key_assignment": r"(?i)(api[_-]?key|secret|token|client[_-]?secret)\s*[:=]\s*['\"][^'\"\s]{12,}['\"]",
}

ENDPOINT_RE = re.compile(r"(?P<quote>['\"])(?P<value>(?:https?://[^'\"]+|/[A-Za-z0-9_\-./?=&%{}:]+))(?P=quote)")


def _scoped(url: str, target: str) -> bool:
    host = urlparse(url if "://" in url else f"https://{url}").hostname or ""
    return host == target or host.endswith(f".{target}") or not host


def _js_urls(target: str, urls: Iterable[str], base_dir: Path) -> List[str]:
    found: Set[str] = {url for url in urls if ".js" in urlparse(url).path.lower()}
    for item in base_dir.glob("httpx/httpx_full.jsonl"):
        with open(item, "r", encoding="utf-8", errors="ignore") as handle:
            for line in handle:
                if ".js" in line:
                    try:
                        data = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    candidate = data.get("url") or data.get("input")
                    if candidate and ".js" in urlparse(candidate).path.lower():
                        found.add(candidate)
    return sorted(url for url in found if _scoped(url, target))


def _download_js(url: str) -> str:
    try:
        response = requests.get(url, timeout=12, headers={"User-Agent": "reco-js-analyzer/1.0"})
    except requests.RequestException:
        return ""
    content_type = response.headers.get("content-type", "")
    if response.status_code >= 400 or len(response.content) > 3_000_000:
        return ""
    if "javascript" not in content_type and not urlparse(url).path.lower().endswith(".js"):
        return ""
    return response.text


def _extract_endpoints(js_url: str, content: str, target: str) -> List[str]:
    endpoints = set()
    for match in ENDPOINT_RE.finditer(content):
        value = match.group("value")
        if value.startswith("//"):
            value = f"https:{value}"
        absolute = value if value.startswith("http") else urljoin(js_url, value)
        if _scoped(absolute, target):
            endpoints.add(absolute)
    return sorted(endpoints)


def _extract_secrets(js_url: str, content: str) -> List[Dict]:
    secrets = []
    for name, pattern in SECRET_PATTERNS.items():
        for match in re.finditer(pattern, content):
            value = match.group(0)
            secrets.append(
                {
                    "id": stable_id(js_url, name, value),
                    "type": name,
                    "source": js_url,
                    "match": value[:8] + "***" + value[-4:] if len(value) > 16 else value,
                    "validation_source": "keyhacks",
                    "status": "CANDIDATE",
                }
            )
    return secrets


def analyze_js(target: str, urls: list, base_dir: Path):
    print(f"[*] Analyzing JS for {target}...")
    js_dir = base_dir / "js"
    js_dir.mkdir(parents=True, exist_ok=True)
    js_urls = _js_urls(target, urls, base_dir)
    endpoints: Set[str] = set()
    secrets: List[Dict] = []

    for js_url in js_urls[:500]:
        content = _download_js(js_url)
        if not content:
            continue
        endpoints.update(_extract_endpoints(js_url, content, target))
        secrets.extend(_extract_secrets(js_url, content))

    write_lines(js_dir / "js_files.txt", js_urls)
    write_lines(js_dir / "endpoints.txt", endpoints)
    write_json(js_dir / "secrets_candidates.json", secrets)

    tasks = []
    for endpoint in endpoints:
        vuln_class = "Swagger/OpenAPI/GraphQL abuse" if any(x in endpoint.lower() for x in ["swagger", "openapi", "graphql"]) else "IDOR/BOLA/API authz"
        tasks.append(
            evidence_record(
                target=target,
                asset=urlparse(endpoint).hostname or target,
                endpoint=endpoint,
                vulnerability_class=vuln_class,
                severity_guess="Medium",
                methodology_source="awesome-oneliner-bugbounty/HowToHunt",
                tool_source="js_analyzer",
                curl=f"curl -i -k {endpoint}",
                impact=f"JavaScript-discovered endpoint may expose {vuln_class} risk.",
                manual_validation_steps=["Replay endpoint with auth matrix and compare unauthenticated/account responses."],
                next_pivots=[{"type": "parameter_discovery", "value": endpoint}],
            )
        )
    for secret in secrets:
        tasks.append(
            evidence_record(
                target=target,
                asset=urlparse(secret["source"]).hostname or target,
                endpoint=secret["source"],
                vulnerability_class="exposed secrets",
                severity_guess="High",
                methodology_source="keyhacks",
                tool_source="js_analyzer",
                proof=f"{secret['type']} pattern matched in JavaScript",
                impact="Potential credential or API key exposure; validate scope and permissions with KeyHacks-safe checks.",
                manual_validation_steps=[
                    "Identify key provider from pattern.",
                    "Run the matching read-only KeyHacks validation request.",
                    "Capture scopes/permissions without modifying data.",
                ],
                next_pivots=[{"type": "keyhacks_validation", "value": secret["id"]}],
            )
        )
    append_unique_json_list(base_dir / "tasks" / "validation_tasks.json", tasks)
    return {"js_urls": js_urls, "endpoints": sorted(endpoints), "secrets": secrets}
