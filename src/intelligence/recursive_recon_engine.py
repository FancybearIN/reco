import subprocess
import json
from src.memory.mem0_client import memory_client
from src.intelligence.skill_generator import SkillEngine

class RecursiveReconEngine:
    def __init__(self):
        self.skill_engine = SkillEngine()

    def execute_native(self, command: list):
        print(f"Executing: {' '.join(command)}")
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=True,
                timeout=1200 # Allow long timeout for native tools
            )
            return result.stdout
        except subprocess.CalledProcessError as e:
            print(f"Error executing {' '.join(command)}: {e.stderr}")
            return ""
        except FileNotFoundError:
            print(f"Binary not found: {command[0]}. Ensure it is installed natively on Kali.")
            return ""
        except Exception as e:
            print(f"Timeout/Error: {e}")
            return ""


    def handle_js_file(self, js_url: str):
        print(f"Deep analyzing JS file: {js_url}")
        # Native execution of nuclei to find secrets in JS
        # nuclei -t exposures/ -target js_url
        output = self.execute_native(["nuclei", "-target", js_url, "-t", "http/exposures/", "-silent", "-jsonl"])
        if output:
            for line in output.split('\n'):
                if line.strip():
                    finding = json.loads(line)
                    memory_client.store_finding(
                        finding=f"Secret found in JS: {finding.get('info', {}).get('name')}",
                        user_id="recon_engine",
                        metadata={"type": "secret", "url": js_url, "severity": "high"}
                    )

    def handle_new_url(self, url: str):
        # 1. Native Katana for crawling
        # katana -u url -silent -jsonl
        print(f"Crawling URL: {url}")
        output = self.execute_native(["katana", "-u", url, "-silent", "-jsonl"])
        
        js_files = []
        endpoints = []

        if output:
            for line in output.split('\n'):
                if line.strip():
                    try:
                        data = json.loads(line)
                        req_url = data.get("request", {}).get("endpoint", "")
                        if req_url.endswith(".js"):
                            js_files.append(req_url)
                        else:
                            endpoints.append(req_url)
                    except json.JSONDecodeError:
                        continue

        # Trigger skill evaluation
        for endpoint in endpoints:
            skills = self.skill_engine.evaluate_target(endpoint, "")
            for skill in skills:
                memory_client.store_finding(
                    finding=f"Candidate for {skill.name} attack on {endpoint}",
                    user_id="recon_engine",
                    metadata={"type": "hypothesis", "url": endpoint, "skill": skill.name}
                )

        # Trigger recursive JS handling
        for js in js_files:
            self.handle_js_file(js)

engine = RecursiveReconEngine()
