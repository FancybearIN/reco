import os
import json
import base64
import requests
from pathlib import Path

try:
    import shodan
    SHODAN_INSTALLED = True
except ImportError:
    SHODAN_INSTALLED = False

try:
    from censys.search import CensysHosts
    CENSYS_INSTALLED = True
except ImportError:
    CENSYS_INSTALLED = False

def _execute_fofa(query: str, email: str, key: str) -> list:
    qbase64 = base64.b64encode(query.encode()).decode()
    url = f"https://fofa.info/api/v1/search/all?email={email}&key={key}&qbase64={qbase64}&fields=ip,port,host,domain,title"
    try:
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            data = response.json()
            if not data.get("error"):
                return data.get("results", [])
    except:
        pass
    return []

def run_exposure(target: str, base_dir: Path):
    print(f"[*] Generating Exposure Recon Queries for {target}...")
    mq_dir = base_dir / "manual_queries"
    mq_dir.mkdir(parents=True, exist_ok=True)
    
    shodan_dir = base_dir / "shodan"
    shodan_dir.mkdir(parents=True, exist_ok=True)
    
    censys_dir = base_dir / "censys"
    censys_dir.mkdir(parents=True, exist_ok=True)
    
    fofa_dir = base_dir / "fofa"
    fofa_dir.mkdir(parents=True, exist_ok=True)
    
    shodan_query = f"ssl:\"{target}\" OR hostname:\"{target}\""
    censys_query = f"services.tls.certificates.leaf_data.names: \"{target}\""
    fofa_query = f"domain=\"{target}\" || host=\"{target}\""
    
    with open(mq_dir / "shodan_queries.txt", "w") as f:
        f.write(shodan_query + "\n")
        
    with open(mq_dir / "censys_queries.txt", "w") as f:
        f.write(censys_query + "\n")
        
    with open(mq_dir / "fofa_queries.txt", "w") as f:
        f.write(fofa_query + "\n")
        
    shodan_key = os.environ.get("SHODAN_API_KEY")
    shodan_results = []
    shodan_ips = set()
    shodan_web_ports = set()
    
    if shodan_key and SHODAN_INSTALLED:
        print(f"[*] Executing Shodan query: {shodan_query}")
        try:
            api = shodan.Shodan(shodan_key)
            results = api.search(shodan_query)
            
            for match in results.get('matches', []):
                ip = match.get('ip_str')
                port = match.get('port')
                if ip:
                    shodan_ips.add(ip)
                if ip and port:
                    shodan_web_ports.add(f"{ip}:{port}")
                
                shodan_item = {
                    "ip": ip,
                    "port": port,
                    "hostnames": match.get('hostnames', []),
                    "org": match.get('org'),
                    "asn": match.get('asn'),
                    "product": match.get('product'),
                    "version": match.get('version'),
                    "ssl": match.get('ssl', {}),
                    "http_title": match.get('http', {}).get('title'),
                    "http_status": match.get('http', {}).get('status')
                }
                shodan_results.append(shodan_item)
        except Exception as e:
            print(f"[-] Shodan API Error: {e}")
    else:
        reason = "SHODAN_API_KEY not found" if not shodan_key else "shodan python module not installed"
        print(f"[-] SKIPPED: Shodan execution skipped ({reason}).")
        
    with open(shodan_dir / "shodan_results.jsonl", "w") as f:
        for r in shodan_results:
            f.write(json.dumps(r) + "\n")
            
    with open(shodan_dir / "ips.txt", "w") as f:
        for ip in sorted(shodan_ips):
            f.write(ip + "\n")
            
    with open(shodan_dir / "web_ports.txt", "w") as f:
        for wp in sorted(shodan_web_ports):
            f.write(wp + "\n")
            
    # Censys Enrichment
    censys_id = os.environ.get("CENSYS_API_ID")
    censys_secret = os.environ.get("CENSYS_API_SECRET")
    censys_results = []
    censys_ips = set()
    censys_web_ports = set()
    
    if censys_id and censys_secret and CENSYS_INSTALLED:
        print(f"[*] Executing Censys query: {censys_query}")
        try:
            h = CensysHosts(api_id=censys_id, api_secret=censys_secret)
            for page in h.search(censys_query, per_page=100, pages=1):
                for match in page:
                    ip = match.get('ip')
                    if ip:
                        censys_ips.add(ip)
                        for service in match.get('services', []):
                            port = service.get('port')
                            if port:
                                censys_web_ports.add(f"{ip}:{port}")
                    censys_results.append(match)
        except Exception as e:
            print(f"[-] Censys API Error: {e}")
    else:
        reason = "CENSYS_API_ID/SECRET not found" if not (censys_id and censys_secret) else "censys python module not installed"
        print(f"[-] SKIPPED: Censys execution skipped ({reason}).")

    with open(censys_dir / "censys_results.jsonl", "w") as f:
        for r in censys_results:
            f.write(json.dumps(r) + "\n")
            
    with open(censys_dir / "ips.txt", "w") as f:
        for ip in sorted(censys_ips):
            f.write(ip + "\n")
            
    with open(censys_dir / "web_ports.txt", "w") as f:
        for wp in sorted(censys_web_ports):
            f.write(wp + "\n")

    # FOFA Enrichment
    fofa_email = os.environ.get("FOFA_EMAIL")
    fofa_key = os.environ.get("FOFA_API_KEY")
    fofa_results = []
    fofa_ips = set()
    fofa_web_ports = set()

    if fofa_email and fofa_key:
        print(f"[*] Executing FOFA query: {fofa_query}")
        results = _execute_fofa(fofa_query, fofa_email, fofa_key)
        for r in results:
            ip, port, host, domain, title = r
            fofa_ips.add(ip)
            fofa_web_ports.add(f"{ip}:{port}")
            fofa_results.append({
                "ip": ip,
                "port": port,
                "host": host,
                "domain": domain,
                "title": title
            })
    else:
        print("[-] SKIPPED: FOFA execution skipped (FOFA_EMAIL or FOFA_API_KEY not found).")

    with open(fofa_dir / "fofa_results.jsonl", "w") as f:
        for r in fofa_results:
            f.write(json.dumps(r) + "\n")
            
    with open(fofa_dir / "ips.txt", "w") as f:
        for ip in sorted(fofa_ips):
            f.write(ip + "\n")
            
    with open(fofa_dir / "web_ports.txt", "w") as f:
        for wp in sorted(fofa_web_ports):
            f.write(wp + "\n")

    return {
        "shodan_query": shodan_query,
        "censys_query": censys_query,
        "fofa_query": fofa_query,
        "shodan_ips": sorted(shodan_ips),
        "censys_ips": sorted(censys_ips),
        "fofa_ips": sorted(fofa_ips),
        "shodan_web_ports": sorted(shodan_web_ports),
        "censys_web_ports": sorted(censys_web_ports),
        "fofa_web_ports": sorted(fofa_web_ports)
    }
