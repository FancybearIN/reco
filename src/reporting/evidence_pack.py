import json
from pathlib import Path
from typing import List, Dict, Any

def generate_evidence_pack(target: str, validated_findings: List[Dict[str, Any]], base_dir: Path):
    print(f"[*] Generating Evidence Pack for {target}...")
    reports_dir = base_dir / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    
    pack_md = f"# Evidence Pack: {target}\n\n"
    pack_json = []
    
    for finding in validated_findings:
        vuln_type = finding.get("vulnerability_class") or finding.get("finding_type") or "unknown"
        severity = finding.get("severity") or finding.get("severity_guess") or "Unknown"
        confidence = finding.get("confidence_score", 0.85) # Default high confidence for validated
        
        entry = {
            "affected_url": finding.get("endpoint"),
            "vuln_type": vuln_type,
            "severity_guess": severity,
            "request": finding.get("request"),
            "response_snippet": finding.get("response", "")[:1000],
            "reproduction_steps": finding.get("manual_validation_steps", []),
            "impact_hypothesis": finding.get("impact"),
            "confidence_score": confidence,
            "source_module": finding.get("tool_source")
        }
        pack_json.append(entry)
        
        pack_md += f"## {vuln_type} - {severity}\n"
        pack_md += f"- **URL:** {entry['affected_url']}\n"
        pack_md += f"- **Module:** {entry['source_module']}\n"
        pack_md += f"- **Confidence:** {entry['confidence_score']}\n"
        pack_md += f"- **Impact:** {entry['impact_hypothesis']}\n\n"
        pack_md += "### Reproduction Steps\n"
        for step in entry['reproduction_steps']:
            pack_md += f"1. {step}\n"
        pack_md += "\n"
        if entry['request']:
            pack_md += "### Request\n```http\n" + entry['request'] + "\n```\n\n"
        if entry['response_snippet']:
            pack_md += "### Response Snippet\n```http\n" + entry['response_snippet'] + "\n```\n\n"
        pack_md += "---\n\n"

    with open(reports_dir / "evidence_pack.md", "w") as f:
        f.write(pack_md)
        
    with open(reports_dir / "evidence_pack.json", "w") as f:
        json.dump(pack_json, f, indent=2)
    
    print(f"[+] Evidence Pack saved to {reports_dir / 'evidence_pack.md'}")
