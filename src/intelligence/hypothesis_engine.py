from pathlib import Path


SURFACE_TO_HYPOTHESES = {
    "APIs": ["IDOR/BOLA/API authz", "SQLi", "SSRF"],
    "login/auth": ["IDOR/BOLA/API authz", "OAuth redirect/callback abuse"],
    "admin panels": ["admin panel exposure", "RCE/CVE exploitability validation"],
    "file upload surfaces": ["upload abuse"],
    "swagger/openapi/graphql": ["Swagger/OpenAPI/GraphQL abuse", "IDOR/BOLA/API authz"],
    "redirect/callback surfaces": ["OAuth redirect/callback abuse", "SSRF"],
    "cacheable endpoints": ["cache poisoning"],
    "cloud/storage": ["cloud metadata exposure", "exposed secrets"],
    "staging/dev/test": ["sensitive file/content discovery"],
    "exposed dashboards": ["admin panel exposure"],
    "takeover candidates": ["subdomain takeover"],
    "old/vulnerable tech": ["RCE/CVE exploitability validation"],
    "unusual ports": ["RCE/CVE exploitability validation"],
    "JS": ["exposed secrets"],
}


def generate_hypotheses(target: str, classified_surface: dict, profile: str, base_dir: Path):
    print(f"[*] Generating Hypotheses for {target} with profile {profile}...")
    hypotheses = []
    for category, endpoints in classified_surface.items():
        for endpoint in endpoints:
            for vuln_class in SURFACE_TO_HYPOTHESES.get(category, ["sensitive file/content discovery"]):
                hypotheses.append(
                    {
                        "type": vuln_class,
                        "endpoint": endpoint,
                        "surface_category": category,
                        "methodology_source": "HowToHunt/PayloadsAllTheThings/bugbounty-cheatsheet",
                    }
                )
    return hypotheses
