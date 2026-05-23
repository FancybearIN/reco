import os
import re

def parse_lead_queue(file_path):
    if not os.path.exists(file_path):
        return []
    
    with open(file_path, 'r') as f:
        lines = f.readlines()
    
    leads = []
    # Simple markdown table parser
    for line in lines:
        if line.startswith('|') and 'Priority' not in line and '---' not in line:
            parts = [p.strip() for p in line.split('|')]
            if len(parts) >= 5:
                leads.append({
                    'priority': parts[1],
                    'type': parts[2],
                    'reason': parts[3],
                    'url': parts[4]
                })
    return leads

def generate_plan(lead):
    ltype = lead['type']
    url = lead['url']
    
    plan = []
    if 'Open Redirect' in ltype or 'OAuth' in ltype:
        plan = [
            f"1. **Regex Bypass**: Attempt to redirect to a subdomain of the target controlled by the attacker (e.g., {url.split('?')[0]}?URL=www.att.com.evil.com).",
            "2. **Parameter Pollution**: Supply the redirect parameter multiple times with different values (e.g., ?URL=https://google.com&URL=https://evil.com) to see which one the server honors.",
            "3. **Token Leakage**: If part of an OAuth flow, check if the `redirect_uri` can be pointed to an external domain to leak `code` or `access_token` via URL fragments or query params.",
            "4. **Fragment Injection**: Test if the redirect can be forced to include a fragment that might be processed by a client-side script on the destination page."
        ]
    elif 'Sensitive Admin Panel' in ltype:
        plan = [
            "1. **Tech Stack Identification**: Use `httpx` or `wappalyzer` to identify the specific version of the panel/software.",
            "2. **Default Credentials**: Test common default credentials for the identified tech stack (e.g., admin:admin, root:password).",
            "3. **Directory Brute Force**: Run a targeted wordlist for common sensitive files like `.env`, `.git/config`, `backup.zip`, and `phpinfo.php`.",
            "4. **Known Vulnerabilities**: Search for N-day exploits for the specific version identified in step 1."
        ]
    elif 'HTTP/2 Rapid Reset' in ltype:
        plan = [
            "1. **Baseline Verification**: Run `att-bounty/05_testing/test_h2.py` to confirm the vulnerability against the target.",
            "2. **Concurrency Testing**: Measure the server's response time when sending multiple RST_STREAM frames to assess the impact.",
            "3. **WAF Bypass**: Test if certain headers or variations in the H2 stream can bypass security filters."
        ]
    else:
        plan = [
            "1. **Manual Inspection**: Visit the URL and observe the behavior of the identified parameter or feature.",
            "2. **Fuzzing**: Use `ffuf` or `wfuzz` to test for common vulnerabilities related to the lead type.",
            "3. **Request Manipulation**: Try changing HTTP methods (GET, POST, PUT) and headers to see if the server responds differently."
        ]
    
    return plan

def main():
    lead_queue_path = '/home/kali/reco/att-bounty/08_memory/lead_queue.md'
    output_path = '/home/kali/reco/att-bounty/08_memory/strategic_plan.md'
    
    leads = parse_lead_queue(lead_queue_path)
    high_priority_leads = [l for l in leads if l['priority'] == 'High']
    
    if not high_priority_leads:
        print("No high priority leads found.")
        return

    with open(output_path, 'w') as f:
        f.write("# Strategic Attack Plan\n\n")
        f.write("Generated based on High priority leads in the queue.\n\n")
        
        for lead in high_priority_leads:
            f.write(f"## Target: {lead['url']}\n")
            f.write(f"- **Type**: {lead['type']}\n")
            f.write(f"- **Reason**: {lead['reason']}\n")
            f.write("- **Attack Plan**:\n")
            plan = generate_plan(lead)
            for step in plan:
                f.write(f"  {step}\n")
            f.write("\n---\n\n")
    print(f"Strategic plan generated at {output_path}")

if __name__ == "__main__":
    main()
