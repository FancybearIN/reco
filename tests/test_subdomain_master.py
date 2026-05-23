import json
import shutil
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from core.pipeline import create_output_structure
from core.artifacts import load_json
from recon.recon_chain import parse_subdomain_master_outputs, run_subdomain_master


class TestSubdomainMasterIntegration(unittest.TestCase):
    def setUp(self):
        self.target = "example.com"
        self.base_dir = create_output_structure(self.target)

    def tearDown(self):
        if Path("runs").exists():
            shutil.rmtree("runs")

    def _write_master_outputs(self, out_dir: Path, include_coverage: bool = True):
        (out_dir / "httpx").mkdir(parents=True, exist_ok=True)
        (out_dir / "takeover").mkdir(parents=True, exist_ok=True)
        (out_dir / "logs").mkdir(parents=True, exist_ok=True)
        (out_dir / "all_unique_final.txt").write_text("www.example.com\napi.example.com\n", encoding="utf-8")
        (out_dir / "resolved.txt").write_text("www.example.com\napi.example.com\n", encoding="utf-8")
        (out_dir / "httpx" / "httpx_alive.txt").write_text("https://api.example.com/login\n", encoding="utf-8")
        (out_dir / "httpx" / "httpx_full.jsonl").write_text(
            json.dumps(
                {
                    "url": "https://api.example.com/login",
                    "status_code": 200,
                    "title": "Login",
                    "tech": ["nginx"],
                    "webserver": "nginx",
                }
            )
            + "\n",
            encoding="utf-8",
        )
        (out_dir / "takeover" / "cnames.txt").write_text("old.example.com old.github.io\n", encoding="utf-8")
        (out_dir / "takeover" / "candidates.txt").write_text("old.example.com old.github.io\n", encoding="utf-8")
        (out_dir / "missing_tools.txt").write_text("subfinder\namass\n", encoding="utf-8")
        (out_dir / "summary.txt").write_text("Subdomain Master Recon Summary\n", encoding="utf-8")
        if include_coverage:
            (out_dir / "method_coverage.jsonl").write_text(
                json.dumps({"method": "subfinder", "status": "missing", "output": "", "note": "tool not installed"}) + "\n"
                + json.dumps({"method": "httpx_full", "status": "ran", "output": "httpx/httpx_full.jsonl", "note": "full web probe"}) + "\n",
                encoding="utf-8",
            )

    def test_run_subdomain_master_invokes_script_and_parses_outputs(self):
        def fake_run(command, capture_output, text, check, timeout):
            out_dir = Path(command[2])
            self._write_master_outputs(out_dir)
            return SimpleNamespace(returncode=0, stdout="ok", stderr="")

        with patch("recon.recon_chain.subprocess.run", side_effect=fake_run) as mocked:
            result = run_subdomain_master(self.target, ["*.example.com"], self.base_dir)

        self.assertTrue(mocked.called)
        self.assertEqual(Path(mocked.call_args.args[0][0]), Path("scripts/recon/subdomain_master.sh"))
        self.assertTrue(result["complete"])
        self.assertTrue((self.base_dir / "recon" / "subdomains.txt").exists())
        self.assertTrue((self.base_dir / "httpx" / "httpx_full.jsonl").exists())
        self.assertIn("subfinder", result["missing_tools"])

        surfaces = load_json(self.base_dir / "surfaces" / "attack_surfaces.json", [])
        tasks = load_json(self.base_dir / "tasks" / "validation_tasks.json", [])
        discarded = load_json(self.base_dir / "surfaces" / "discarded_items.json", [])
        self.assertTrue(any(surface["category"] == "login/auth" for surface in surfaces))
        self.assertTrue(any(task["vulnerability_class"] == "subdomain takeover" for task in tasks))
        self.assertTrue(any(item["item"] == "subfinder" for item in discarded))

    def test_parse_outputs_requires_method_coverage_for_completion(self):
        out_dir = self.base_dir / "recon" / "subdomains"
        self._write_master_outputs(out_dir, include_coverage=False)

        result = parse_subdomain_master_outputs(self.target, out_dir, self.base_dir)

        self.assertFalse(result["complete"])
        status = load_json(self.base_dir / "recon" / "subdomain_master_status.json", {})
        self.assertFalse(status["complete"])
        discarded = load_json(self.base_dir / "surfaces" / "discarded_items.json", [])
        self.assertTrue(any("method_coverage.jsonl missing" in item["reason"] for item in discarded))

    def test_subdomain_master_script_is_limited_to_subdomains_and_takeover(self):
        script = Path("scripts/recon/subdomain_master.sh").read_text(encoding="utf-8")
        self.assertIn("subfinder", script)
        self.assertIn("CNAME takeover checks", script)
        self.assertNotIn("httpx probing", script)
        self.assertNotIn("URL/JS scraping", script)
        self.assertNotIn("VHost candidate prep", script)
        self.assertNotIn("Cloud candidates", script)


if __name__ == "__main__":
    unittest.main()
