import os
import sys
import requests
import json
import argparse

def fetch_structured_scope(identifier, token, handle):
    """
    Fetches structured scope from HackerOne API.
    """
    url = f"https://api.hackerone.com/v1/programs/{handle}/structured_scopes"
    auth = (identifier, token)
    headers = {"Accept": "application/json"}
    
    scopes = []
    page = 1
    
    while True:
        params = {"page[number]": page, "page[size]": 100}
        response = requests.get(url, auth=auth, headers=headers, params=params)
        
        if response.status_code != 200:
            print(f"Error: Received status code {response.status_code}", file=sys.stderr)
            print(response.text, file=sys.stderr)
            break
            
        data = response.json()
        page_data = data.get("data", [])
        if not page_data:
            break
            
        scopes.extend(page_data)
        
        # Check for next page
        links = data.get("links", {})
        if "next" not in links:
            break
        page += 1
        
    return scopes

def parse_scope(scopes):
    """
    Parses the structured scope into a more readable format.
    """
    parsed = {
        "in_scope": [],
        "out_of_scope": []
    }
    
    for item in scopes:
        attributes = item.get("attributes", {})
        asset = {
            "identifier": attributes.get("asset_identifier"),
            "type": attributes.get("asset_type"),
            "instruction": attributes.get("instruction"),
            "eligible_for_bounty": attributes.get("eligible_for_bounty"),
            "eligible_for_submission": attributes.get("eligible_for_submission")
        }
        
        if attributes.get("eligible_for_submission"):
            parsed["in_scope"].append(asset)
        else:
            parsed["out_of_scope"].append(asset)
            
    return parsed

def main():
    parser = argparse.ArgumentParser(description="Fetch and parse HackerOne structured scope.")
    parser.add_argument("--handle", help="HackerOne program handle (e.g., att)", default=os.getenv("H1_PROGRAM_HANDLE", "att"))
    parser.add_argument("--identifier", help="HackerOne API Identifier", default=os.getenv("H1_API_IDENTIFIER"))
    parser.add_argument("--token", help="HackerOne API Token", default=os.getenv("H1_API_TOKEN"))
    parser.add_argument("--output", help="Output file (JSON)", default=None)
    parser.add_argument("--raw", action="store_true", help="Output raw JSON from API")
    
    args = parser.parse_args()
    
    if not args.identifier or not args.token:
        print("Error: HackerOne API Identifier and Token must be provided via arguments or environment variables (H1_API_IDENTIFIER, H1_API_TOKEN).", file=sys.stderr)
        sys.exit(1)
        
    raw_scopes = fetch_structured_scope(args.identifier, args.token, args.handle)
    
    if args.raw:
        output_data = raw_scopes
    else:
        output_data = parse_scope(raw_scopes)
        
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(output_data, f, indent=2)
        print(f"Scope saved to {args.output}")
    else:
        print(json.dumps(output_data, indent=2))

if __name__ == "__main__":
    main()
