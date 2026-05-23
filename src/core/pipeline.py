import os
import json
import yaml
import asyncio
from pathlib import Path
from typing import Dict, Any, List, Iterable
from urllib.parse import urlparse

# Placeholder imports for pipeline stages
from intelligence.scope_parser import parse_scope
from recon.recon_chain import run_recon, run_httpx_full
from recon.exposure_recon import run_exposure
from recon.dork_generator import generate_dorks
from recon.url_collector import collect_urls
from intelligence.js_analyzer import analyze_js
from intelligence.api_mapper import map_apis
from intelligence.surface_classifier import classify_surface
from intelligence.hypothesis_engine import generate_hypotheses
from intelligence.playbook_runner import run_playbooks
from intelligence.validator import validate
from intelligence.severity_mapper import map_severity
from intelligence.report_builder import build_report
from intelligence.methodology_parser import MethodologyEngine
from intelligence.nuclei_parser import parse_nuclei_results, run_nuclei_on_alive
from intelligence.pivot_engine import enqueue_pivots
from intelligence.gf_analyzer import analyze_urls_gf
from orchestration.orchestrator import Orchestrator
from orchestration.schemas import TaskResult
from recon.fuzzing import run_content_discovery, run_parameter_discovery
from core.artifacts import ensure_run_dirs, read_lines, write_json, stable_id, should_skip, now_iso, record_command, write_lines, ScopeGuard
from reporting.evidence_pack import generate_evidence_pack

def create_output_structure(target: str) -> Path:
    base_dir = Path(f"runs/{target}")
    dirs = [
        "scope", "recon", "urls", "js", "api", "dorks", "exposure",
        "nuclei", "fuzz", "candidates", "validation", "reports", "logs", "manual_queries",
        "httpx", "surfaces", "tasks", "findings", "imports", "playbooks"
    ]
    for d in dirs:
        (base_dir / d).mkdir(parents=True, exist_ok=True)
    ensure_run_dirs(base_dir)
    required_empty_files = {
        "recon/subdomains.txt": "",
        "recon/resolved.txt": "",
        "httpx/httpx_full.jsonl": "",
        "httpx/httpx_alive.txt": "",
        "httpx/httpx_interesting.txt": "",
        "urls/collected_urls.txt": "",
        "urls/params.txt": "",
        "js/js_files.txt": "",
        "js/endpoints.txt": "",
        "js/secrets_candidates.json": "[]",
        "surfaces/attack_surfaces.json": "[]",
        "tasks/validation_tasks.json": "[]",
        "findings/candidates.json": "[]",
        "findings/reportable.json": "[]",
        "reports/final_summary.md": "",
    }
    for rel, content in required_empty_files.items():
        path = base_dir / rel
        if not path.exists():
            path.write_text(content, encoding="utf-8")
    return base_dir

def load_reco_config(profile_name: str = "safe") -> Dict[str, Any]:
    path = Path("config/reco.yaml")
    default_config = {
        "httpx_threads": 20,
        "katana_concurrency": 5,
        "nuclei_rate_limit": 50,
        "naabu_rate": 500,
        "request_timeout": 10,
        "max_retries": 2,
        "max_runtime_per_stage": 3600
    }
    
    if not path.exists():
        return default_config
        
    with open(path, "r") as f:
        full_config = yaml.safe_load(f) or {}
        
    profiles = full_config.get("profiles", {})
    profile = profiles.get(profile_name, profiles.get("safe", default_config))
    return profile

def _update_memory_sync(task_name: str, target: str, data: dict):
    """Synchronous wrapper to update memory via Orchestrator."""
    try:
        orchestrator = Orchestrator()
        result = TaskResult(
            task_id=stable_id(task_name, target, str(data.get("id", task_name))),
            task_name=task_name,
            target=target,
            status="completed",
            data=data,
            depth=0
        )
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.ensure_future(orchestrator.evaluate_and_route(result))
        else:
            loop.run_until_complete(orchestrator.evaluate_and_route(result))
    except Exception as exc:
        print(f"[-] Failed to update memory for {task_name}: {exc}")

