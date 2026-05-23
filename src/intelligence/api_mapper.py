import json
import re
from pathlib import Path
from typing import Dict, Iterable, List
from urllib.parse import urlparse

import requests
import yaml

from core.artifacts import append_unique_json_list, evidence_record, stable_id, write_json, write_lines


API_HINTS = ("/api/", "api.", ".json", "/graphql", "/openapi", "/swagger")
PLACEHOLDER_MARKERS = ("REDACTED", "TOKEN_A", "TOKEN_B", "KEY")


def _is_api(url: str) -> bool:
    low = url.lower()
    return any(hint in low for hint in API_HINTS)


def _load_session() -> Dict:
    path = Path("config/session.yaml")
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8", errors="ignore") as handle:
        return yaml.safe_load(handle) or {}


def _auth_headers(account_name: str, account: Dict) -> Dict[str, str]:
    token = str(account.get("token") or "")
    if token and not any(marker in token for marker in PLACEHOLDER_MARKERS):
        return {"Authorization": f"Bearer {token}"}
    headers = account.get("headers")
    if isinstance(headers, dict):
        return {str(k): str(v) for k, v in headers.items() if v and not any(marker in str(v) for marker in PLACEHOLDER_MARKERS)}
    return {}


def _curl(url: str, headers: Dict[str, str]) -> str:
    parts = ["curl", "-i", "-k"]
    for key, value in headers.items():
        parts.extend(["-H", f"'{key}: {value}'"])
    parts.append(f"'{url}'")
    return " ".join(parts)


def _object_id_variants(url: str, account_a: Dict, account_b: Dict) -> List[str]:
    a_id = str(account_a.get("id") or "")
    b_id = str(account_b.get("id") or "")
    if not a_id or not b_id or a_id == b_id:
        return []
    return [re.sub(rf"(?<!\d){re.escape(a_id)}(?!\d)", b_id, url)]


def _probe_auth_matrix(url: str, accounts: Dict) -> List[Dict]:
    probes = []
    variants = {
        "unauthenticated": {},
        "account_a": _auth_headers("account_a", accounts.get("account_a", {})),
        "account_b": _auth_headers("account_b", accounts.get("account_b", {})),
        "low_privilege": _auth_headers("low_privilege", accounts.get("low_privilege", {})),
        "high_privilege": _auth_headers("high_privilege", accounts.get("high_privilege", {})),
    }
    for name, headers in variants.items():
        if name != "unauthenticated" and not headers:
            probes.append({"account": name, "status": "SKIPPED", "reason": "credentials not configured"})
            continue
        try:
            response = requests.get(url, headers=headers, timeout=10)
            probes.append(
                {
                    "account": name,
                    "status_code": response.status_code,
                    "length": len(response.content),
                    "content_type": response.headers.get("content-type", ""),
                    "curl": _curl(url, headers),
                }
            )
        except requests.RequestException as exc:
            probes.append({"account": name, "status": "ERROR", "reason": str(exc)[:160]})
    return probes


def generate_auth_matrix_tasks(target: str, apis: Iterable[str], base_dir: Path, run_live: bool = False) -> List[Dict]:
    session = _load_session()
    accounts = session.get("accounts", {})
    tasks = []
    matrix_results = []
    for api in sorted(set(apis)):
        account_a = accounts.get("account_a", {})
        account_b = accounts.get("account_b", {})
        variants = [api] + _object_id_variants(api, account_a, account_b)
        for endpoint in sorted(set(variants)):
            headers_a = _auth_headers("account_a", account_a)
            steps = [
                "Replay with account A.",
                "Replay with account B.",
                "Replay unauthenticated.",
                "Swap object IDs between account A and B where present.",
                "Compare status code, body length, and sensitive fields.",
                "Mark reportable only on confirmed cross-account or unauthenticated data access.",
            ]
            task = evidence_record(
                target=target,
                asset=urlparse(endpoint).hostname or target,
                endpoint=endpoint,
                vulnerability_class="IDOR/BOLA/API authz",
                severity_guess="High",
                methodology_source="HowToHunt/IDOR",
                tool_source="api_mapper",
                curl=_curl(endpoint, headers_a),
                impact="Potential authorization bypass or object-level data exposure.",
                false_positive_checks=[
                    "Verify the object belongs to a different account.",
                    "Verify differences are not public or cache artifacts.",
                ],
                manual_validation_steps=steps,
                next_pivots=[{"type": "parameter_discovery", "value": endpoint}],
            )
            tasks.append(task)
            if run_live:
                matrix_results.append({"endpoint": endpoint, "results": _probe_auth_matrix(endpoint, accounts)})
    append_unique_json_list(base_dir / "tasks" / "validation_tasks.json", tasks)
    if matrix_results:
        write_json(base_dir / "api" / "auth_matrix_results.json", matrix_results)
    return tasks


def map_apis(target: str, urls: list, js_data: dict, base_dir: Path):
    print(f"[*] Mapping APIs for {target}...")
    api_dir = base_dir / "api"
    api_dir.mkdir(parents=True, exist_ok=True)
    apis = set(url for url in urls if _is_api(url))
    apis.update(endpoint for endpoint in js_data.get("endpoints", []) if _is_api(endpoint))
    write_lines(api_dir / "api_endpoints.txt", apis)
    generate_auth_matrix_tasks(target, apis, base_dir, run_live=False)
    return sorted(apis)
