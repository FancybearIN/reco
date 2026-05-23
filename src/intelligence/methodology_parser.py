import os
import glob
import re
try:
    from src.memory.mem0_client import memory_client
except Exception:
    try:
        from memory.mem0_client import memory_client
    except Exception:
        memory_client = None
from pathlib import Path
from core.artifacts import write_json, write_lines

class MethodologyEngine:
    def __init__(self, data_dir: str = "data/methodologies"):
        self.data_dir = data_dir

    def extract_markdown_chunks(self, file_path: str):
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        chunks = re.split(r'\n(?=##? )', content)
        return [chunk.strip() for chunk in chunks if len(chunk.strip()) > 50]

    def ingest_repo(self, repo_name: str, methodology_type: str):
        repo_path = os.path.join(self.data_dir, repo_name)
        if not os.path.exists(repo_path):
            print(f"Repo {repo_path} not found.")
            return

        print(f"Ingesting {repo_name} methodologies into Mem0...")
        md_files = glob.glob(f"{repo_path}/**/*.md", recursive=True)
        
        count = 0
        for file_path in md_files:
            if "README" in file_path.upper() and len(md_files) > 10:
                continue
            
            category = os.path.basename(os.path.dirname(file_path))
            filename = os.path.basename(file_path).replace(".md", "")
            
            chunks = self.extract_markdown_chunks(file_path)
            for chunk in chunks:
                metadata = {
                    "source": repo_name,
                    "category": category,
                    "topic": filename,
                    "type": "offensive_methodology",
                    "methodology_type": methodology_type
                }
                
                # Semantic filtering before ingestion to keep context clean
                if "```" in chunk or "payload" in chunk.lower() or "bypass" in chunk.lower() or "exploit" in chunk.lower():
                    # We store the chunk, Mem0 automatically embeds it via Qdrant/OpenAI
                    if memory_client:
                        memory_client.store_finding(
                            finding=chunk[:1500], # Prevent massive token blasts
                            user_id="system_methodology",
                            metadata=metadata
                        )
                        count += 1
        return count

    def retrieve_methodologies(self, finding_description: str, limit: int = 3):
        """
        Retrieves semantically relevant methodologies based on a discovered finding.
        Example finding_description: "SVG upload endpoint found without CSP"
        """
        print(f"Retrieving methodology for finding: {finding_description}")
        if not memory_client:
            return []
        results = memory_client.retrieve_context(finding_description, user_id="system_methodology")
        
        methodologies = []
        for res in results[:limit]:
            # Extract metadata and text
            meta = res.get("metadata", {})
            if meta.get("type") == "offensive_methodology":
                methodologies.append({
                    "topic": meta.get("topic"),
                    "category": meta.get("category"),
                    "content": res.get("text")
                })
        return methodologies

    def build_local_playbooks(self, base_dir: Path = None):
        """
        Extract reusable local methodology snippets without requiring Mem0.
        Output is intentionally structured for pipeline stages: payload seeds,
        one-liners, validation notes, bypass notes, and provider key checks.
        """
        sources = [
            "AllAboutBugBounty",
            "awesome-oneliner-bugbounty",
            "bugbounty-cheatsheet",
            "gmapsapiscanner",
            "hacktricks",
            "HowToHunt",
            "keyhacks",
            "PayloadsAllTheThings",
            "Resources-for-Beginner-Bug-Bounty-Hunters",
        ]
        keywords = re.compile(
            r"(httpx|subfinder|assetfinder|amass|dnsx|gau|waybackurls|katana|ffuf|arjun|nuclei|payload|bypass|cors|sqli|ssrf|idor|bola|cache|takeover|swagger|openapi|graphql|upload|oauth|firebase|github|s3|key)",
            re.I,
        )
        playbooks = []
        param_words = set()
        for source in sources:
            repo = Path(self.data_dir) / source
            if not repo.exists():
                continue
            for path in repo.rglob("*.md"):
                if path.stat().st_size > 2_000_000:
                    continue
                content = path.read_text(encoding="utf-8", errors="ignore")
                chunks = self.extract_markdown_chunks(str(path))
                for chunk in chunks:
                    if not keywords.search(chunk):
                        continue
                    code_blocks = re.findall(r"```(?:bash|sh|shell|http|json)?\n(.*?)```", chunk, re.S | re.I)
                    words = re.findall(r"\b(?:redirect_uri|url|uri|next|return|callback|file|path|id|user_id|account_id|q|query|search|token|key|debug|admin|upload)\b", chunk, re.I)
                    param_words.update(word.lower() for word in words)
                    playbooks.append(
                        {
                            "source": source,
                            "path": str(path),
                            "topic": path.stem,
                            "commands": [cmd.strip()[:1000] for cmd in code_blocks[:5]],
                            "notes": re.sub(r"\s+", " ", chunk)[:1200],
                        }
                    )
        if base_dir:
            write_json(base_dir / "playbooks" / "methodology_playbooks.json", playbooks)
            write_lines(base_dir / "fuzz" / "methodology_params.txt", param_words)
        return {"playbooks": playbooks, "param_words": sorted(param_words)}

if __name__ == "__main__":
    engine = MethodologyEngine()
    engine.ingest_repo("hacktricks", "general_web")
    engine.ingest_repo("HowToHunt", "bug_bounty_specific")
