import json
from pathlib import Path
from typing import Dict, List
from urllib.parse import urlparse

from core.artifacts import append_unique_json_list, stable_id, write_json
from recon.recon_chain import classify_httpx_result


def _load_httpx(target: str, base_dir: Path) -> List[Dict]:
    path = base_dir / "httpx" / "httpx_full.jsonl"
    results = []
    if not path.exists():
        return results
    with open(path, "r", encoding="utf-8", errors="ignore") as handle:
        for line in handle:
            try:
                results.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return results


def classify_surface(target: str, urls: list, apis: list, base_dir: Path):
    print(f"[*] Classifying Attack Surface for {target}...")
    surfaces = []
    for item in _load_httpx(target, base_dir):
        surfaces.extend(classify_httpx_result(target, item))

    for url in urls:
        low = url.lower()
        category = "unknown"
        if any(x in low for x in ["login", "auth", "signin", "sso"]):
            category = "login/auth"
        elif url in apis or "/api/" in low:
            category = "APIs"
        elif "admin" in low:
            category = "admin panels"
        elif "upload" in low or "import" in low:
            category = "file upload surfaces"
        elif "graphql" in low or "swagger" in low or "openapi" in low:
            category = "swagger/openapi/graphql"
        elif "redirect" in low or "callback" in low:
            category = "redirect/callback surfaces"
        elif urlparse(url).path.endswith(".js"):
            category = "JS"
        surfaces.append(
            {
                "id": stable_id("url", category, url),
                "target": target,
                "asset": urlparse(url).hostname or target,
                "endpoint": url,
                "category": category,
                "tool_source": "url_collector",
            }
        )

    grouped: Dict[str, List[str]] = {}
    for surface in surfaces:
        grouped.setdefault(surface["category"], []).append(surface["endpoint"])

    append_unique_json_list(base_dir / "surfaces" / "attack_surfaces.json", surfaces)
    write_json(base_dir / "recon" / "classified_surface.json", grouped)
    return grouped
