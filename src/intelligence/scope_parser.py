import os
import shutil
from pathlib import Path

def parse_scope(target: str, scope_file: str, base_dir: Path):
    print(f"[*] Parsing scope for {target}...")
    out_scope = base_dir / "scope" / "parsed_scope.txt"
    scope_data = [target]
    if scope_file and os.path.exists(scope_file):
        with open(scope_file, "r") as f:
            lines = [l.strip() for l in f.readlines() if l.strip()]
            scope_data.extend(lines)
            
    with open(out_scope, "w") as f:
        for s in set(scope_data):
            f.write(s + "\n")
            
    return scope_data