def run_pipeline(target: str, scope_file: str, profile_name: str = "safe", force: bool = False, allow_out_of_scope: bool = False):
    print(f"[*] Starting Hunt Pipeline for {target} with profile {profile_name}")
    base_dir = create_output_structure(target)
    config = load_reco_config(profile_name)
    
    # 1. Parse Scope
    scope_out = base_dir / "scope" / "parsed_scope.txt"
    if not should_skip(scope_out, force):
        start = now_iso()
        scope = parse_scope(target, scope_file, base_dir)
        record_command(base_dir, "scope_parser", ["parse_scope"], scope_file, str(scope_out), start_time=start)
    else:
        scope = read_lines(scope_out)
    
    guard = ScopeGuard(target, scope, base_dir, allow_out_of_scope)

    # 3. Exposure Recon (Shodan/Censys)
    exposure_out = base_dir / "shodan" / "shodan_results.jsonl"
    if not should_skip(exposure_out, force):
        start = now_iso()
        exposure_data = run_exposure(target, base_dir)
        record_command(base_dir, "exposure_recon", ["run_exposure"], target, str(exposure_out), start_time=start)
    
    # 2. Recon Chain (Mandatory)
    recon_out = base_dir / "recon" / "subdomain_master_status.json"
    if not should_skip(recon_out, force):
        start = now_iso()
        recon_data = run_recon(target, scope, base_dir, config)
        _update_memory_sync("subdomain_enum", target, recon_data)
        record_command(base_dir, "recon_chain", ["run_recon"], str(scope_out), str(recon_out), start_time=start)
    else:
        with open(recon_out, "r") as f:
            recon_data = json.load(f)

    # 2b. Local methodology extraction into reusable playbooks/word seeds.
    methodology_data = MethodologyEngine().build_local_playbooks(base_dir)
    
    # 4. Dork Generator
    dorks_out = base_dir / "dorks" / "dork_results.jsonl"
    if not should_skip(dorks_out, force):
        start = now_iso()
        dorks = generate_dorks(target, base_dir)
        record_command(base_dir, "dork_generator", ["generate_dorks"], target, str(dorks_out), start_time=start)
    
    # 5. URL Collector
    urls_out = base_dir / "urls" / "collected_urls.txt"
    if not should_skip(urls_out, force):
        start = now_iso()
        urls = collect_urls(target, base_dir, config)
        urls = guard.filter(urls)
        write_lines(urls_out, urls)
        record_command(base_dir, "url_collector", ["collect_urls"], target, str(urls_out), start_time=start)
    else:
        urls = read_lines(urls_out)
    
    # 6. JS Analyzer
    js_out = base_dir / "js" / "secrets_candidates.json"
    if not should_skip(js_out, force):
        start = now_iso()
        js_data = analyze_js(target, urls, base_dir)
        record_command(base_dir, "js_analyzer", ["analyze_js"], str(urls_out), str(js_out), start_time=start)
    else:
        with open(js_out, "r") as f:
            js_data = {"secrets": json.load(f), "endpoints": read_lines(base_dir / "js" / "endpoints.txt")}
    
    # P1: Connect JS-discovered endpoints back into httpx/URL testing
    js_endpoints = guard.filter(js_data.get("endpoints", []))
    if js_endpoints:
        print(f"[*] Probing {len(js_endpoints)} JS-discovered endpoints via HTTPX...")
        run_httpx_full(target, js_endpoints, base_dir, config)
        
    # P1: GF-style URL classifier
    gf_urls = analyze_urls_gf(target, urls + js_endpoints, base_dir)
    
    # 7. API Mapper
    api_out = base_dir / "api" / "api_endpoints.txt"
    if not should_skip(api_out, force):
        start = now_iso()
        api_data = map_apis(target, urls, js_data, base_dir)
        api_data = guard.filter(api_data)
        write_lines(api_out, api_data)
        record_command(base_dir, "api_mapper", ["map_apis"], str(urls_out), str(api_out), start_time=start)
    else:
        api_data = read_lines(api_out)
    
    # 8. Surface Classifier
    surf_out = base_dir / "recon" / "classified_surface.json"
    if not should_skip(surf_out, force):
        start = now_iso()
        classified_surface = classify_surface(target, urls, api_data, base_dir)
        _update_memory_sync("browser_verify", target, {"technologies": list(classified_surface.keys())})
        record_command(base_dir, "surface_classifier", ["classify_surface"], target, str(surf_out), start_time=start)
    else:
        with open(surf_out, "r") as f:
            classified_surface = json.load(f)
    
    # 9. Hypothesis Engine
    hypotheses = generate_hypotheses(target, classified_surface, profile_name, base_dir)
    
    # 10. Playbook Runner
    candidates = run_playbooks(target, hypotheses, base_dir)

    # 10b. Convert nuclei signals into validation tasks, never direct reports.
    nuclei_out = base_dir / "nuclei" / "nuclei_results.jsonl"
    if not should_skip(nuclei_out, force):
        start = now_iso()
        alive_filtered = guard.filter(read_lines(base_dir / "httpx" / "httpx_alive.txt"))
        write_lines(base_dir / "httpx" / "httpx_alive_scoped.txt", alive_filtered)
        run_nuclei_on_alive(target, base_dir, config)
        record_command(base_dir, "nuclei", ["run_nuclei"], target, str(nuclei_out), start_time=start)
    nuclei_tasks = parse_nuclei_results(target, base_dir)

    # 10c. Parameter/content discovery loops over collected live URLs.
    fuzz_anchor = base_dir / "fuzz" / ".fuzzing_complete"
    if force or not fuzz_anchor.exists():
        start = now_iso()
        run_parameter_discovery(target, urls, base_dir, config)
        run_content_discovery(target, guard.filter(read_lines(base_dir / "httpx" / "httpx_alive.txt")), base_dir, config)
        fuzz_anchor.touch()
        record_command(base_dir, "fuzzing", ["run_fuzzing"], target, str(fuzz_anchor), start_time=start)
    else:
        print(f"[*] SKIPPED existing output: fuzzing anchor found")
    
    enqueue_pivots(base_dir, candidates + nuclei_tasks)
    
    # 11. Validator
    validated_findings = []
    for candidate in candidates:
        v = validate(target, candidate, base_dir)
        if v and v.get("state") == "VALIDATED":
            validated_findings.append(v)
            _update_memory_sync("finding_validated", target, v)
            
    # 12. Severity Mapper
    for finding in validated_findings:
        map_severity(finding)
        
    # 13. Report Builder
    for finding in validated_findings:
        if finding.get("status") == "REPORTABLE" or finding.get("state") == "REPORTABLE":
            build_report(finding, base_dir)
    build_report({"id": "final_summary", "target": target, "summary_only": True}, base_dir)
    
    # P2: Evidence Pack
    generate_evidence_pack(target, validated_findings, base_dir)
            
    print(f"[*] Pipeline completed for {target}")

