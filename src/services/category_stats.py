# transaction-categorizer/src/services/category_stats.py - NEW

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, func
from sqlalchemy.orm import Session
from src.core.database import CategorizedTransaction


class CategoryStatsService:
    """Service for category-level analytics"""

    def __init__(self, db: Session):
        self.db = db

    def get_stats(self, tenant_id: str, days: int = 30) -> Dict[str, Any]:
        """Get category statistics for a tenant"""

        cutoff = datetime.utcnow() - timedelta(days=days)

        # Get totals by category (expenses only)
        results = (
            self.db.query(
                CategorizedTransaction.category,
                func.sum(CategorizedTransaction.amount).label("total"),
                func.count(CategorizedTransaction.id).label("count"),
            )
            .filter(
                and_(
                    CategorizedTransaction.tenant_id == tenant_id,
                    CategorizedTransaction.transaction_date >= cutoff,
                    CategorizedTransaction.transaction_type == "expense",
                    CategorizedTransaction.amount > 0,
                )
            )
            .group_by(CategorizedTransaction.category)
            .all()
        )

        total_spent = sum(r.total for r in results) if results else 0

        categories = []
        for r in results:
            categories.append(
                {
                    "category": r.category,
                    "total": float(r.total) if r.total else 0,
                    "count": r.count,
                    "percentage": round(
                        (r.total / total_spent * 100) if total_spent > 0 else 0, 1
                    ),
                }
            )

        # Sort by total descending
        categories.sort(key=lambda x: x["total"], reverse=True)

        return {
            "categories": categories,
            "total_spent": float(total_spent),
            "period_days": days,
            "period_start": cutoff.isoformat(),
            "period_end": datetime.utcnow().isoformat(),
            "category_count": len(categories),
        }

    def get_trends(
        self, tenant_id: str, category: Optional[str] = None, weeks: int = 12
    ) -> List[Dict]:
        """Get category trends over time (weekly)"""

        cutoff = datetime.utcnow() - timedelta(weeks=weeks)

        # Build query
        query = self.db.query(
            func.date_trunc("week", CategorizedTransaction.transaction_date).label(
                "week"
            ),
            func.sum(CategorizedTransaction.amount).label("total"),
            func.count(CategorizedTransaction.id).label("count"),
        ).filter(
            and_(
                CategorizedTransaction.tenant_id == tenant_id,
                CategorizedTransaction.transaction_date >= cutoff,
                CategorizedTransaction.transaction_type == "expense",
                CategorizedTransaction.amount > 0,
            )
        )

        if category:
            query = query.filter(CategorizedTransaction.category == category)

        results = query.group_by("week").order_by("week").all()

        # Fill in missing weeks with zeros
        trends = []
        current = cutoff
        result_dict = {
            r.week.isoformat(): {"total": r.total, "count": r.count} for r in results
        }

        for i in range(weeks):
            week_start = cutoff + timedelta(weeks=i)
            week_key = week_start.isoformat()

            trends.append(
                {
                    "week": week_key,
                    "total": float(result_dict.get(week_key, {}).get("total", 0)),
                    "count": result_dict.get(week_key, {}).get("count", 0),
                }
            )

        return trends

    def get_top_categories(self, tenant_id: str, limit: int = 5) -> List[Dict]:
        """Get top spending categories"""
        stats = self.get_stats(tenant_id, days=30)
        return stats["categories"][:limit]

    def get_category_breakdown(
        self, tenant_id: str, categories: List[str] = None
    ) -> Dict:
        """Get detailed breakdown for specific categories"""

        query = self.db.query(
            CategorizedTransaction.category,
            func.sum(CategorizedTransaction.amount).label("total"),
            func.count(CategorizedTransaction.id).label("count"),
            func.avg(CategorizedTransaction.amount).label("average"),
        ).filter(
            and_(
                CategorizedTransaction.tenant_id == tenant_id,
                CategorizedTransaction.transaction_type == "expense",
                CategorizedTransaction.amount > 0,
            )
        )

        if categories:
            query = query.filter(CategorizedTransaction.category.in_(categories))

        results = query.group_by(CategorizedTransaction.category).all()

        return {
            category: {
                "total": float(r.total) if r.total else 0,
                "count": r.count,
                "average": float(r.average) if r.average else 0,
            }
            for r in results
        }
