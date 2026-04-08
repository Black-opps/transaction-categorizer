"""
Transaction categorization service.
"""
import logging
from typing import List, Dict, Any
from datetime import datetime
from uuid import uuid4

from .rules import get_default_engine, Category
from ..core.database import SessionLocal, CategorizedTransaction

logger = logging.getLogger(__name__)


class TransactionCategorizer:
    """Main transaction categorization service."""
    
    def __init__(self, rule_engine=None):
        self.rule_engine = rule_engine or get_default_engine()
        self.db = SessionLocal()
    
    def __del__(self):
        if hasattr(self, 'db') and self.db:
            self.db.close()
    
    def categorize_transaction(self, transaction: Dict[str, Any]) -> Dict[str, Any]:
        """
        Categorize a single transaction.
        """

        description = transaction.get("description", "")
        amount = float(transaction.get("amount", 0))
        transaction_type = transaction.get("transaction_type", "expense")
        tenant_id = transaction.get("tenant_id", "unknown")

        # Categorize using rules engine
        category, confidence, matched_rules = self.rule_engine.categorize(description)

        if transaction_type == "income" and category == Category.OTHER.value:
            category = Category.REVENUE.value
            confidence = 0.7

        # Parse transaction date safely
        tx_date = transaction.get("transaction_date")

        try:
            parsed_date = datetime.fromisoformat(tx_date.replace("Z", "+00:00"))
        except Exception:
            parsed_date = datetime.utcnow()

        # Generate ID if missing
        tx_id = transaction.get("id") or str(uuid4())

        categorized = {
            "id": tx_id,
            "tenant_id": tenant_id,
            "original_description": description,
            "amount": amount,
            "transaction_type": transaction_type,
            "transaction_date": parsed_date.isoformat(),
            "category": category,
            "confidence": confidence,
            "rules_applied": matched_rules,
            "processed_at": datetime.utcnow().isoformat(),
        }

        # Save to DB safely
        try:
            db_record = CategorizedTransaction(
                id=tx_id,
                tenant_id=tenant_id,
                original_description=description,
                amount=amount,
                transaction_type=transaction_type,
                transaction_date=parsed_date,
                category=category,
                confidence=confidence,
                rules_applied=",".join(matched_rules),  # store as string
                phone_number=transaction.get("phone_number"),
                reference=transaction.get("reference"),
                processed_at=datetime.utcnow(),
            )

            self.db.add(db_record)
            self.db.commit()

        except Exception as e:
            logger.error(f"DB insert failed: {e}")
            self.db.rollback()

        logger.info(f"Categorized: {description[:50]} -> {category}")

        return categorized
    
    def categorize_batch(self, transactions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Categorize a batch of transactions."""
        results = []
        for tx in transactions:
            try:
                result = self.categorize_transaction(tx)
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to categorize: {e}")
                results.append({
                    **tx,
                    "category": "Error",
                    "confidence": 0,
                    "error": str(e)
                })
        return results
    
    def get_stats(self, tenant_id: str = None) -> Dict[str, Any]:
        """Get categorization statistics."""
        query = self.db.query(CategorizedTransaction)
        if tenant_id:
            query = query.filter(CategorizedTransaction.tenant_id == tenant_id)
        
        total = query.count()
        
        from sqlalchemy import func
        category_breakdown = {}
        results = query.with_entities(
            CategorizedTransaction.category, 
            func.count(CategorizedTransaction.id)
        ).group_by(CategorizedTransaction.category).all()
        
        for category, count in results:
            category_breakdown[category] = count
        
        return {
            "total_transactions": total,
            "category_breakdown": category_breakdown,
            "unique_tenants": self.db.query(CategorizedTransaction.tenant_id).distinct().count()
        }