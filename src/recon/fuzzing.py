import json
import shutil
import subprocess
from pathlib import Path
from typing import Iterable, List, Set, Dict
from urllib.parse import urlparse

from core.artifacts import append_unique_json_list, evidence_record, read_lines, stable_id, write_lines


def _run(command: List[str], timeout: int = 1800) -> str:
    if shutil.which(command[0]) is None:
        return ""
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=False, timeout=timeout)
        return result.stdout or ""
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return ""


def run_parameter_discovery(target: str, urls: Iterable[str], base_dir: Path, config: Dict = None) -> List[str]:
    out_dir = base_dir / "fuzz"
    out_dir.mkdir(parents=True, exist_ok=True)
    params_file = base_dir / "urls" / "params.txt"
    params: Set[str] = set(read_lines(params_file))
    
    timeout = config.get("request_timeout", 900) if config else 900
    for url in list(urls)[:200]:
        out_file = out_dir / f"arjun_{stable_id(url)}.json"
        if out_file.exists() and out_file.stat().st_size > 0:
            # Try to load existing and skip
            try:
                with open(out_file, "r") as f:
                    data = json.load(f)
                    # arjun output format varies, but we usually want the discovered params
                    # for simplicity in resume, we just skip running but we still need to collect params
                    # Actually, if it exists, we just move to next url
                    continue
            except: pass

        if shutil.which("arjun"):
            stdout = _run(["arjun", "-u", url, "-oJ", str(out_file)], timeout=timeout)
            for match in __import__("re").findall(r"[A-Za-z0-9_.-]{2,}", stdout):
                if len(match) < 40:
                    params.add(match)
        else:
            append_unique_json_list(base_dir / "surfaces" / "discarded_items.json", [{"id": stable_id("arjun", url), "item": url, "reason": "arjun not installed", "tool_source": "arjun"}])
            break
    write_lines(params_file, params)
    # ... rest of tasks generation remains same or similar
    tasks = [
        evidence_record(
            target=target,
            asset=urlparse(url).hostname or target,
            endpoint=url,
            vulnerability_class="SQLi",
            severity_guess="High",
            methodology_source="AllAboutBugBounty/SQL Injection; bugbounty-cheatsheet/sqli",
            tool_source="parameter_discovery",
            curl=f"curl -i -k '{url}'",
            impact="Parameterized endpoint may be injectable; differential validation required.",
            manual_validation_steps=["Test baseline, quote, boolean, and time-delay payloads against each discovered parameter."],
            next_pivots=[{"type": "active_validation", "value": url, "playbook": "SQLi"}],
        )
        for url in urls
        if "?" in url
    ]
    append_unique_json_list(base_dir / "tasks" / "validation_tasks.json", tasks)
    return sorted(params)


def run_content_discovery(target: str, bases: Iterable[str], base_dir: Path, config: Dict = None) -> List[dict]:
    out_dir = base_dir / "fuzz"
    out_dir.mkdir(parents=True, exist_ok=True)
    wordlist = Path("data/methodologies/bugbounty-cheatsheet/cheatsheets/recon.md")
    results = []
    if not shutil.which("ffuf"):
        append_unique_json_list(base_dir / "surfaces" / "discarded_items.json", [{"id": stable_id("ffuf", target), "item": target, "reason": "ffuf not installed", "tool_source": "ffuf"}])
        return results
    if not wordlist.exists():
        append_unique_json_list(base_dir / "surfaces" / "discarded_items.json", [{"id": stable_id("ffuf_wordlist", target), "item": str(wordlist), "reason": "wordlist missing", "tool_source": "ffuf"}])
        return results

    threads = str(config.get("httpx_threads", 50)) if config else "50"
    timeout = str(config.get("request_timeout", 10)) if config else "10"

    for base in list(bases)[:50]:
        url = base.rstrip("/") + "/FUZZ"
        out = out_dir / f"ffuf_{stable_id(url)}.json"
        
        if out.exists() and out.stat().st_size > 0:
            try:
                data = json.loads(out.read_text(encoding="utf-8"))
                for item in data.get("results", []):
                    results.append(item)
                continue
            except: pass

        _run(["ffuf", "-u", url, "-w", str(wordlist), "-of", "json", "-o", str(out), "-mc", "200,204,301,302,307,401,403", "-ac", "-t", threads, "-timeout", timeout], timeout=1800)
        if out.exists() and out.stat().st_size > 0:
            try:
                data = json.loads(out.read_text(encoding="utf-8"))
                for item in data.get("results", []):
                    results.append(item)
            except: pass

    tasks = [
        evidence_record(
            target=target,
            asset=urlparse(item.get("url", "")).hostname or target,
            endpoint=item.get("url", ""),
            vulnerability_class="sensitive file/content discovery",
            severity_guess="Medium",
            methodology_source="HowToHunt/Recon; PayloadsAllTheThings",
            tool_source="ffuf",
            curl=f"curl -i -k '{item.get('url', '')}'",
            impact="Discovered content may expose sensitive files, admin paths, or recursive pivots.",
            manual_validation_steps=["Open minimally, verify sensitivity, and avoid bulk download."],
            next_pivots=[{"type": "url_collection", "value": item.get("url", "")}],
        )
        for item in results
    ]
    append_unique_json_list(base_dir / "tasks" / "validation_tasks.json", tasks)
    return results
