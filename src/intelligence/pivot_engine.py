from pathlib import Path
from typing import Dict, Iterable, List

from core.artifacts import append_unique_json_list, load_json, stable_id, write_json


def enqueue_pivots(base_dir: Path, items: Iterable[Dict]) -> List[Dict]:
    queued = []
    for item in items:
        for pivot in item.get("next_pivots", []) or []:
            if not pivot.get("value"):
                continue
            queued.append(
                {
                    "id": stable_id(pivot.get("type"), pivot.get("value"), pivot.get("playbook"), pivot.get("template")),
                    "type": pivot.get("type"),
                    "value": pivot.get("value"),
                    "playbook": pivot.get("playbook"),
                    "template": pivot.get("template"),
                    "source_task": item.get("id"),
                    "status": "QUEUED",
                }
            )
    return append_unique_json_list(base_dir / "tasks" / "pivot_queue.json", queued)


def mark_pivot_processed(base_dir: Path, pivot_id: str) -> None:
    path = base_dir / "tasks" / "pivot_queue.json"
    queue = load_json(path, [])
    for pivot in queue:
        if pivot.get("id") == pivot_id:
            pivot["status"] = "PROCESSED"
    write_json(path, queue)
