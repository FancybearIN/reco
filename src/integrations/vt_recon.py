import requests
import json
import sys

def vt_recon(domain, api_key):
    print(f"[*] Starting VirusTotal recon for {domain}...")
    
    # VT API v2 Domain Report
    url = 'https://www.virustotal.com/vtapi/v2/domain/report'
    params = {'apikey': api_key, 'domain': domain}
    
    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            
            # Extract subdomains
            subdomains = data.get('subdomains', [])
            print(f"[+] Found {len(subdomains)} subdomains.")
            
            # Extract detected URLs (often good for finding bugs)
            detected_urls = data.get('detected_urls', [])
            print(f"[+] Found {len(detected_urls)} detected URLs.")
            
            # Save results
            result = {
                'domain': domain,
                'subdomains': subdomains,
                'detected_urls': detected_urls,
                'resolutions': data.get('resolutions', []),
                'whois': data.get('whois', '')
            }
            
            filename = f"vt_recon_{domain}.json"
            with open(filename, 'w') as f:
                json.dump(result, f, indent=4)
            print(f"[+] Results saved to {filename}")
            
            # Initial bug-hunting scan
            print("\n[*] Analyzing for potential leads...")
            leads = []
            
            # 1. Look for interesting subdomains (dev, api, etc.)
            interesting_keywords = ['dev', 'staging', 'test', 'admin', 'api', 'internal', 'vpn', 'jira', 'jenkins', 'gitlab', 'monitoring', 'grafana', 'prometheus']
            for sub in subdomains:
                if any(keyword in sub.lower() for keyword in interesting_keywords):
                    leads.append({'type': 'Interesting Subdomain', 'asset': sub, 'reason': 'Matches sensitive keyword'})
            
            # 2. Look for suspicious URLs
            bug_patterns = ['config', 'env', '.git', 'backup', 'sql', 'phpinfo', 'swagger', 'graphql', 'auth', 'login']
            for entry in detected_urls:
                url_str = entry.get('url', '')
                if any(pattern in url_str.lower() for pattern in bug_patterns):
                    leads.append({'type': 'Suspicious URL', 'asset': url_str, 'reason': 'Matches bug pattern'})
            
            if leads:
                print(f"[+] Identified {len(leads)} potential leads:")
                for lead in leads:
                    print(f"  - [{lead['type']}] {lead['asset']} ({lead['reason']})")
            else:
                print("[-] No immediate high-value leads found in VT report.")
                
            return result
        else:
            print(f"[-] VT API Error: {response.status_code}")
            print(response.text)
            return None
    except Exception as e:
        print(f"[-] Error: {e}")
        return None

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 vt_recon.py <domain> <api_key>")
        sys.exit(1)
        
    domain = sys.argv[1]
    api_key = sys.argv[2]
    vt_recon(domain, api_key)