def run_recon_only(target: str, scope_file: str):
    print(f"[*] Starting Mandatory Recon Chain for {target}")
    base_dir = create_output_structure(target)
    scope = parse_scope(target, scope_file, base_dir)
    config = load_reco_config("safe")
    run_recon(target, scope, base_dir, config)
    run_exposure(target, base_dir)
    generate_dorks(target, base_dir)
    print(f"[*] Recon completed for {target}")

def validate_finding(finding_path: str):
    path = Path(finding_path)
    if not path.exists():
        print(f"[-] Finding file {finding_path} not found.")
        return
    
    with open(path, "r") as f:
        finding = json.load(f)
        
    target = finding.get("target", "unknown")
    base_dir = create_output_structure(target)
    print(f"[*] Validating finding from {finding_path}")
    v = validate(target, finding, base_dir)
    if v:
        map_severity(v)
        v["state"] = "REPORTABLE"
        out_path = base_dir / "validation" / f"{v['id']}.json"
        with open(out_path, "w") as out:
            json.dump(v, out, indent=2)
        print(f"[+] Finding validated. Saved to {out_path}")

def report_finding(finding_path: str):
    path = Path(finding_path)
    if not path.exists():
        print(f"[-] Finding file {finding_path} not found.")
        return
        
    with open(path, "r") as f:
        finding = json.load(f)
        
    target = finding.get("target", "unknown")
    base_dir = create_output_structure(target)
    print(f"[*] Generating report for finding from {finding_path}")
    build_report(finding, base_dir)
