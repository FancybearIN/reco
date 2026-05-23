import os
import json
import shutil
import sys
from pathlib import Path
from typing import Dict, Any

def healthcheck():
    print("[*] Running Reco Tool Health Check...")
    
    tools = [
        "subfinder", "assetfinder", "amass", "httpx", "dnsx", 
        "naabu", "nmap", "nuclei", "katana", "gau", 
        "waybackurls", "gf", "subzy"
    ]
    
    env_vars = [
        "CHAOS_API_KEY", "H1_API_TOKEN", "SHODAN_API_KEY", 
        "FOFA_EMAIL", "FOFA_API_KEY", "OTX_API_KEY", 
        "VIRUSTOTAL_API_KEY", "CENSYS_API_ID", "CENSYS_API_SECRET", 
        "SERPER_API_KEY", "GOOGLE_CSE_API_KEY", "GOOGLE_CSE_ID",
        "SECURITYTRAILS_API_KEY"
    ]
    
    results = {
        "tools": {},
        "env_vars": {},
        "timestamp": __import__("datetime").datetime.now().isoformat()
    }
    
    # Check Tools
    for tool in tools:
        path = shutil.which(tool)
        results["tools"][tool] = {
            "installed": path is not None,
            "path": path or "NOT FOUND"
        }
        status = "OK" if path else "MISSING"
        print(f"  [Tool] {tool:15}: {status}")

    # Check API Keys
    for var in env_vars:
        val = os.environ.get(var)
        results["env_vars"][var] = {
            "set": val is not None,
            "length": len(val) if val else 0
        }
        status = "SET" if val else "MISSING"
        print(f"  [Env]  {var:20}: {status}")

    # Save Results
    runs_dir = Path("runs")
    runs_dir.mkdir(exist_ok=True)
    
    json_path = runs_dir / "healthcheck.json"
    with open(json_path, "w") as f:
        json.dump(results, f, indent=2)
        
    md_path = runs_dir / "healthcheck.md"
    with open(md_path, "w") as f:
        f.write("# Reco Health Check Report\n\n")
        f.write(f"Generated at: {results['timestamp']}\n\n")
        f.write("## Tools\n\n")
        f.write("| Tool | Status | Path |\n")
        f.write("| --- | --- | --- |\n")
        for tool, info in results["tools"].items():
            f.write(f"| {tool} | {'✅' if info['installed'] else '❌'} | `{info['path']}` |\n")
        
        f.write("\n## Environment Variables\n\n")
        f.write("| Variable | Status | Set |\n")
        f.write("| --- | --- | --- |\n")
        for var, info in results["env_vars"].items():
            f.write(f"| {var} | {'✅' if info['set'] else '❌'} | {info['set']} |\n")

    print(f"\n[+] Health Check saved to {json_path} and {md_path}")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "healthcheck":
        healthcheck()
    else:
        print("Usage: python -m src.cli healthcheck")
