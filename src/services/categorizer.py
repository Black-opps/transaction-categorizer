# src/services/categorizer.py
import time
from typing import Dict, List

import httpx
from sqlalchemy.orm import Session
from src.core.database import CategorizedTransaction as DBCategorizedTransaction
from src.core.database import CategoryRule
from src.models.transaction import CategorizedTransaction, Category, Transaction
from src.services.rules import MpesaRuleEngine


class CategorizerService:
    """Main categorizer service with M-PESA specific logic."""

    def __init__(self, db: Session):
        self.db = db
        self.rule_engine = MpesaRuleEngine()
        self.last_processing_time_ms = 0

    async def categorize_batch(
        self, tenant_id: str, transactions: List[Transaction]
    ) -> List[CategorizedTransaction]:
        """Categorize a batch of transactions."""

        start_time = time.time()
        categorized = []

        for tx in transactions:
            cat_tx = await self.categorize_single(tenant_id, tx)
            categorized.append(cat_tx)

            # Store in database
            db_tx = DBCategorizedTransaction(
                tenant_id=tenant_id,
                original_description=tx.description,
                amount=tx.amount,
                transaction_type=tx.transaction_type.value,
                transaction_date=tx.transaction_date,
                category=cat_tx.category.value,
                confidence=cat_tx.confidence,
                rules_applied=",".join(cat_tx.category_rules_applied),
                phone_number=tx.phone_number,
                reference=tx.reference,
            )
            self.db.add(db_tx)

        self.db.commit()
        self.last_processing_time_ms = (time.time() - start_time) * 1000

        return categorized

    async def categorize_single(
        self, tenant_id: str, transaction: Transaction
    ) -> CategorizedTransaction:
        """Categorize a single transaction."""

        # First check custom tenant rules
        custom_rules = (
            self.db.query(CategoryRule)
            .filter(CategoryRule.tenant_id == tenant_id, CategoryRule.is_active == True)
            .order_by(CategoryRule.priority.desc())
            .all()
        )

        for rule in custom_rules:
            import re

            if re.search(rule.pattern, transaction.description, re.IGNORECASE):
                return CategorizedTransaction(
                    tenant_id=tenant_id,
                    **transaction.dict(),
                    category=Category(rule.category),
                    confidence=rule.confidence,
                    category_rules_applied=[rule.name],
                )

        # Use M-PESA rule engine
        category, confidence, matched_rules = self.rule_engine.categorize(
            transaction.description,
            transaction.amount,
            transaction.transaction_type.value,
        )

        # Map string category to enum
        category_enum = Category.OTHER
        for c in Category:
            if c.value == category:
                category_enum = c
                break

        return CategorizedTransaction(
            tenant_id=tenant_id,
            **transaction.dict(),
            category=category_enum,
            confidence=confidence,
            category_rules_applied=matched_rules,
        )

    async def update_transaction_service(
        self, tenant_id: str, categorized_transactions: List[CategorizedTransaction]
    ):
        """Update Transaction Service with categories."""

        async with httpx.AsyncClient() as client:
            for tx in categorized_transactions:
                await client.patch(
                    f"http://localhost:8006/api/v1/transactions/{tx.id}",
                    json={
                        "category": tx.category.value,
                        "confidence": tx.confidence,
                        "categorized_at": tx.categorized_at.isoformat(),
                    },
                    headers={"X-Tenant-ID": tenant_id},
                )

    def get_stats(self, categorized: List[CategorizedTransaction]) -> Dict[str, int]:
        """Get statistics for categorized batch."""
        stats = {}
        for cat in categorized:
            cat_name = cat.category.value
            stats[cat_name] = stats.get(cat_name, 0) + 1
        return stats

    async def get_rules(self, tenant_id: str) -> List[Dict]:
        """Get rules for a tenant."""
        rules = (
            self.db.query(CategoryRule)
            .filter(CategoryRule.tenant_id == tenant_id)
            .all()
        )

        return [
            {
                "id": r.id,
                "name": r.name,
                "pattern": r.pattern,
                "category": r.category,
                "confidence": r.confidence,
                "priority": r.priority,
                "is_active": r.is_active,
            }
            for r in rules
        ]

    async def create_rule(self, tenant_id: str, rule: dict) -> Dict:
        """Create a custom rule for a tenant."""
        db_rule = CategoryRule(
            tenant_id=tenant_id,
            name=rule.get("name"),
            pattern=rule.get("pattern"),
            category=rule.get("category"),
            confidence=rule.get("confidence", 0.9),
            priority=rule.get("priority", 0),
            is_active=rule.get("is_active", True),
        )
        self.db.add(db_rule)
        self.db.commit()
        self.db.refresh(db_rule)

        return {
            "id": db_rule.id,
            "name": db_rule.name,
            "pattern": db_rule.pattern,
            "category": db_rule.category,
            "confidence": db_rule.confidence,
            "priority": db_rule.priority,
            "is_active": db_rule.is_active,
        }
