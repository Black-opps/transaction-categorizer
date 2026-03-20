"""
FastAPI routes for transaction categorization.
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List
from uuid import UUID

from ..models.transaction import (
    CategorizationRequest,
    CategorizationResponse,
    CategorizedTransaction,
    Transaction,
    CategorizationRule
)
from ..services.categorizer import TransactionCategorizer

router = APIRouter(prefix="/api/v1/categorize", tags=["Transaction Categorization"])


@router.post("/", response_model=CategorizationResponse)
async def categorize_transactions(
    request: CategorizationRequest,
    background_tasks: BackgroundTasks
):
    """
    Categorize a batch of transactions for a single tenant.
    
    Tenant ID is provided once at the top level.
    """
    categorizer = TransactionCategorizer()

    try:
        result = await categorizer.categorize_batch(
            transactions=request.transactions,
            tenant_id=request.tenant_id
        )
        # Optional: background task for logging or analytics
        # background_tasks.add_task(log_batch_result, result)
        return result
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=f"Invalid input: {str(ve)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Categorization failed: {str(e)}")


@router.post("/single", response_model=CategorizedTransaction)
async def categorize_single(
    transaction: Transaction,
    tenant_id: UUID  # Query or header in real usage; for simplicity added as param
):
    """
    Categorize a single transaction.
    Tenant ID can be passed as query param or header in production.
    """
    categorizer = TransactionCategorizer()

    try:
        categorized = await categorizer.categorize_single_transaction(
            transaction=transaction,
            tenant_id=tenant_id
        )
        return categorized
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=f"Invalid transaction: {str(ve)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Categorization failed: {str(e)}")


@router.get("/rules")
async def list_rules():
    """List all active categorization rules."""
    categorizer = TransactionCategorizer()
    rules = await categorizer.get_rules()
    return {"count": len(rules), "rules": rules}


@router.post("/rules")
async def add_rule(rule: CategorizationRule):
    """Add or update a categorization rule."""
    categorizer = TransactionCategorizer()
    added = await categorizer.add_rule(rule)
    return {"message": "Rule added/updated", "rule": added}


@router.delete("/rules/{rule_id}")
async def remove_rule(rule_id: UUID):
    """Remove a categorization rule by ID."""
    categorizer = TransactionCategorizer()
    await categorizer.remove_rule(rule_id)
    return {"message": "Rule removed"}


@router.get("/stats")
async def get_stats():
    """Get categorization statistics and rule overview."""
    categorizer = TransactionCategorizer()
    return await categorizer.get_stats()