import json
import os

def load_vrt():
    vrt_path = "vulnerability-rating-taxonomy.json"
    if os.path.exists(vrt_path):
        with open(vrt_path, "r") as f:
            return json.load(f)
    return {}

def map_severity(finding: dict):
    print(f"[*] Mapping Severity for {finding['finding_type']}")
    ft = finding["finding_type"]
    
    vrt = load_vrt()
    # Simplified mock mapping based on requirements
    mapping = {
        "IDOR": {"category": "Broken Access Control", "subcategory": "IDOR", "priority": "P2"},
        "SQLi": {"category": "Server-Side Injection", "subcategory": "SQL Injection", "priority": "P1"},
        "RCE": {"category": "Server-Side Injection", "subcategory": "Remote Code Execution", "priority": "P1"},
        "SSRF": {"category": "Server Security Misconfiguration", "subcategory": "SSRF", "priority": "P2"},
        "Request Smuggling": {"category": "Server Security Misconfiguration", "subcategory": "HTTP Request Smuggling", "priority": "P1"},
        "Cache Poisoning": {"category": "Server Security Misconfiguration", "subcategory": "Cache Poisoning", "priority": "P3"},
        "CORS": {"category": "Server Security Misconfiguration", "subcategory": "Unsafe CORS", "priority": "P3"},
        "Open Redirect": {"category": "Unvalidated Redirects and Forwards", "subcategory": "Open Redirect", "priority": "P4"},
        "OAuth": {"category": "Server Security Misconfiguration", "subcategory": "OAuth Misconfiguration", "priority": "P2"},
        "File Upload": {"category": "Server Security Misconfiguration", "subcategory": "Unsafe File Upload", "priority": "P2"},
        "Subdomain Takeover": {"category": "Server Security Misconfiguration", "subcategory": "Misconfigured DNS", "priority": "P2"},
        "Broken Link Hijacking": {"category": "Server-Side Injection", "subcategory": "Content Spoofing", "priority": "P3"},
        "Sensitive JS Secret": {"category": "Sensitive Data Exposure", "subcategory": "Disclosure of Secrets", "priority": "P3"},
        "Exposed Admin": {"category": "Server Security Misconfiguration", "subcategory": "Exposed Portal", "priority": "P2"},
        "GraphQL Introspection": {"category": "Sensitive Data Exposure", "subcategory": "GraphQL Introspection Enabled", "priority": "P4"},
        "Clickjacking": {"category": "Server Security Misconfiguration", "subcategory": "Clickjacking", "priority": "P4"}
    }
    
    if ft in mapping:
        m = mapping[ft]
        finding["bugcrowd_vrt"] = {
            "category": m["category"],
            "subcategory": m["subcategory"],
            "priority": m["priority"]
        }
        
        pri = m["priority"]
        if pri == "P1": finding["severity"] = "Critical"
        elif pri == "P2": finding["severity"] = "High"
        elif pri == "P3": finding["severity"] = "Medium"
        else: finding["severity"] = "Low"
    else:
        finding["bugcrowd_vrt"] = {"category": "Unknown", "subcategory": "Unknown", "priority": "P4"}
        finding["severity"] = "Low"
        
    return finding
