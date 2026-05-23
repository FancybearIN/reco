import base64
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List
from urllib.parse import urlparse

from core.artifacts import append_unique_json_list, evidence_record, stable_id, write_json


def _request_to_curl(raw: str, fallback_url: str = "") -> str:
    lines = raw.replace("\r\n", "\n").split("\n")
    if not lines:
        return ""
    first = lines[0].split()
    method = first[0] if first else "GET"
    path = first[1] if len(first) > 1 else "/"
    host = ""
    headers = []
    body_index = None
    for idx, line in enumerate(lines[1:], start=1):
        if line == "":
            body_index = idx + 1
            break
        if line.lower().startswith("host:"):
            host = line.split(":", 1)[1].strip()
        elif ":" in line:
            headers.append(line)
    scheme = "https" if fallback_url.startswith("https://") else "http"
    url = fallback_url or f"{scheme}://{host}{path}"
    parts = ["curl", "-i", "-k", "-X", method]
    for header in headers:
        parts.extend(["-H", f"'{header}'"])
    body = "\n".join(lines[body_index:]) if body_index is not None else ""
    if body.strip():
        parts.extend(["--data-binary", repr(body)])
    parts.append(f"'{url}'")
    return " ".join(parts)


def import_raw_request(target: str, base_dir: Path, request_path: Path) -> Dict:
    raw = request_path.read_text(encoding="utf-8", errors="ignore")
    curl = _request_to_curl(raw)
    endpoint = curl.split("'")[-2] if "'" in curl else ""
    task = evidence_record(
        id=stable_id("raw_request", request_path),
        target=target,
        asset=urlparse(endpoint).hostname or target,
        endpoint=endpoint,
        vulnerability_class="manual imported request",
        severity_guess="Medium",
        methodology_source="Burp/CLI bridge",
        tool_source="raw_http_request",
        request=raw,
        curl=curl,
        impact="Imported request requires classification and active validation.",
        manual_validation_steps=["Replay request.", "Classify parameters and auth sensitivity.", "Run matching playbook."],
        next_pivots=[{"type": "parameter_discovery", "value": endpoint}],
    )
    append_unique_json_list(base_dir / "tasks" / "validation_tasks.json", [task])
    return task


def import_burp_xml(target: str, base_dir: Path, xml_path: Path) -> List[Dict]:
    root = ET.parse(xml_path).getroot()
    tasks = []
    inventory = []
    for item in root.findall(".//item"):
        url = (item.findtext("url") or "").strip()
        request_node = item.find("request")
        raw = ""
        if request_node is not None and request_node.text:
            raw = request_node.text
            if request_node.attrib.get("base64", "").lower() == "true":
                raw = base64.b64decode(raw).decode("utf-8", errors="ignore")
        curl = _request_to_curl(raw, url) if raw else f"curl -i -k '{url}'"
        params = sorted(set(re.findall(r"[?&]([A-Za-z0-9_.-]+)=", url)))
        inventory.append({"url": url, "params": params, "method": (raw.split() or ["GET"])[0]})
        task = evidence_record(
            id=stable_id("burp", xml_path, url, raw[:80]),
            target=target,
            asset=urlparse(url).hostname or target,
            endpoint=url,
            vulnerability_class="auth-sensitive candidate" if "authorization:" in raw.lower() or "cookie:" in raw.lower() else "manual imported request",
            severity_guess="Medium",
            methodology_source="Burp sitemap/history import",
            tool_source="burp_bridge",
            request=raw,
            curl=curl,
            impact="Imported Burp request may expose auth-sensitive parameters or workflows.",
            manual_validation_steps=["Replay with account matrix.", "Swap object IDs and remove auth.", "Classify response differences."],
            next_pivots=[{"type": "api_auth_matrix", "value": url}],
        )
        tasks.append(task)
    write_json(base_dir / "imports" / f"{xml_path.stem}_inventory.json", inventory)
    append_unique_json_list(base_dir / "tasks" / "validation_tasks.json", tasks)
    return tasks
