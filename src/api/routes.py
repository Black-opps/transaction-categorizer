# transaction-categorizer/src/api/routes.py - COMPLETE VERSION

"""
API routes for transaction categorization service.
"""

from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from src.core.database import get_db
from src.models.transaction import (
    CategorizationRequest,
    CategorizationResponse,
    CategorizationRule,
    Category,
)
from src.services.categorizer import CategorizerService
from src.services.category_stats import CategoryStatsService
from src.services.confidence import ConfidenceScorer
from src.services.merchant_classifier import MerchantClassifier

router = APIRouter(prefix="/api/v1/categorizer", tags=["categorization"])


# ============================================================
# MAIN CATEGORIZATION ENDPOINTS
# ============================================================


@router.post("/categorize", response_model=CategorizationResponse)
async def categorize_transactions(
    request: CategorizationRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Categorize a batch of transactions.
    Called by Transaction Service after ingestion.

    Args:
        request: Batch of transactions to categorize
        background_tasks: FastAPI background tasks
        db: Database session

    Returns:
        CategorizationResponse with categorized transactions and stats
    """
    service = CategorizerService(db)

    # Categorize
    categorized = await service.categorize_batch(
        tenant_id=request.tenant_id, transactions=request.transactions
    )

    # Update Transaction Service in background
    background_tasks.add_task(
        service.update_transaction_service,
        tenant_id=request.tenant_id,
        categorized_transactions=categorized,
    )

    return CategorizationResponse(
        categorized_transactions=categorized,
        stats=service.get_stats(categorized),
        processing_time_ms=service.last_processing_time_ms,
    )


@router.post("/categorize/single")
async def categorize_single_transaction(
    transaction: dict,
    tenant_id: str,
    db: Session = Depends(get_db),
):
    """
    Categorize a single transaction.
    Useful for testing or real-time categorization.
    """
    service = CategorizerService(db)

    # Convert to Transaction model
    from src.models.transaction import Transaction, TransactionType

    tx = Transaction(
        amount=transaction.get("amount", 0),
        description=transaction.get("description", ""),
        phone_number=transaction.get("phone_number"),
        transaction_date=datetime.fromisoformat(transaction.get("transaction_date")),
        transaction_type=TransactionType(
            transaction.get("transaction_type", "unknown")
        ),
        reference=transaction.get("reference"),
        merchant=transaction.get("merchant"),
    )

    categorized = await service.categorize_single(tenant_id, tx)

    return {
        "original": tx.dict(),
        "categorized": categorized.dict(),
        "category": categorized.category.value,
        "confidence": categorized.confidence,
        "confidence_level": categorized.confidence_level,
        "rules_applied": categorized.category_rules_applied,
    }


# ============================================================
# CATEGORY STATISTICS ENDPOINTS
# ============================================================


@router.get("/stats")
async def get_category_stats(
    tenant_id: str,
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    db: Session = Depends(get_db),
):
    """
    Get category statistics for a tenant.

    Args:
        tenant_id: Tenant identifier
        days: Number of days to analyze (default: 30)
        db: Database session

    Returns:
        Category statistics including totals, percentages, and breakdowns
    """
    service = CategoryStatsService(db)
    return service.get_stats(tenant_id, days)


@router.get("/stats/category/{category}")
async def get_category_detail(
    tenant_id: str,
    category: str,
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
):
    """
    Get detailed statistics for a specific category.

    Args:
        tenant_id: Tenant identifier
        category: Category name
        days: Number of days to analyze
        db: Database session
    """
    service = CategoryStatsService(db)
    stats = service.get_stats(tenant_id, days)

    # Find the specific category
    for cat in stats["categories"]:
        if cat["category"] == category:
            return cat

    return {
        "category": category,
        "total": 0,
        "count": 0,
        "percentage": 0,
        "message": "Category not found in this period",
    }


@router.get("/top")
async def get_top_categories(
    tenant_id: str,
    limit: int = Query(5, ge=1, le=20),
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
):
    """
    Get top spending categories.

    Args:
        tenant_id: Tenant identifier
        limit: Number of categories to return (default: 5)
        days: Number of days to analyze (default: 30)
        db: Database session
    """
    service = CategoryStatsService(db)
    stats = service.get_stats(tenant_id, days)
    return {
        "top_categories": stats["categories"][:limit],
        "total_spent": stats["total_spent"],
        "period_days": stats["period_days"],
    }


# ============================================================
# TREND ENDPOINTS
# ============================================================


@router.get("/trends")
async def get_category_trends(
    tenant_id: str,
    category: Optional[str] = None,
    weeks: int = Query(12, ge=4, le=52, description="Number of weeks to analyze"),
    db: Session = Depends(get_db),
):
    """
    Get category trends over time (weekly).

    Args:
        tenant_id: Tenant identifier
        category: Specific category to analyze (optional)
        weeks: Number of weeks to analyze (default: 12)
        db: Database session
    """
    service = CategoryStatsService(db)
    trends = service.get_trends(tenant_id, category, weeks)

    # Calculate summary statistics
    if trends:
        total = sum(t["total"] for t in trends)
        average = total / len(trends) if trends else 0
        max_value = max(t["total"] for t in trends) if trends else 0
        min_value = min(t["total"] for t in trends) if trends else 0
    else:
        total = average = max_value = min_value = 0

    return {
        "trends": trends,
        "summary": {
            "total": total,
            "average": average,
            "max": max_value,
            "min": min_value,
            "weeks": len(trends),
        },
        "category": category or "all",
    }


@router.get("/trends/monthly")
async def get_monthly_trends(
    tenant_id: str,
    category: Optional[str] = None,
    months: int = Query(6, ge=3, le=24, description="Number of months to analyze"),
    db: Session = Depends(get_db),
):
    """
    Get category trends over time (monthly).

    Args:
        tenant_id: Tenant identifier
        category: Specific category to analyze (optional)
        months: Number of months to analyze (default: 6)
        db: Database session
    """
    service = CategoryStatsService(db)
    return service.get_trends(tenant_id, category, months)


# ============================================================
# MERCHANT ENDPOINTS
# ============================================================


@router.post("/classify-merchant")
async def classify_merchant(
    merchant: str,
    db: Session = Depends(get_db),
):
    """
    Classify a merchant by name.

    Args:
        merchant: Merchant name to classify
        db: Database session

    Returns:
        Classification results including category and confidence
    """
    # First check merchant directory
    service = CategorizerService(db)
    merchant_info = service.classify_merchant(merchant)

    if merchant_info:
        return merchant_info

    # Fallback to rule-based classification
    category = MerchantClassifier.classify(merchant)
    normalized = MerchantClassifier.get_normalized_name(merchant)

    return {
        "merchant": merchant,
        "normalized": normalized,
        "category": category.value if category else "Unknown",
        "category_label": category.value if category else "Unknown",
        "confidence": 0.7 if category else 0.0,
        "source": "rule_engine",
    }


@router.get("/merchants")
async def get_merchants(
    tenant_id: str,
    category: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """
    Get merchants for a tenant, optionally filtered by category or search term.

    Args:
        tenant_id: Tenant identifier
        category: Filter by category
        search: Search term for merchant name
        limit: Maximum number of merchants to return
        db: Database session
    """
    service = CategorizerService(db)
    return service.get_merchants(tenant_id, category, search, limit)


@router.post("/merchants/normalize")
async def normalize_merchant(
    merchant: str,
):
    """
    Normalize a merchant name.

    Args:
        merchant: Merchant name to normalize

    Returns:
        Normalized merchant name
    """
    normalized = MerchantClassifier.get_normalized_name(merchant)

    return {
        "original": merchant,
        "normalized": normalized,
    }


# ============================================================
# RULES MANAGEMENT ENDPOINTS
# ============================================================


@router.get("/rules")
async def get_rules(
    tenant_id: Optional[str] = None,
    active_only: bool = Query(True, description="Only return active rules"),
    db: Session = Depends(get_db),
):
    """
    Get categorization rules.

    Args:
        tenant_id: Tenant identifier (optional)
        active_only: Only return active rules
        db: Database session

    Returns:
        List of categorization rules
    """
    service = CategorizerService(db)
    return await service.get_rules(tenant_id, active_only)


@router.post("/rules")
async def create_rule(
    rule: CategorizationRule,
    tenant_id: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """
    Create a custom categorization rule for a tenant.

    Args:
        rule: Rule configuration
        tenant_id: Tenant identifier (optional, null = global rule)
        db: Database session
    """
    service = CategorizerService(db)
    return await service.create_rule(tenant_id, rule.dict())


@router.put("/rules/{rule_id}")
async def update_rule(
    rule_id: int,
    rule: CategorizationRule,
    db: Session = Depends(get_db),
):
    """
    Update an existing categorization rule.

    Args:
        rule_id: Rule identifier
        rule: Updated rule configuration
        db: Database session
    """
    service = CategorizerService(db)
    return await service.update_rule(rule_id, rule.dict())


@router.delete("/rules/{rule_id}")
async def delete_rule(
    rule_id: int,
    db: Session = Depends(get_db),
):
    """
    Delete a categorization rule.

    Args:
        rule_id: Rule identifier
        db: Database session
    """
    service = CategorizerService(db)
    return await service.delete_rule(rule_id)


@router.patch("/rules/{rule_id}/toggle")
async def toggle_rule(
    rule_id: int,
    active: bool = Query(..., description="Active status"),
    db: Session = Depends(get_db),
):
    """
    Toggle a rule's active status.

    Args:
        rule_id: Rule identifier
        active: New active status
        db: Database session
    """
    service = CategorizerService(db)
    return await service.toggle_rule(rule_id, active)


# ============================================================
# CONFIDENCE ENDPOINTS
# ============================================================


@router.post("/confidence/calculate")
async def calculate_confidence(
    category: str,
    description: str,
    matched_rules: List[str] = [],
    amount: float = 0,
    merchant: Optional[str] = None,
):
    """
    Calculate confidence score for a categorization.

    Args:
        category: Category name
        description: Transaction description
        matched_rules: List of matched rules
        amount: Transaction amount
        merchant: Merchant name

    Returns:
        Confidence score and level
    """
    from src.models.transaction import Category as CategoryEnum

    # Convert category string to enum
    category_enum = CategoryEnum.OTHER
    for c in CategoryEnum:
        if c.value == category:
            category_enum = c
            break

    confidence = ConfidenceScorer.calculate(
        category=category_enum,
        matched_rules=matched_rules,
        description=description,
        amount=amount,
        merchant=merchant,
    )

    return {
        "confidence": confidence,
        "confidence_level": ConfidenceScorer.get_confidence_level(confidence),
        "category": category,
        "description": description[:100],
    }


# ============================================================
# BATCH OPERATIONS ENDPOINTS
# ============================================================


@router.post("/batch/reprocess")
async def reprocess_transactions(
    tenant_id: str,
    start_date: str,
    end_date: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Reprocess transactions in a date range with updated rules.

    Args:
        tenant_id: Tenant identifier
        start_date: Start date (ISO format)
        end_date: End date (ISO format)
        background_tasks: FastAPI background tasks
        db: Database session
    """
    start = datetime.fromisoformat(start_date)
    end = datetime.fromisoformat(end_date)

    service = CategorizerService(db)

    # Get transactions in date range
    transactions = service.get_transactions_by_date(tenant_id, start, end)

    if not transactions:
        return {
            "status": "completed",
            "processed": 0,
            "message": "No transactions found in date range",
        }

    # Reprocess in background
    background_tasks.add_task(
        service.reprocess_batch,
        tenant_id=tenant_id,
        transactions=transactions,
    )

    return {
        "status": "accepted",
        "processed": len(transactions),
        "message": f"Reprocessing {len(transactions)} transactions in background",
    }


# ============================================================
# HEALTH AND STATUS ENDPOINTS
# ============================================================


@router.get("/health")
async def health_check(
    db: Session = Depends(get_db),
):
    """
    Health check endpoint.

    Args:
        db: Database session

    Returns:
        Service health status
    """
    try:
        # Check database connection
        db.execute("SELECT 1")
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    return {
        "status": "healthy",
        "service": "transaction-categorizer",
        "database": db_status,
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/stats/rules")
async def get_rule_stats(
    db: Session = Depends(get_db),
):
    """
    Get statistics about categorization rules.

    Args:
        db: Database session

    Returns:
        Rule statistics
    """
    service = CategorizerService(db)
    return service.get_rule_stats()


@router.get("/stats/coverage")
async def get_categorization_coverage(
    tenant_id: str,
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
):
    """
    Get categorization coverage statistics.

    Args:
        tenant_id: Tenant identifier
        days: Number of days to analyze
        db: Database session

    Returns:
        Coverage statistics including categorized vs uncategorized
    """
    service = CategoryStatsService(db)
    stats = service.get_stats(tenant_id, days)

    # Calculate coverage
    total = stats["total_spent"]
    categorized = sum(
        c["total"] for c in stats["categories"] if c["category"] != "Other"
    )

    return {
        "total_transactions": sum(c["count"] for c in stats["categories"]),
        "total_amount": total,
        "categorized_amount": categorized,
        "uncategorized_amount": total - categorized,
        "coverage_percentage": round(
            (categorized / total * 100) if total > 0 else 0, 1
        ),
        "category_count": stats["category_count"],
        "period_days": stats["period_days"],
    }
