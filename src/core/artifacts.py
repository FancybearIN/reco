import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


EVIDENCE_FIELDS = {
    "target": "",
    "asset": "",
    "endpoint": "",
    "vulnerability_class": "",
    "severity_guess": "",
    "methodology_source": "",
    "tool_source": "",
    "request": "",
    "response": "",
    "curl": "",
    "proof": "",
    "impact": "",
    "false_positive_checks": [],
    "manual_validation_steps": [],
    "next_pivots": [],
    "status": "CANDIDATE",
}


def ensure_run_dirs(base_dir: Path) -> None:
    for name in [
        "recon",
        "httpx",
        "urls",
        "js",
        "api",
        "fuzz",
        "exposure",
        "nuclei",
        "surfaces",
        "tasks",
        "findings",
        "reports",
        "logs",
        "manual_queries",
        "imports",
        "playbooks",
    ]:
        (base_dir / name).mkdir(parents=True, exist_ok=True)


def read_lines(path: Path) -> List[str]:
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8", errors="ignore") as handle:
        return [line.strip() for line in handle if line.strip()]


def write_lines(path: Path, lines: Iterable[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    unique = sorted({line.strip() for line in lines if str(line).strip()})
    with open(path, "w", encoding="utf-8") as handle:
        for line in unique:
            handle.write(f"{line}\n")


def append_jsonl(path: Path, item: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(item, sort_keys=True) + "\n")


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2, sort_keys=True)


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    with open(path, "r", encoding="utf-8", errors="ignore") as handle:
        return json.load(handle)


def stable_id(*parts: Any) -> str:
    raw = "|".join(str(part) for part in parts if part is not None)
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def record_command(base_dir: Path, tool: str, command: List[str], input_file: str = "", output_file: str = "", exit_code: int = 0, error: str = "", start_time: str = "", end_time: str = ""):
    manifest_path = base_dir / "run_manifest.jsonl"
    entry = {
        "tool": tool,
        "command": " ".join(command),
        "input_file": str(input_file),
        "output_file": str(output_file),
        "start_time": start_time,
        "end_time": end_time or now_iso(),
        "exit_code": exit_code,
        "error": error
    }
    append_jsonl(manifest_path, entry)


def should_skip(output_path: Path, force: bool = False) -> bool:
    if force:
        print(f"[*] RE-RUN due to --force: {output_path.name}")
        return False
    if output_path.exists() and output_path.stat().st_size > 0:
        print(f"[*] SKIPPED existing output: {output_path.name}")
        return True
    return False


def evidence_record(**kwargs: Any) -> Dict[str, Any]:
    record = dict(EVIDENCE_FIELDS)
    record.update(kwargs)
    record.setdefault("false_positive_checks", [])
    record.setdefault("manual_validation_steps", [])
    record.setdefault("next_pivots", [])
    if "id" not in record:
        record["id"] = stable_id(
            record.get("target"),
            record.get("asset"),
            record.get("endpoint"),
            record.get("vulnerability_class"),
            record.get("tool_source"),
        )
    record["created_at"] = record.get("created_at") or now_iso()
    return record

class ScopeGuard:
    def __init__(self, target: str, scope: List[str], base_dir: Path, allow_out_of_scope: bool = False):
        self.target = target
        self.scope_domains = {s.strip().lower().lstrip("*.") for s in scope if s.strip()}
        self.base_dir = base_dir
        self.allow_out_of_scope = allow_out_of_scope
        self.blocked_path = base_dir / "scope" / "blocked_out_of_scope.txt"

    def is_in_scope(self, asset: str) -> bool:
        if self.allow_out_of_scope:
            return True
        
        from urllib.parse import urlparse
        parsed = urlparse(asset if "://" in asset else f"https://{asset}")
        hostname = (parsed.hostname or asset).lower().lstrip(".")
        
        # Check root domain or subdomain
        in_scope = hostname == self.target or hostname.endswith(f".{self.target}")
        
        if not in_scope:
            # Check against explicit scope domains
            for s in self.scope_domains:
                if hostname == s or hostname.endswith(f".{s}"):
                    in_scope = True
                    break
        
        if not in_scope:
            self.blocked_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.blocked_path, "a") as f:
                f.write(f"{asset}\n")
        return in_scope

    def filter(self, assets: Iterable[str]) -> List[str]:
        return [a for s in assets if (a := s.strip()) and self.is_in_scope(a)]


def append_unique_json_list(path: Path, items: Iterable[Dict[str, Any]], key: Optional[str] = "id") -> List[Dict[str, Any]]:
    existing = load_json(path, [])
    if not isinstance(existing, list):
        existing = []
    merged = list(existing)
    seen = set()
    for item in merged:
        if key and item.get(key):
            seen.add(item[key])
        else:
            seen.add(json.dumps(item, sort_keys=True))
    for item in items:
        marker = item.get(key) if key and item.get(key) else json.dumps(item, sort_keys=True)
        if marker in seen:
            continue
        seen.add(marker)
        merged.append(item)
    write_json(path, merged)
    return merged
