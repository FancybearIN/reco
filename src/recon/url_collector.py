import shutil
import subprocess
import asyncio
import os
import json
from pathlib import Path
from typing import Iterable, List, Set, Dict, Optional
from urllib.parse import parse_qsl, urlparse

from core.artifacts import append_unique_json_list, read_lines, stable_id, write_lines, should_skip


STATIC_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".svg", ".css", ".woff", ".woff2", 
    ".ttf", ".ico", ".mp4", ".mp3", ".pdf", ".zip", ".exe", ".bin",
    ".out", ".o", ".a", ".so", ".dll", ".dmg", ".iso", ".img", ".gz", ".tgz", ".rar"
}

INTERESTING_KEYWORDS = {
    "login", "auth", "reset", "upload", "admin", "debug", "config", "setup",
    "backup", "v1", "v2", "api", "internal", "dev", "test", "staging", "beta", "uat"
}

def _is_static_junk(url: str) -> bool:
    parsed = urlparse(url)
    path = parsed.path.lower()
    if not path:
        return False
    ext = os.path.splitext(path)[1]
    if ext in STATIC_EXTENSIONS:
        return True
    return False

def _is_interesting(url: str) -> bool:
    if "?" in url:
        return True
    parsed = urlparse(url)
    path = parsed.path.lower()
    if path.endswith(".js"):
        return True
    if "/api/" in path:
        return True
    if any(kw in path for kw in INTERESTING_KEYWORDS):
        return True
    return False

async def _stream_tool_output(tool_name: str, command: List[str], raw_file: Path, shared_urls: Set[str], interesting_urls: Set[str], js_urls: Set[str], timeout: int):
    if shutil.which(command[0]) is None:
        print(f"[-] {tool_name} not installed, skipping.")
        return

    try:
        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL
        )

        with open(raw_file, "w") as f:
            while True:
                line = await process.stdout.readline()
                if not line:
                    break
                url = line.decode().strip()
                if not url:
                    continue
                
                f.write(url + "\n")
                
                # Filter static junk early
                if _is_static_junk(url):
                    continue
                
                if url not in shared_urls:
                    shared_urls.add(url)
                    if _is_interesting(url):
                        interesting_urls.add(url)
                    if urlparse(url).path.lower().endswith(".js"):
                        js_urls.add(url)
        
        try:
            await asyncio.wait_for(process.wait(), timeout=timeout)
        except asyncio.TimeoutExpired:
            print(f"[-] {tool_name} timed out after {timeout} seconds, killing.")
            process.kill()
            
    except Exception as e:
        print(f"[-] Error running {tool_name}: {e}")

async def _collect_parallel(target: str, base_dir: Path, config: Dict):
    urls_dir = base_dir / "urls"
    raw_dir = urls_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    
    shared_urls: Set[str] = set()
    interesting_urls: Set[str] = set()
    js_urls: Set[str] = set()
    
    timeout = config.get("url_collection_timeout", 600)
    gau_threads = str(config.get("gau_threads", 10))
    katana_concurrency = str(config.get("katana_concurrency", 10))
    
    commands = [
        ("gau", ["gau", "--threads", gau_threads, target], raw_dir / "gau.txt"),
        ("waybackurls", ["waybackurls", target], raw_dir / "waybackurls.txt"),
    ]
    
    # Katana needs seeds
    seeds = [target, f"https://{target}", f"http://{target}"]
    # Add alive hosts if any
    alive_file = base_dir / "httpx" / "httpx_alive.txt"
    if alive_file.exists():
        seeds.extend(read_lines(alive_file))
    
    seed_file = urls_dir / "katana_seeds.txt"
    write_lines(seed_file, sorted(set(seeds)))
    
    if shutil.which("katana"):
        commands.append(("katana_passive", ["katana", "-list", str(seed_file), "-passive", "-silent", "-c", katana_concurrency], raw_dir / "katana_passive.txt"))
        commands.append(("katana_active", ["katana", "-list", str(seed_file), "-silent", "-c", katana_concurrency], raw_dir / "katana_active.txt"))

    tasks = [
        _stream_tool_output(name, cmd, rfile, shared_urls, interesting_urls, js_urls, timeout)
        for name, cmd, rfile in commands
    ]
    
    print(f"[*] Starting parallel URL collection for {target} (Timeout: {timeout}s)...")
    await asyncio.gather(*tasks)
    
    return shared_urls, interesting_urls, js_urls

def _extract_params(urls: Iterable[str]) -> List[str]:
    params: Set[str] = set()
    for url in urls:
        parsed = urlparse(url)
        for key, _value in parse_qsl(parsed.query, keep_blank_values=True):
            if key:
                params.add(key)
    return sorted(params)

def collect_urls(target: str, base_dir: Path, config: Optional[Dict] = None):
    config = config or {}
    urls_dir = base_dir / "urls"
    collected_file = urls_dir / "collected_urls.txt"
    
    # Resume mode
    if collected_file.exists() and collected_file.stat().st_size > 0:
        # Check if we are forced
        # We don't have direct access to force here, but should_skip handles it via pipeline
        # Actually, collect_urls is called only if should_skip passed in pipeline.py
        pass

    loop = asyncio.get_event_loop()
    if loop.is_running():
        # This might happen in some environments
        # We'll use a nested event loop or run_coroutine_threadsafe if needed
        # But for now, let's assume we can run it
        all_urls, interesting, js_files = loop.run_until_complete(_collect_parallel(target, base_dir, config))
    else:
        all_urls, interesting, js_files = asyncio.run(_collect_parallel(target, base_dir, config))

    # Scoped filtering
    scoped_urls = []
    for url in all_urls:
        try:
            host = urlparse(url if "://" in url else f"https://{url}").hostname or ""
            if host == target or host.endswith(f".{target}"):
                scoped_urls.append(url)
        except: continue
        
    final_urls = sorted(set(scoped_urls))
    write_lines(collected_file, final_urls)
    write_lines(urls_dir / "interesting_urls.txt", sorted(interesting))
    write_lines(urls_dir / "js_files.txt", sorted(js_files))
    write_lines(urls_dir / "params.txt", _extract_params(final_urls))
    
    print(f"[+] Collected {len(final_urls)} unique scoped URLs ({len(interesting)} interesting, {len(js_files)} JS).")
    return final_urls
