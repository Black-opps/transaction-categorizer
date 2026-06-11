# src/api/routes.py
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session
from src.core.database import get_db
from src.models.transaction import CategorizationRequest, CategorizationResponse
from src.services.categorizer import CategorizerService

router = APIRouter(prefix="/api/v1/categorizer", tags=["categorization"])


@router.post("/categorize", response_model=CategorizationResponse)
async def categorize_transactions(
    request: CategorizationRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Categorize a batch of transactions.
    Called by Transaction Service after ingestion.
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


@router.get("/rules")
async def get_rules(tenant_id: str, db: Session = Depends(get_db)):
    """Get categorization rules for a tenant."""
    service = CategorizerService(db)
    return await service.get_rules(tenant_id)


@router.post("/rules")
async def create_rule(
    rule: CategorizationRule, tenant_id: str, db: Session = Depends(get_db)
):
    """Create a custom categorization rule for a tenant."""
    service = CategorizerService(db)
    return await service.create_rule(tenant_id, rule)
