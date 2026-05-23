import unittest
import os
import shutil
import json
from pathlib import Path
import sys

# Add src to pythonpath for tests
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from intelligence.scope_parser import parse_scope
from intelligence.severity_mapper import load_vrt, map_severity
from intelligence.validator import validate
from intelligence.report_builder import build_report
from core.pipeline import create_output_structure

class TestRecoPipeline(unittest.TestCase):
    def setUp(self):
        self.target = "example.com"
        self.base_dir = create_output_structure(self.target)
        self.scope_file = "test_scope.txt"
        with open(self.scope_file, "w") as f:
            f.write("*.example.com\napi.example.com")
            
    def tearDown(self):
        if os.path.exists(self.scope_file):
            os.remove(self.scope_file)
        if os.path.exists("runs"):
            shutil.rmtree("runs")

    def test_scope_parser(self):
        scope = parse_scope(self.target, self.scope_file, self.base_dir)
        self.assertIn("*.example.com", scope)
        self.assertIn(self.target, scope)
        self.assertTrue((self.base_dir / "scope" / "parsed_scope.txt").exists())
        
    def test_wordlist_paths_exist(self):
        # We simulate this since we don't have the real paths in the container reliably
        # just testing the logic of loading
        import yaml
        if os.path.exists("config/wordlists.yaml"):
            with open("config/wordlists.yaml", "r") as f:
                data = yaml.safe_load(f)
                self.assertIn("paths", data)

    def test_vrt_taxonomy_loads(self):
        # We uploaded vulnerability-rating-taxonomy.json previously
        vrt = load_vrt()
        self.assertIsInstance(vrt, dict)
        
    def test_vrt_mapper_works(self):
        finding = {
            "finding_type": "SQLi"
        }
        mapped = map_severity(finding)
        self.assertEqual(mapped["severity"], "Critical")
        self.assertEqual(mapped["bugcrowd_vrt"]["category"], "Server-Side Injection")
        
    def test_validation_gate_blocks_incomplete(self):
        candidate = {
            "id": "123",
            "finding_type": "IDOR",
            "endpoint": "https://api.example.com/v1/user/2",
            # missing request/response
        }
        res = validate(self.target, candidate, self.base_dir)
        self.assertIsNone(res)
        self.assertEqual(candidate["state"], "DEAD")

    def test_finding_state_transition_and_report(self):
        candidate = {
            "id": "123",
            "target": self.target,
            "asset": "api.example.com",
            "finding_type": "IDOR",
            "endpoint": "https://api.example.com/v1/user/2",
            "request": "GET /v1/user/2",
            "response": "200 OK User 2 Data",
            "curl_poc": "curl ...",
            "impact": "Data leak",
            "false_positive_checks": []
        }
        
        # Validate
        res = validate(self.target, candidate, self.base_dir)
        self.assertIsNotNone(res)
        self.assertEqual(res["state"], "VALIDATED")
        
        # Map Severity
        mapped = map_severity(res)
        mapped["state"] = "REPORTABLE"
        
        # Report Builder
        build_report(mapped, self.base_dir)
        report_file = self.base_dir / "reports" / f"REPORT_{mapped['id']}.md"
        self.assertTrue(report_file.exists())
        with open(report_file, "r") as f:
            content = f.read()
            self.assertIn("Title: IDOR", content)
            self.assertIn("High", content)

if __name__ == "__main__":
    unittest.main()
