import requests
import time
from typing import Dict, Any

class ValidationState:
    SIGNAL = "SIGNAL"
    WEAK_EVIDENCE = "WEAK_EVIDENCE"
    REPRODUCIBLE = "REPRODUCIBLE"
    CONFIRMED = "CONFIRMED"
    EXPLOITABLE = "EXPLOITABLE"

class ValidationEngine:
    """
    Verifies reproducibility and evidence quality. Never treats weak heuristics as confirmed.
    """
    def __init__(self):
        pass

    def perform_differential_analysis(self, target_url: str, baseline_req: dict, payload_req: dict) -> float:
        """
        Compare baseline vs payload response to detect actual behavioral changes.
        Returns a differential score (0.0 to 1.0).
        """
        # Placeholder for actual HTTP request execution and AST/DOM diffing
        # In a real implementation, we'd use native tools like `curl` or `httpx` to replay
        try:
            baseline_resp = requests.get(target_url, timeout=5)
            # Example: Append a safe payload to test behavior
            payload_url = f"{target_url}?test=1"
            test_resp = requests.get(payload_url, timeout=5)
            
            # Simple content length differential
            len_diff = abs(len(baseline_resp.text) - len(test_resp.text))
            
            if len_diff > 50 or baseline_resp.status_code != test_resp.status_code:
                return 0.8 # High variance
            return 0.1 # Low variance
        except:
            return 0.0

    def perform_timing_analysis(self, target_url: str, payload: str) -> bool:
        """
        Send payload designed to sleep/delay and measure response time.
        """
        try:
            start = time.time()
            requests.get(f"{target_url}?q={payload}", timeout=15)
            end = time.time()
            if (end - start) > 9: # Assuming a 10s sleep payload
                return True
        except requests.exceptions.ReadTimeout:
            return True
        except:
            pass
        return False

    def check_oob_interaction(self, interactsh_data: list) -> bool:
        """
        Validate DNS callback / OOB interaction via interactsh.
        """
        if interactsh_data and len(interactsh_data) > 0:
            return True
        return False

    def evaluate_evidence(self, finding_data: Dict[str, Any]) -> str:
        """
        Evaluates collected evidence and returns a strict ValidationState.
        """
        oob_confirmed = finding_data.get("oob_confirmed", False)
        diff_score = finding_data.get("differential_score", 0.0)
        reproducible = finding_data.get("reproducible", False)

        if oob_confirmed:
            return ValidationState.EXPLOITABLE
        if reproducible and diff_score > 0.8:
            return ValidationState.CONFIRMED
        if reproducible:
            return ValidationState.REPRODUCIBLE
        if diff_score > 0.4:
            return ValidationState.WEAK_EVIDENCE
            
        return ValidationState.SIGNAL

validation_engine = ValidationEngine()
