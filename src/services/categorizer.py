"""
Transaction categorizer service - core categorization logic.
"""
import logging
import time
from typing import List, Dict, Tuple, Optional
from uuid import UUID
from datetime import datetime

from ..models.transaction import (
    Transaction,
    CategorizedTransaction,
    Category,
    CategorizationRequest,
    CategorizationResponse,
    CategorizationRule
)
# from .rules import CategorizationRules  # Uncomment when rules.py is ready

logger = logging.getLogger(__name__)


class TransactionCategorizer:
    """
    Service responsible for categorizing transactions using rule-based logic.
    Ready to be extended with ML or more advanced matching.
    """

    def __init__(self):
        # self.rules_engine = CategorizationRules()  # Uncomment when implemented
        self.rules: List[CategorizationRule] = self._load_default_rules()

    def _load_default_rules(self) -> List[CategorizationRule]:
        """Temporary hardcoded rules - replace with DB or file loading later."""
        return [
            CategorizationRule(
                name="Salary detection",
                patterns=["salary", "payment received", "mpesa from"],
                category=Category.REVENUE,
                confidence=0.95,
                priority=10
            ),
            CategorizationRule(
                name="Utilities - electricity",
                patterns=["electricity", "kplc", "power", "bill"],
                category=Category.UTILITIES,
                confidence=0.90,
                priority=5
            ),
            # Add more rules here or load from DB/file
        ]

    async def categorize_batch(
        self,
        transactions: List[Transaction],
        tenant_id: UUID
    ) -> CategorizationResponse:
        """Categorize multiple transactions for one tenant."""
        start_time = time.time()

        categorized = []
        stats: Dict[str, int] = {cat.value: 0 for cat in Category}

        for tx in transactions:
            category, confidence, applied_rules = await self._categorize_single(tx)
            stats[category.value] += 1

            categorized.append(
                CategorizedTransaction(
                    **tx.model_dump(),
                    tenant_id=tenant_id,
                    category=category,
                    confidence=confidence,
                    category_rules_applied=applied_rules,
                    categorized_at=datetime.utcnow()
                )
            )

        processing_time_ms = (time.time() - start_time) * 1000

        logger.info(
            f"Batch categorized {len(transactions)} transactions in {processing_time_ms:.2f}ms"
        )

        return CategorizationResponse(
            categorized_transactions=categorized,
            stats=stats,
            processing_time_ms=processing_time_ms
        )

    async def categorize_single_transaction(
        self,
        transaction: Transaction,
        tenant_id: UUID
    ) -> CategorizedTransaction:
        """Categorize one transaction (used by /single endpoint)."""
        category, confidence, applied_rules = await self._categorize_single(transaction)

        return CategorizedTransaction(
            **transaction.model_dump(),
            tenant_id=tenant_id,
            category=category,
            confidence=confidence,
            category_rules_applied=applied_rules,
            categorized_at=datetime.utcnow()
        )

    async def _categorize_single(
        self,
        transaction: Transaction
    ) -> Tuple[Category, float, List[str]]:
        """
        Core categorization logic.
        Returns (category, confidence, list_of_applied_rule_names)
        """
        description = transaction.description.lower()
        applied_rules = []
        max_confidence = 0.0
        best_category = Category.OTHER

        # Simple rule matching (priority not yet implemented)
        for rule in self.rules:
            if rule.is_active and any(p.lower() in description for p in rule.patterns):
                if rule.confidence > max_confidence:
                    max_confidence = rule.confidence
                    best_category = rule.category
                    applied_rules = [rule.name]

        # Fallback
        if best_category == Category.OTHER:
            max_confidence = 0.5
            applied_rules = ["fallback_rule"]

        logger.debug(
            f"Categorized '{transaction.description}' → {best_category} "
            f"(conf: {max_confidence:.2f}, rules: {applied_rules})"
        )

        return best_category, max_confidence, applied_rules

    async def get_rules(self) -> List[Dict]:
        """Return list of active rules in simple dict format."""
        return [
            {
                "id": str(rule.id),
                "name": rule.name,
                "patterns": rule.patterns,
                "category": rule.category.value,
                "confidence": rule.confidence,
                "priority": rule.priority
            }
            for rule in self.rules if rule.is_active
        ]

    async def add_rule(self, rule: CategorizationRule) -> Dict:
        """Add or update rule (in-memory for now)."""
        # In real app: save to DB or file
        self.rules.append(rule)
        return {
            "id": str(rule.id),
            "name": rule.name,
            "category": rule.category.value,
            "patterns": rule.patterns,
            "confidence": rule.confidence
        }

    async def remove_rule(self, rule_id: UUID) -> None:
        """Remove rule by ID (in-memory)."""
        self.rules = [r for r in self.rules if r.id != rule_id]

    async def get_stats(self) -> Dict:
        """Basic stats about rules and categories."""
        return {
            "total_rules": len(self.rules),
            "active_rules": len([r for r in self.rules if r.is_active]),
            "categories_supported": [cat.value for cat in Category],
            "highest_confidence_rule": max(
                (r.confidence for r in self.rules), default=0.0
            )
        }