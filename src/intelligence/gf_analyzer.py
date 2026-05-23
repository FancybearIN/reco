import json
import re
from pathlib import Path
from typing import Dict, Iterable, List

from core.artifacts import append_unique_json_list, evidence_record, read_lines, stable_id, write_json, write_lines

# GF patterns mapped from PayloadsAllTheThings / gf-patterns
GF_PATTERNS = {
    "sqli": r"(?i)(id|page|dir|category|param|query|search|q|view|id|id|id|id|id)=",
    "xss": r"(?i)(q|s|search|lang|keyword|query|page|url|name|callback|jsonp)=",
    "ssrf": r"(?i)(url|uri|dest|redirect|path|continue|window|next|data|reference|site|html|val|validate|domain|callback|return|page|feed|host|port|to|out|view|dir|show|navigation|open)=",
    "lfi": r"(?i)(file|document|folder|root|path|pg|style|pdf|template|folder|dir|name|page|view|img)=",
    "idor": r"(?i)(id|user|account|number|order|no|doc|key|email|group|profile|edit|update|delete|uid)=",
    "rce": r"(?i)(cmd|exec|command|execute|ping|query|jump|code|reg|do|func|arg|option|load|process|step|read|function|req|feature|exe|module|payload|run|print)=",
    "redirect": r"(?i)(url|redirect|next|return|continue|checkout|out|dest|path|target|forward|go|goto)=",
    "cors": r"(?i)(origin|callback|jsonp)=",
    "upload": r"(?i)(upload|file|import|attachment|media)=",
    "api": r"(?i)(api|v1|v2|v3|graphql|swagger|openapi)=",
    "debug": r"(?i)(debug|test|dev|env|config|status|info|log)=",
}

def analyze_urls_gf(target: str, urls: Iterable[str], base_dir: Path) -> Dict[str, List[str]]:
    print(f"[*] Classifying collected URLs against GF-patterns for {target}...")
    gf_dir = base_dir / "urls" / "gf"
    gf_dir.mkdir(parents=True, exist_ok=True)
    
    categorized_urls: Dict[str, set] = {k: set() for k in GF_PATTERNS.keys()}
    
    for url in urls:
        for category, pattern in GF_PATTERNS.items():
            if re.search(pattern, url):
                categorized_urls[category].add(url)
                
    tasks = []
    
    # Map to hypotheses and tasks
    vuln_mapping = {
        "sqli": "SQLi",
        "ssrf": "SSRF",
        "idor": "IDOR/BOLA/API authz",
        "redirect": "OAuth redirect/callback abuse",
        "rce": "RCE/CVE exploitability validation",
        "lfi": "sensitive file/content discovery",
    }
    
    for category, matched_urls in categorized_urls.items():
        if not matched_urls:
            continue
        
        file_path = gf_dir / f"{category}.txt"
        write_lines(file_path, sorted(matched_urls))
        
        vuln_class = vuln_mapping.get(category)
        if vuln_class:
            for url in list(matched_urls)[:20]:  # Limit task generation to top 20 per category to prevent explosion
                tasks.append(
                    evidence_record(
                        target=target,
                        asset=target,
                        endpoint=url,
                        vulnerability_class=vuln_class,
                        severity_guess="High",
                        methodology_source="PayloadsAllTheThings/GF",
                        tool_source="gf_analyzer",
                        curl=f"curl -i -k '{url}'",
                        impact=f"Parameter matches pattern for {vuln_class}; further testing required.",
                        manual_validation_steps=[f"Test parameters for {vuln_class} indicators."],
                        next_pivots=[{"type": "active_validation", "value": url, "playbook": vuln_class}],
                    )
                )

    if tasks:
        append_unique_json_list(base_dir / "tasks" / "validation_tasks.json", tasks)

    return {k: sorted(v) for k, v in categorized_urls.items()}
