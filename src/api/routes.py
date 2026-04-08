"""
API routes for transaction categorizer.
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
from uuid import UUID

from ..services.categorizer import TransactionCategorizer
from ..services.rules import DEFAULT_RULES

router = APIRouter(prefix="/api/v1/categorize", tags=["Transaction Categorization"])


# Request Models
class Transaction(BaseModel):
    id: Optional[str] = None
    tenant_id: str
    amount: float
    description: str
    transaction_type: str = "expense"
    transaction_date: str
    phone_number: Optional[str] = None
    reference: Optional[str] = None


class CategorizeRequest(BaseModel):
    transactions: List[Transaction]


# Response Models
class CategorizedTransaction(BaseModel):
    id: str
    tenant_id: str
    original_description: str
    amount: float
    transaction_type: str
    transaction_date: str
    category: str
    confidence: float
    rules_applied: List[str]
    processed_at: str


class CategorizeResponse(BaseModel):
    categorized_transactions: List[CategorizedTransaction]
    stats: dict
    processing_time_ms: float


@router.post("/", response_model=CategorizeResponse)
async def categorize_transactions(request: CategorizeRequest):
    """
    Categorize a batch of transactions.
    """
    import time

    start_time = time.time()

    categorizer = TransactionCategorizer()

    transactions = [tx.dict() for tx in request.transactions]

    results = categorizer.categorize_batch(transactions)

    stats = {}

    for result in results:
        category = result.get("category", "Other")
        stats[category] = stats.get(category, 0) + 1

    processing_time = (time.time() - start_time) * 1000

    return CategorizeResponse(
        categorized_transactions=results,
        stats=stats,
        processing_time_ms=round(processing_time, 2),
    )


@router.post("/single", response_model=CategorizedTransaction)
async def categorize_single(transaction: Transaction):
    """
    Categorize a single transaction.
    """
    categorizer = TransactionCategorizer()

    try:
        result = categorizer.categorize_transaction(transaction.dict())
        return result

    except Exception as e:
        print("Categorization error:", str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rules")
async def list_rules():
    """
    List all active categorization rules.
    """
    rules = [
        {
            "name": r.name,
            "pattern": r.pattern,
            "category": r.category,
            "confidence": r.confidence,
            "priority": r.priority,
        }
        for r in DEFAULT_RULES
    ]

    return {"rules": rules, "count": len(rules)}


@router.get("/stats")
async def get_stats(tenant_id: Optional[str] = None):
    """
    Get categorization statistics.
    """
    categorizer = TransactionCategorizer()

    return categorizer.get_stats(tenant_id)


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "transaction-categorizer",
        "version": "1.0.0",
    }


@router.get("/ping")
async def ping():
    """Simple ping endpoint."""
    return {"status": "ok", "message": "Service is running"}


@router.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "Transaction Categorizer Service",
        "version": "1.0.0",
        "description": "ML-powered transaction categorization",
        "categories": [
            "Revenue",
            "Inventory",
            "Rent",
            "Salaries",
            "Transport",
            "Utilities",
            "Other",
        ],
    }