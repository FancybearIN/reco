import json
import re
import shutil
import subprocess
from collections import Counter
from pathlib import Path
from typing import Dict, Iterable, List, Tuple
from urllib.parse import urlparse

from core.artifacts import (
    append_unique_json_list,
    ensure_run_dirs,
    evidence_record,
    read_lines,
    stable_id,
    write_json,
    write_lines,
)

SUBDOMAIN_MASTER = Path("scripts/recon/subdomain_master.sh")

COMMON_WEB_PORTS = [
    80,
    443,
    8080,
    8000,
    8008,
    8081,
    8082,
    8443,
    9443,
    9000,
    9090,
    3000,
    3001,
    5000,
    5001,
    7001,
    7002,
    8888,
    9200,
    5601,
    15672,
    2375,
    2376,
    10250,
]

HTTPX_FLAGS = [
    "-silent",
    "-json",
    "-status-code",
    "-title",
    "-tech-detect",
    "-web-server",
    "-cdn",
    "-ip",
    "-cname",
    "-asn",
    "-tls-probe",
    "-tls-grab",
    "-follow-redirects",
    "-location",
    "-content-length",
    "-response-time",
    "-favicon",
    "-path",
    "/,/login,/admin,/api,/swagger,/swagger.json,/openapi.json,/graphql",
    "-ports",
    ",".join(str(port) for port in COMMON_WEB_PORTS),
    "-no-color",
]


def _run_tool(command: List[str], input_text: str = "", timeout: int = 1800) -> Tuple[str, str, int]:
    try:
        result = subprocess.run(
            command,
            input=input_text or None,
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout,
        )
        return result.stdout or "", result.stderr or "", result.returncode
    except FileNotFoundError:
        return "", f"{command[0]} not installed", 127
    except subprocess.TimeoutExpired as exc:
        return exc.stdout or "", f"timeout after {timeout}s", 124


def _record_discard(base_dir: Path, item: str, reason: str, tool: str) -> None:
    append_unique_json_list(
        base_dir / "surfaces" / "discarded_items.json",
        [{"id": stable_id(tool, item, reason), "item": item, "reason": reason, "tool_source": tool}],
    )


def _run_lines(command: List[str], base_dir: Path, tool: str, input_text: str = "", timeout: int = 1800) -> List[str]:
    if shutil.which(command[0]) is None:
        _record_discard(base_dir, " ".join(command), "tool not installed", tool)
        return []
    stdout, stderr, code = _run_tool(command, input_text=input_text, timeout=timeout)
    if code not in (0, 1) and not stdout:
        _record_discard(base_dir, " ".join(command), f"tool failed: {stderr.strip()[:240]}", tool)
    return [line.strip() for line in stdout.splitlines() if line.strip()]


def _domains_from_scope(target: str, scope: list) -> List[str]:
    domains = {target}
    for entry in scope or []:
        clean = str(entry).strip().lower()
        if not clean or clean.startswith("#"):
            continue
        clean = clean.replace("*.", "").strip(".")
        # Simple domain validation check instead of full URL parsing
        if any(x in clean for x in ["/", ":"]):
            try:
                parsed = urlparse(clean if "://" in clean else f"https://{clean}")
                clean = parsed.hostname or clean
            except:
                continue
        if clean:
            domains.add(clean)
    return sorted(domains)


