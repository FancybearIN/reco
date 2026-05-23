import json
import shutil
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List
from urllib.parse import urlparse

from core.artifacts import append_unique_json_list, evidence_record, read_lines, stable_id


def run_nuclei_on_alive(target: str, base_dir: Path, config: Dict = None) -> Path:
    alive = base_dir / "httpx" / "httpx_alive.txt"
    output = base_dir / "nuclei" / "nuclei_results.jsonl"
    output.parent.mkdir(parents=True, exist_ok=True)
    if not read_lines(alive):
        append_unique_json_list(
            base_dir / "surfaces" / "discarded_items.json",
            [{"id": stable_id("nuclei", target, "no_alive_hosts"), "item": str(alive), "reason": "no live hosts for nuclei", "tool_source": "nuclei"}],
        )
        return output
    if shutil.which("nuclei") is None:
        append_unique_json_list(
            base_dir / "surfaces" / "discarded_items.json",
            [{"id": stable_id("nuclei", target, "missing"), "item": "nuclei", "reason": "tool not installed", "tool_source": "nuclei"}],
        )
        return output
    
    rate = str(config.get("nuclei_rate_limit", 150)) if config else "150"
    try:
        subprocess.run(
            ["nuclei", "-l", str(alive), "-silent", "-jsonl", "-o", str(output), "-rl", rate],
            capture_output=True,
            text=True,
            check=False,
            timeout=3600,
        )
    except subprocess.TimeoutExpired:
        append_unique_json_list(
            base_dir / "surfaces" / "discarded_items.json",
            [{"id": stable_id("nuclei", target, "timeout"), "item": str(alive), "reason": "nuclei timed out", "tool_source": "nuclei"}],
        )
    return output


def parse_nuclei_results(target: str, base_dir: Path, paths: Iterable[Path] = None) -> List[Dict]:
    nuclei_dir = base_dir / "nuclei"
    result_paths = list(paths or nuclei_dir.glob("*.jsonl"))
    tasks = []
    for path in result_paths:
        if not path.exists():
            continue
        with open(path, "r", encoding="utf-8", errors="ignore") as handle:
            for line in handle:
                try:
                    item = json.loads(line)
                except json.JSONDecodeError:
                    continue
                matched = item.get("matched-at") or item.get("host") or item.get("url") or ""
                info = item.get("info") or {}
                name = info.get("name") or item.get("template-id") or "nuclei finding"
                severity = str(info.get("severity") or "info").title()
                task = evidence_record(
                    id=stable_id("nuclei", path, matched, item.get("template-id")),
                    target=target,
                    asset=urlparse(matched).hostname or target,
                    endpoint=matched,
                    vulnerability_class=name,
                    severity_guess=severity,
                    methodology_source="nuclei-template/manual-validation-required",
                    tool_source=f"nuclei:{item.get('template-id', 'unknown')}",
                    request="",
                    response=json.dumps(item, sort_keys=True)[:4000],
                    curl=f"curl -i -k '{matched}'" if matched else "",
                    proof="Nuclei signal only; manual validation required before report.",
                    impact=info.get("description") or "Potential issue detected by nuclei; validate exploitability and impact manually.",
                    false_positive_checks=["Reproduce manually without relying on nuclei output.", "Confirm business/security impact."],
                    manual_validation_steps=[
                        "Replay the affected endpoint manually.",
                        "Follow the referenced template logic and capture request/response proof.",
                        "Do not mark reportable until manual validation is completed.",
                    ],
                    next_pivots=[{"type": "active_validation", "value": matched, "template": item.get("template-id")}],
                    status="CANDIDATE",
                )
                tasks.append(task)
    append_unique_json_list(base_dir / "tasks" / "validation_tasks.json", tasks)
    append_unique_json_list(base_dir / "findings" / "candidates.json", tasks)
    return tasks
