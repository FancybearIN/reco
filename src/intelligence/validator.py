from pathlib import Path
from typing import Dict, List

from core.artifacts import append_unique_json_list


REQUIRED_REPORT_FIELDS = ["target", "asset", "endpoint", "impact"]


def _has_repro_request(candidate: Dict) -> bool:
    return bool(candidate.get("request") or candidate.get("curl") or candidate.get("curl_poc"))


def _has_repro_curl(candidate: Dict) -> bool:
    return bool(candidate.get("curl") or candidate.get("curl_poc"))


def _has_response_proof(candidate: Dict) -> bool:
    return bool(candidate.get("response") and (candidate.get("proof") or candidate.get("response")))


def report_gate(candidate: Dict) -> List[str]:
    failures = []
    for field in REQUIRED_REPORT_FIELDS:
        if not candidate.get(field):
            failures.append(f"missing {field}")
    if not _has_repro_request(candidate):
        failures.append("missing reproducible request")
    if not _has_repro_curl(candidate):
        failures.append("missing reproducible curl")
    if not _has_response_proof(candidate):
        failures.append("missing response proof")
    if not candidate.get("false_positive_checks"):
        failures.append("false-positive checks not recorded")
    if not candidate.get("manual_validation_completed"):
        failures.append("manual validation not completed")
    if not (candidate.get("severity") or candidate.get("severity_guess")):
        failures.append("severity not mapped")
    return failures


def validate(target: str, candidate: dict, base_dir: Path):
    vuln_name = candidate.get("vulnerability_class") or candidate.get("finding_type") or "candidate"
    endpoint = candidate.get("endpoint", "")
    print(f"[*] Validating candidate: {vuln_name} on {endpoint}")

    if not _has_repro_request(candidate) or not candidate.get("response"):
        candidate["status"] = "DEAD"
        candidate["state"] = "DEAD"
        candidate["dead_reason"] = "missing reproducible request/response evidence"
        return None

    failures = report_gate(candidate)
    if failures:
        candidate["status"] = "CANDIDATE"
        candidate["state"] = "VALIDATED"
        candidate["report_gate_failures"] = failures
        append_unique_json_list(base_dir / "findings" / "candidates.json", [candidate])
        return candidate

    candidate["status"] = "REPORTABLE"
    candidate["state"] = "REPORTABLE"
    append_unique_json_list(base_dir / "findings" / "reportable.json", [candidate])
    return candidate
