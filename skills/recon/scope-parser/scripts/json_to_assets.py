import json
import sys
import argparse

def json_to_assets(json_data):
    """
    Extracts identifiers from parsed JSON scope.
    """
    assets = []
    for asset in json_data.get("in_scope", []):
        if asset.get("identifier"):
            assets.append(asset.get("identifier"))
    return sorted(set(assets))

def main():
    parser = argparse.ArgumentParser(description="Convert parsed HackerOne JSON scope to asset list.")
    parser.add_argument("input", help="Input JSON file")
    parser.add_argument("--output", help="Output text file", default=None)
    
    args = parser.parse_args()
    
    try:
        with open(args.input, 'r') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error reading {args.input}: {e}", file=sys.stderr)
        sys.exit(1)
        
    assets = json_to_assets(data)
    
    if args.output:
        with open(args.output, 'w') as f:
            for asset in assets:
                f.write(f"{asset}\n")
        print(f"Assets saved to {args.output}")
    else:
        for asset in assets:
            print(asset)

if __name__ == "__main__":
    main()
