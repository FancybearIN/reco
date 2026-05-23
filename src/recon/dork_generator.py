import os
import json
import requests
from pathlib import Path

def _execute_serper(query: str, api_key: str) -> list:
    url = "https://google.serper.dev/search"
    headers = {
        'X-API-KEY': api_key,
        'Content-Type': 'application/json'
    }
    payload = json.dumps({"q": query})
    try:
        response = requests.post(url, headers=headers, data=payload, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data.get("organic", [])
    except requests.RequestException:
        pass
    return []

def _execute_google_cse(query: str, api_key: str, cse_id: str) -> list:
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": api_key,
        "cx": cse_id,
        "q": query
    }
    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data.get("items", [])
    except requests.RequestException:
        pass
    return []

def generate_dorks(target: str, base_dir: Path):
    print(f"[*] Generating Dorks for {target}...")
    dorks_dir = base_dir / "dorks"
    dorks_dir.mkdir(parents=True, exist_ok=True)
    
    google_dorks = [
        f"site:{target} ext:php | ext:aspx | ext:jsp",
        f"site:{target} inurl:admin | inurl:login",
        f"site:{target} intitle:\"index of\"",
        f"site:{target} \"choose password\" | \"reset password\"",
        f"site:{target} ext:env | ext:log | ext:sql"
    ]
    github_dorks = [
        f"org:{target} \"password\"",
        f"\"{target}\" \"API_KEY\"",
        f"\"{target}\" \"Authorization: Bearer\""
    ]
    
    all_dorks = google_dorks + github_dorks
    
    with open(dorks_dir / "dork_queries.txt", "w") as f:
        for d in all_dorks:
            f.write(d + "\n")
            
    with open(dorks_dir / "google_dorks.txt", "w") as f:
        for d in google_dorks:
            f.write(d + "\n")
            
    with open(dorks_dir / "github_dorks.txt", "w") as f:
        for d in github_dorks:
            f.write(d + "\n")
            
    serper_key = os.environ.get("SERPER_API_KEY")
    cse_key = os.environ.get("GOOGLE_CSE_API_KEY")
    cse_id = os.environ.get("GOOGLE_CSE_ID")
    
    dork_results = []
    dork_urls = set()
    
    if serper_key:
        print("[*] Executing Google Dorks via Serper API...")
        for query in google_dorks:
            items = _execute_serper(query, serper_key)
            for item in items:
                result = {"query": query, "url": item.get("link"), "title": item.get("title"), "snippet": item.get("snippet")}
                dork_results.append(result)
                if item.get("link"):
                    dork_urls.add(item.get("link"))
    elif cse_key and cse_id:
        print("[*] Executing Google Dorks via Google CSE API...")
        for query in google_dorks:
            items = _execute_google_cse(query, cse_key, cse_id)
            for item in items:
                result = {"query": query, "url": item.get("link"), "title": item.get("title"), "snippet": item.get("snippet")}
                dork_results.append(result)
                if item.get("link"):
                    dork_urls.add(item.get("link"))
    else:
        print("[-] SKIPPED: Dork execution skipped (SERPER_API_KEY or GOOGLE_CSE_API_KEY + GOOGLE_CSE_ID not found).")
        
    with open(dorks_dir / "dork_results.jsonl", "w") as f:
        for r in dork_results:
            f.write(json.dumps(r) + "\n")
            
    with open(dorks_dir / "dork_urls.txt", "w") as f:
        for u in sorted(dork_urls):
            f.write(u + "\n")
            
    return {"google": google_dorks, "github": github_dorks, "urls": sorted(dork_urls)}
