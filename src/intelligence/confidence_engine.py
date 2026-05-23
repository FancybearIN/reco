from typing import Dict, Any
from src.intelligence.validation_engine import ValidationState

class ConfidenceEngine:
    """
    Enforces rigorous evidence standards. Low-confidence findings remain hypotheses.
    """
    def __init__(self):
        pass

    def score_confidence(self, validation_state: str, diff_score: float, methodology_match: bool) -> float:
        """
        Calculates a confidence score (0.0 to 1.0).
        """
        base_score = 0.1

        if validation_state == ValidationState.EXPLOITABLE:
            base_score += 0.8
        elif validation_state == ValidationState.CONFIRMED:
            base_score += 0.6
        elif validation_state == ValidationState.REPRODUCIBLE:
            base_score += 0.4
        elif validation_state == ValidationState.WEAK_EVIDENCE:
            base_score += 0.2

        if methodology_match:
            base_score += 0.1
            
        if diff_score > 0.8:
            base_score += 0.1

        return min(base_score, 1.0)

    def is_actionable(self, confidence_score: float) -> bool:
        """
        Prefer silence over false positives. Only report highly confident findings.
        """
        return confidence_score >= 0.7

confidence_engine = ConfidenceEngine()