def _copy_if_exists(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if src.exists():
        shutil.copyfile(src, dst)
    elif not dst.exists():
        dst.write_text("", encoding="utf-8")


def _load_jsonl(path: Path) -> List[Dict]:
    items = []
    if not path.exists():
        return items
    with open(path, "r", encoding="utf-8", errors="ignore") as handle:
        for line in handle:
            if not line.strip():
                continue
            try:
                items.append(json.loads(line))
            except json.JSONDecodeError:
                items.append({"raw": line.strip(), "parse_error": True})
    return items


def _parse_method_coverage(target: str, subdomain_dir: Path, base_dir: Path) -> List[Dict]:
    coverage_path = subdomain_dir / "method_coverage.jsonl"
    coverage = _load_jsonl(coverage_path)
    write_json(base_dir / "recon" / "subdomain_method_coverage.json", coverage)
    if not coverage_path.exists():
        _record_discard(
            base_dir,
            str(coverage_path),
            "subdomain recon incomplete: method_coverage.jsonl missing",
            "subdomain_master",
        )
    for item in coverage:
        if item.get("status") == "missing":
            _record_discard(
                base_dir,
                item.get("method", "unknown"),
                item.get("note", "tool not installed"),
                "subdomain_master",
            )
    return coverage


def _parse_missing_tools(subdomain_dir: Path, base_dir: Path) -> List[str]:
    missing = read_lines(subdomain_dir / "missing_tools.txt")
    write_lines(base_dir / "recon" / "missing_tools.txt", missing)
    for tool in missing:
        _record_discard(base_dir, tool, "tool missing in subdomain automation", "subdomain_master")
    return missing


def _parse_takeover_outputs(target: str, subdomain_dir: Path, base_dir: Path) -> List[Dict]:
    surfaces = []
    tasks = []
    for line in read_lines(subdomain_dir / "takeover" / "cnames.txt"):
        parts = line.split()
        if len(parts) < 2:
            continue
        subdomain, cname = parts[0], parts[1]
        surfaces.append(
            {
                "id": stable_id("cname", subdomain, cname),
                "target": target,
                "asset": subdomain,
                "endpoint": subdomain,
                "category": "CNAME records",
                "tool_source": "subdomain_master",
                "cname": cname,
            }
        )
    for line in read_lines(subdomain_dir / "takeover" / "candidates.txt"):
        parts = line.split()
        subdomain = parts[0] if parts else line
        cname = parts[1] if len(parts) > 1 else ""
        surface = {
            "id": stable_id("takeover", subdomain, cname),
            "target": target,
            "asset": subdomain,
            "endpoint": subdomain,
            "category": "takeover candidates",
            "tool_source": "subdomain_master",
            "cname": cname,
        }
        surfaces.append(surface)
        tasks.append(
            evidence_record(
                target=target,
                asset=subdomain,
                endpoint=subdomain,
                vulnerability_class="subdomain takeover",
                severity_guess="High",
                methodology_source="HowToHunt/Subdomain_Takeover",
                tool_source="subdomain_master",
                proof=f"Dangling-provider CNAME pattern candidate: {line}",
                impact="Potential subdomain takeover if provider resource is unclaimed.",
                false_positive_checks=[
                    "Confirm provider-specific not-found fingerprint.",
                    "Confirm the external resource is claimable without affecting production.",
                ],
                manual_validation_steps=[
                    "Resolve CNAME and capture DNS proof.",
                    "Check provider fingerprint against known takeover conditions.",
                    "Do not claim the resource unless program rules explicitly allow it.",
                ],
                next_pivots=[{"type": "active_validation", "value": subdomain, "playbook": "subdomain takeover"}],
            )
        )
    append_unique_json_list(base_dir / "surfaces" / "attack_surfaces.json", surfaces)
    append_unique_json_list(base_dir / "tasks" / "validation_tasks.json", tasks)
    return surfaces


def _parse_script_httpx(target: str, subdomain_dir: Path, base_dir: Path) -> Dict:
    script_full = subdomain_dir / "httpx" / "httpx_full.jsonl"
    root_full = base_dir / "httpx" / "httpx_full.jsonl"
    root_alive = base_dir / "httpx" / "httpx_alive.txt"
    _copy_if_exists(script_full, root_full)
    _copy_if_exists(subdomain_dir / "httpx" / "httpx_alive.txt", root_alive)

    results = [item for item in _load_jsonl(script_full) if not item.get("parse_error")]
    surfaces = []
    for item in results:
        surfaces.extend(classify_httpx_result(target, item))
    tasks = generate_httpx_tasks(target, surfaces)

    tech_counter = Counter()
    status_counter = Counter()
    category_counter = Counter()
    for item in results:
        status_counter[str(item.get("status_code") or item.get("status-code") or "unknown")] += 1
        for tech in item.get("tech") or item.get("technologies") or []:
            tech_counter[tech] += 1
    for surface in surfaces:
        category_counter[surface["category"]] += 1

    write_lines(base_dir / "httpx" / "httpx_interesting.txt", [s["endpoint"] for s in surfaces if s["category"] != "attack surface"])
    write_json(
        base_dir / "httpx" / "httpx_tech_summary.json",
        {
            "total": len(results),
            "alive": len(read_lines(root_alive)),
            "tech": dict(tech_counter),
            "status_codes": dict(status_counter),
            "categories": dict(category_counter),
            "source": str(script_full),
        },
    )
    append_unique_json_list(base_dir / "surfaces" / "attack_surfaces.json", surfaces)
    append_unique_json_list(base_dir / "tasks" / "validation_tasks.json", tasks)
    return {"results": results, "surfaces": surfaces, "tasks": tasks}


def parse_subdomain_master_outputs(target: str, subdomain_dir: Path, base_dir: Path) -> Dict:
    coverage = _parse_method_coverage(target, subdomain_dir, base_dir)
    missing = _parse_missing_tools(subdomain_dir, base_dir)
    _copy_if_exists(subdomain_dir / "all_unique_final.txt", base_dir / "recon" / "subdomains.txt")
    _copy_if_exists(subdomain_dir / "resolved.txt", base_dir / "recon" / "resolved.txt")
    _copy_if_exists(subdomain_dir / "summary.txt", base_dir / "recon" / "subdomain_master_summary.txt")
    httpx_data = _parse_script_httpx(target, subdomain_dir, base_dir)
    takeover_surfaces = _parse_takeover_outputs(target, subdomain_dir, base_dir)

    complete = bool((subdomain_dir / "method_coverage.jsonl").exists() and coverage)
    status = {
        "complete": complete,
        "subdomain_dir": str(subdomain_dir),
        "coverage_count": len(coverage),
        "missing_tools": missing,
        "summary": (subdomain_dir / "summary.txt").read_text(encoding="utf-8", errors="ignore") if (subdomain_dir / "summary.txt").exists() else "",
    }
    write_json(base_dir / "recon" / "subdomain_master_status.json", status)
    return {
        **status,
        "httpx_results": httpx_data["results"],
        "attack_surfaces": httpx_data["surfaces"] + takeover_surfaces,
        "validation_tasks": httpx_data["tasks"],
    }


def run_subdomain_master(target: str, scope: list, base_dir: Path) -> Dict:
    subdomain_dir = base_dir / "recon" / "subdomains"
    subdomain_dir.mkdir(parents=True, exist_ok=True)
    input_path = subdomain_dir / "domains.txt"
    write_lines(input_path, _domains_from_scope(target, scope))

    if not SUBDOMAIN_MASTER.exists():
        _record_discard(base_dir, str(SUBDOMAIN_MASTER), "subdomain automation script missing", "subdomain_master")
        write_json(
            base_dir / "recon" / "subdomain_master_status.json",
            {"complete": False, "subdomain_dir": str(subdomain_dir), "coverage_count": 0, "missing_tools": ["subdomain_master.sh"]},
        )
        return parse_subdomain_master_outputs(target, subdomain_dir, base_dir)

    result = subprocess.run(
        [str(SUBDOMAIN_MASTER), str(input_path), str(subdomain_dir)],
        capture_output=True,
        text=True,
        check=False,
        timeout=7200,
    )
    (subdomain_dir / "logs").mkdir(parents=True, exist_ok=True)
    (subdomain_dir / "logs" / "subdomain_master.stdout").write_text(result.stdout or "", encoding="utf-8")
    (subdomain_dir / "logs" / "subdomain_master.stderr").write_text(result.stderr or "", encoding="utf-8")
    if result.returncode != 0:
        _record_discard(base_dir, "subdomain_master.sh", f"script exited {result.returncode}", "subdomain_master")
    return parse_subdomain_master_outputs(target, subdomain_dir, base_dir)


def enumerate_subdomains(target: str, base_dir: Path) -> List[str]:
    recon_dir = base_dir / "recon"
    all_subdomains = {target}
    commands = [
        ("subfinder", ["subfinder", "-d", target, "-all", "-silent", "-nc"]),
        ("assetfinder", ["assetfinder", "--subs-only", target]),
        ("amass", ["amass", "enum", "-passive", "-norecursive", "-noalts", "-d", target]),
        ("findomain", ["findomain", "-t", target, "-q"]),
    ]
    for tool, command in commands:
        for line in _run_lines(command, base_dir, tool, timeout=2400):
            host = line.lower().strip().strip(".")
            if host == target or host.endswith(f".{target}"):
                all_subdomains.add(host)
            else:
                _record_discard(base_dir, host, "out of scope for target suffix", tool)
    write_lines(recon_dir / "subdomains.txt", all_subdomains)
    return sorted(all_subdomains)


def resolve_dns(subdomains: Iterable[str], base_dir: Path) -> List[str]:
    recon_dir = base_dir / "recon"
    candidates = sorted(set(subdomains))
    resolved = set()
    if shutil.which("dnsx"):
        lines = _run_lines(["dnsx", "-silent", "-a", "-aaaa", "-resp-only"], base_dir, "dnsx", "\n".join(candidates))
        # dnsx -resp-only emits IPs; keep original host resolution with default mode instead.
        host_lines = _run_lines(["dnsx", "-silent", "-a", "-aaaa"], base_dir, "dnsx", "\n".join(candidates))
        for line in host_lines:
            resolved.add(line.split()[0].strip())
    elif shutil.which("puredns"):
        lines = _run_lines(["puredns", "resolve"], base_dir, "puredns", "\n".join(candidates))
        resolved.update(line.split()[0].strip() for line in lines)
    elif shutil.which("shuffledns"):
        lines = _run_lines(["shuffledns", "-silent", "-d", candidates[0].split(".", 1)[-1]], base_dir, "shuffledns", "\n".join(candidates))
        resolved.update(lines)
    else:
        _record_discard(base_dir, "dns resolution", "dnsx/puredns/shuffledns not installed; carrying unresolved candidates forward", "dns")
        resolved.update(candidates)
    write_lines(recon_dir / "resolved.txt", resolved)
    return sorted(resolved)


def permute_subdomains(target: str, resolved: Iterable[str], base_dir: Path) -> List[str]:
    seeds = sorted(set(resolved))
    generated = set()
    if shutil.which("dnsgen"):
        generated.update(_run_lines(["dnsgen", "-"], base_dir, "dnsgen", "\n".join(seeds)))
    elif shutil.which("gotator"):
        generated.update(_run_lines(["gotator", "-sub", "-", "-perm", "wordlist.txt"], base_dir, "gotator", "\n".join(seeds)))
    else:
        _record_discard(base_dir, "subdomain permutation", "dnsgen/gotator not installed", "permutation")
    generated = {host for host in generated if host.endswith(target)}
    if generated:
        write_lines(base_dir / "recon" / "permutations.txt", generated)
        return resolve_dns(generated, base_dir)
    return []


def _parse_httpx_json(stdout: str, output_path: Path) -> List[Dict]:
    results = []
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as handle:
        for line in stdout.splitlines():
            if not line.strip():
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                continue
            results.append(item)
            handle.write(json.dumps(item, sort_keys=True) + "\n")
    return results


def _result_url(item: Dict) -> str:
    return item.get("url") or item.get("input") or item.get("host") or ""


def classify_httpx_result(target: str, item: Dict) -> List[Dict]:
    url = _result_url(item)
    parsed = urlparse(url if "://" in url else f"https://{url}")
    host = parsed.hostname or item.get("host") or item.get("input") or target
    port = parsed.port or item.get("port")
    path = parsed.path.lower()
    title = str(item.get("title") or "").lower()
    tech = " ".join(item.get("tech") or item.get("technologies") or [])
    tech_l = tech.lower()
    server = str(item.get("webserver") or item.get("server") or "").lower()
    cname = str(item.get("cname") or "").lower()
    location = str(item.get("location") or "").lower()
    status = int(item.get("status_code") or item.get("status-code") or 0)
    labels = []

    checks = {
        "admin panels": ("admin" in path or "admin" in title or "dashboard" in title or "jenkins" in tech_l),
        "login/auth": any(token in path or token in title for token in ["login", "signin", "auth", "sso", "oauth"]),
        "APIs": "/api" in path or "application/json" in str(item).lower() or "api" in host,
        "staging/dev/test": any(token in host for token in ["dev", "stage", "staging", "test", "qa", "uat", "preprod"]),
        "cloud/storage": any(token in host + cname + tech_l for token in ["s3", "amazonaws", "blob.core", "storage", "firebase", "cloudfront", "azure"]),
        "exposed dashboards": any(token in title + tech_l for token in ["grafana", "kibana", "rabbitmq", "prometheus", "elasticsearch", "kubernetes", "docker"]),
        "swagger/openapi/graphql": any(token in path + title + tech_l for token in ["swagger", "openapi", "graphql", "graphiql"]),
        "file upload surfaces": any(token in path + title for token in ["upload", "import", "attachment", "media"]),
        "redirect/callback surfaces": any(token in path + location for token in ["redirect", "callback", "returnurl", "next=", "continue="]),
        "cacheable endpoints": any(header in str(item).lower() for header in ["cache-control", "etag", "x-cache", "age"]),
        "unusual ports": bool(port and int(port) not in (80, 443)),
        "high-value tech stacks": any(token in tech_l + server for token in ["jenkins", "jira", "confluence", "wordpress", "drupal", "laravel", "spring", "grafana", "kibana", "nginx", "apache"]),
        "old/vulnerable tech": bool(re.search(r"(php/5|apache/2\.2|jquery 1\.|struts|weblogic|tomcat/7|iis/6)", tech_l + server)),
        "takeover candidates": any(token in cname for token in ["github.io", "herokuapp", "azurewebsites", "cloudapp.net", "s3.amazonaws.com", "pages.dev"]),
        "WAF/CDN protected assets": bool(item.get("cdn") or item.get("cdn_name") or item.get("cdn-name")),
        "direct-IP candidates": bool(item.get("host") and re.match(r"^\d{1,3}(\.\d{1,3}){3}$", str(item.get("host")))),
    }
    for label, matched in checks.items():
        if matched:
            labels.append(label)
    if not labels and status:
        labels.append("attack surface")

    return [
        {
            "id": stable_id("httpx", label, url),
            "target": target,
            "asset": host,
            "endpoint": url,
            "category": label,
            "tool_source": "httpx",
            "status_code": status,
            "title": item.get("title"),
            "tech": item.get("tech") or item.get("technologies") or [],
            "webserver": item.get("webserver") or item.get("server"),
            "cdn": item.get("cdn") or item.get("cdn_name") or item.get("cdn-name"),
            "ip": item.get("a") or item.get("ip"),
            "cname": item.get("cname"),
            "port": port,
            "raw": item,
        }
        for label in labels
    ]


def generate_httpx_tasks(target: str, surfaces: Iterable[Dict]) -> List[Dict]:
    class_map = {
        "admin panels": "admin panel exposure",
        "login/auth": "IDOR/BOLA/API authz",
        "APIs": "IDOR/BOLA/API authz",
        "staging/dev/test": "sensitive file/content discovery",
        "cloud/storage": "cloud metadata exposure",
        "exposed dashboards": "admin panel exposure",
        "swagger/openapi/graphql": "Swagger/OpenAPI/GraphQL abuse",
        "file upload surfaces": "upload abuse",
        "redirect/callback surfaces": "OAuth redirect/callback abuse",
        "cacheable endpoints": "cache poisoning",
        "unusual ports": "RCE/CVE exploitability validation",
        "high-value tech stacks": "RCE/CVE exploitability validation",
        "old/vulnerable tech": "RCE/CVE exploitability validation",
        "takeover candidates": "subdomain takeover",
        "WAF/CDN protected assets": "WAF bypass retry strategy",
        "direct-IP candidates": "cloud metadata exposure",
    }
    tasks = []
    for surface in surfaces:
        vuln_class = class_map.get(surface["category"], "sensitive file/content discovery")
        endpoint = surface["endpoint"]
        tasks.append(
            evidence_record(
                target=target,
                asset=surface["asset"],
                endpoint=endpoint,
                vulnerability_class=vuln_class,
                severity_guess="Medium",
                methodology_source="HowToHunt/bugbounty-cheatsheet/awesome-oneliner-bugbounty",
                tool_source="httpx",
                curl=f"curl -i -k {endpoint}",
                impact=f"Potential {vuln_class} on classified {surface['category']} surface.",
                manual_validation_steps=[
                    "Replay the baseline request and capture status, headers, and body length.",
                    "Apply the matching active validation playbook before reporting.",
                ],
                next_pivots=[{"type": "url_collection", "value": endpoint}],
            )
        )
    return tasks


def run_httpx_full(target: str, resolved: Iterable[str], base_dir: Path, config: Dict = None) -> Dict:
    httpx_dir = base_dir / "httpx"
    inputs = sorted(set(resolved))
    full_path = httpx_dir / "httpx_full.jsonl"
    alive_path = httpx_dir / "httpx_alive.txt"
    interesting_path = httpx_dir / "httpx_interesting.txt"
    summary_path = httpx_dir / "httpx_tech_summary.json"

    if not inputs:
        write_lines(alive_path, [])
        write_lines(interesting_path, [])
        write_json(summary_path, {"total": 0, "tech": {}, "status_codes": {}, "categories": {}})
        return {"results": [], "surfaces": [], "tasks": []}

    if shutil.which("httpx") is None:
        _record_discard(base_dir, "httpx full probing", "httpx not installed", "httpx")
        write_lines(alive_path, [])
        write_lines(interesting_path, [])
        write_json(summary_path, {"total": 0, "tech": {}, "status_codes": {}, "categories": {}, "error": "httpx not installed"})
        return {"results": [], "surfaces": [], "tasks": []}

    threads = str(config.get("httpx_threads", 50)) if config else "50"
    timeout = str(config.get("request_timeout", 10)) if config else "10"
    
    cmd = ["httpx", *HTTPX_FLAGS, "-t", threads, "-timeout", timeout]
    stdout, stderr, code = _run_tool(cmd, input_text="\n".join(inputs), timeout=3600)
    results = _parse_httpx_json(stdout, full_path)
    if code not in (0, 1) and not results:
        _record_discard(base_dir, "httpx full probing", f"httpx failed: {stderr.strip()[:240]}", "httpx")

    alive = [_result_url(item) for item in results if _result_url(item)]
    surfaces = []
    for item in results:
        surfaces.extend(classify_httpx_result(target, item))
    interesting = [surface["endpoint"] for surface in surfaces if surface["category"] != "attack surface"]
    tasks = generate_httpx_tasks(target, surfaces)

    tech_counter = Counter()
    status_counter = Counter()
    category_counter = Counter()
    for item in results:
        status_counter[str(item.get("status_code") or item.get("status-code") or "unknown")] += 1
        for tech in item.get("tech") or item.get("technologies") or []:
            tech_counter[tech] += 1
    for surface in surfaces:
        category_counter[surface["category"]] += 1

    write_lines(alive_path, alive)
    write_lines(interesting_path, interesting)
    write_json(
        summary_path,
        {
            "total": len(results),
            "alive": len(alive),
            "tech": dict(tech_counter),
            "status_codes": dict(status_counter),
            "categories": dict(category_counter),
            "ports": COMMON_WEB_PORTS,
        },
    )
    append_unique_json_list(base_dir / "surfaces" / "attack_surfaces.json", surfaces)
    append_unique_json_list(base_dir / "tasks" / "validation_tasks.json", tasks)
    return {"results": results, "surfaces": surfaces, "tasks": tasks}


def run_port_discovery(target: str, resolved: Iterable[str], base_dir: Path, config: Dict = None) -> List[str]:
    ports_dir = base_dir / "ports"
    ports_dir.mkdir(parents=True, exist_ok=True)
    open_ports_file = ports_dir / "open_ports.txt"
    web_ports_file = ports_dir / "web_ports.txt"
    inputs = sorted(set(resolved))
    if not inputs:
        write_lines(open_ports_file, [])
        write_lines(web_ports_file, [])
        return []

    input_file = ports_dir / "ips_and_domains.txt"
    write_lines(input_file, inputs)

    has_naabu = shutil.which("naabu") is not None
    has_nmap = shutil.which("nmap") is not None
    rate = str(config.get("naabu_rate", 1000)) if config else "1000"

    if has_naabu:
        print("[*] Running naabu for port discovery...")
        _run_tool(["naabu", "-l", str(input_file), "-o", str(open_ports_file), "-silent", "-c", "50", "-rate", rate], timeout=3600)
    elif has_nmap:
        print("[*] Running nmap for port discovery...")
        stdout, _, _ = _run_tool(["nmap", "-iL", str(input_file), "-T4", "-F", "--open", "-oG", "-"], timeout=3600)
        ports = []
        for line in stdout.splitlines():
            if "Ports:" in line:
                host = line.split()[1]
                for p in line.split("Ports:")[1].split(","):
                    p = p.strip()
                    if "/" in p:
                        port = p.split("/")[0]
                        ports.append(f"{host}:{port}")
        write_lines(open_ports_file, ports)
    else:
        print("[-] SKIPPED: Port discovery skipped (naabu/nmap not found).")
        write_lines(open_ports_file, [])
        
    web_candidates = []
    if open_ports_file.exists():
        for line in read_lines(open_ports_file):
            if ":" in line:
                host, port = line.rsplit(":", 1)
                try:
                    if int(port) in COMMON_WEB_PORTS or int(port) > 1024:
                        web_candidates.append(line)
                except ValueError:
                    web_candidates.append(line)
            else:
                web_candidates.append(line)
    
    # Merge exposure web ports
    shodan_web = base_dir / "shodan" / "web_ports.txt"
    if shodan_web.exists():
        web_candidates.extend(read_lines(shodan_web))
    censys_web = base_dir / "censys" / "web_ports.txt"
    if censys_web.exists():
        web_candidates.extend(read_lines(censys_web))
    fofa_web = base_dir / "fofa" / "web_ports.txt"
    if fofa_web.exists():
        web_candidates.extend(read_lines(fofa_web))

    web_candidates.extend(inputs)
    final_web = sorted(set(web_candidates))
    write_lines(web_ports_file, final_web)
    return final_web


def run_recon(target: str, scope: list, base_dir: Path, config: Dict = None):
    print(f"[*] Running mandatory recon chain for {target}...")
    ensure_run_dirs(base_dir)
    master_data = run_subdomain_master(target, scope, base_dir)
    resolved = read_lines(base_dir / "recon" / "resolved.txt")
    
    # Port discovery
    web_candidates = run_port_discovery(target, resolved, base_dir, config)
    
    httpx_data = run_httpx_full(target, web_candidates, base_dir, config)
    attack_surfaces = master_data["attack_surfaces"] + httpx_data["surfaces"]
    validation_tasks = master_data["validation_tasks"] + httpx_data["tasks"]
    return {
        "subdomains": str(base_dir / "recon" / "subdomains.txt"),
        "resolved": str(base_dir / "recon" / "resolved.txt"),
        "httpx_full": str(base_dir / "httpx" / "httpx_full.jsonl"),
        "httpx_alive": str(base_dir / "httpx" / "httpx_alive.txt"),
        "subdomain_master_complete": master_data["complete"],
        "subdomain_master_dir": master_data["subdomain_dir"],
        "method_coverage_count": master_data["coverage_count"],
        "missing_tools": master_data["missing_tools"],
        "httpx_results": httpx_data["results"],
        "attack_surfaces": attack_surfaces,
        "validation_tasks": validation_tasks,
    }
