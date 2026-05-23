import subprocess
import json
import os

class ReconTool:
    def __init__(self, name: str):
        self.name = name

    def run(self, command: list):
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout
        except subprocess.CalledProcessError as e:
            print(f"Error running {self.name}: {e.stderr}")
            return None

class Subfinder(ReconTool):
    def __init__(self):
        super().__init__("subfinder")

    def enumerate(self, domain: str):
        # -d domain -silent -nc (no color) -all
        command = ["subfinder", "-d", domain, "-silent", "-nc"]
        output = self.run(command)
        if output:
            return [line.strip() for line in output.split("\n") if line.strip()]
        return []

class Httpx(ReconTool):
    def __init__(self):
        super().__init__("httpx")

    def probe(self, domains: list):
        # Use stdin for domains
        process = subprocess.Popen(
            ["httpx", "-silent", "-json", "-sc", "-td", "-title"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        stdout, stderr = process.communicate(input="\n".join(domains))
        
        results = []
        for line in stdout.split("\n"):
            if line.strip():
                results.append(json.loads(line))
        return results

class Nuclei(ReconTool):
    def __init__(self):
        super().__init__("nuclei")

    def scan(self, target: str, templates: list = None):
        command = ["nuclei", "-target", target, "-silent", "-jsonl"]
        if templates:
            for t in templates:
                command.extend(["-t", t])
        
        output = self.run(command)
        results = []
        if output:
            for line in output.split("\n"):
                if line.strip():
                    results.append(json.loads(line))
        return results
