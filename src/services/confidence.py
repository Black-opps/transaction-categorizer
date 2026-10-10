# transaction-categorizer/src/services/confidence.py - NEW

from typing import Any, Dict, List

from src.models.transaction import Category


class ConfidenceScorer:
    """Enhanced confidence scoring for categorization"""

    @classmethod
    def calculate(
        cls, category: Category, matched_rules: List[str], description: str
    ) -> float:
        """Calculate confidence score"""

        base_score = 0.7  # Base confidence

        # Rule count bonus
        if len(matched_rules) >= 2:
            base_score += 0.1

        # Multiple keyword matches
        matched_keywords = sum(
            1 for rule in matched_rules if rule in description.lower()
        )
        if matched_keywords > 0:
            base_score += min(0.15, matched_keywords * 0.05)

        # Category-specific adjustments
        if category in [Category.UTILITIES, Category.AIRTIME_DATA]:
            # These are usually very distinct
            base_score += 0.05

        # Description length bonus
        if len(description) > 50:
            base_score += 0.05

        return min(1.0, base_score)
