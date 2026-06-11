# src/main.py
"""
Transaction Categorizer Service - MVP Hardened with M-PESA Patterns
Direct HTTP API - No RabbitMQ needed for MVP
"""

import logging
import re
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import Column, DateTime, Float, Index, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker

from .core.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Database setup
DATABASE_URL = "postgresql://postgres:password@localhost:5432/parser_db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ==================== MODELS ====================


class CategorizedTransactionDB(Base):
    __tablename__ = "categorized_transactions"
    __table_args__ = {"extend_existing": True}  # This fixes the error

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String(36), nullable=False)
    original_description = Column(String(500), nullable=False)
    amount = Column(Float, nullable=False)
    transaction_type = Column(String(20), nullable=False)
    transaction_date = Column(DateTime, nullable=False)
    category = Column(String(50), nullable=False, default="Other")
    subcategory = Column(String(50), default="Other")
    confidence = Column(Float, default=0.0)
    rules_applied = Column(String(500))
    phone_number = Column(String(20))
    reference = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_categorized_tenant_date", "tenant_id", "transaction_date"),
        Index("ix_categorized_tenant_category", "tenant_id", "category"),
        {"extend_existing": True},
    )


# Create tables (if not exist)
Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Create FastAPI app
app = FastAPI(
    title="Transaction Categorizer Service",
    description="Categorizes M-PESA transactions for financial intelligence",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== M-PESA SPECIFIC CATEGORY RULES ====================

MPESA_MERCHANT_PATTERNS = {
    "KPLC": {"category": "Utilities", "subcategory": "Electricity", "confidence": 0.95},
    "KPLC PREPAID": {
        "category": "Utilities",
        "subcategory": "Electricity",
        "confidence": 0.95,
    },
    "National Oil": {
        "category": "Transport",
        "subcategory": "Fuel",
        "confidence": 0.95,
    },
    "TotalEnergies": {
        "category": "Transport",
        "subcategory": "Fuel",
        "confidence": 0.95,
    },
    "Shell": {"category": "Transport", "subcategory": "Fuel", "confidence": 0.95},
    "Naivas": {"category": "Shopping", "subcategory": "Groceries", "confidence": 0.95},
    "Quick Mart": {
        "category": "Shopping",
        "subcategory": "Groceries",
        "confidence": 0.95,
    },
    "Java House": {"category": "Food", "subcategory": "Restaurant", "confidence": 0.95},
    "KFC": {"category": "Food", "subcategory": "Restaurant", "confidence": 0.95},
    "Airtime Purchase": {
        "category": "Mobile",
        "subcategory": "Airtime",
        "confidence": 0.95,
    },
    "Fuliza": {"category": "Financial", "subcategory": "Loan", "confidence": 0.95},
    "OD Loan Repayment": {
        "category": "Financial",
        "subcategory": "Loan Repayment",
        "confidence": 0.95,
    },
    "Pay Merchant Charge": {
        "category": "Fees",
        "subcategory": "Transaction Fee",
        "confidence": 0.95,
    },
    "Business Payment from": {
        "category": "Income",
        "subcategory": "Business Income",
        "confidence": 0.9,
    },
    "Funds received from": {
        "category": "Income",
        "subcategory": "Received",
        "confidence": 0.85,
    },
    "Customer Transfer to": {
        "category": "Transfer",
        "subcategory": "Send Money",
        "confidence": 0.9,
    },
}

TYPE_CATEGORY_MAP = {
    "sent": {"category": "Expense", "subcategory": "Other", "confidence": 0.6},
    "received": {"category": "Income", "subcategory": "Other", "confidence": 0.6},
    "send_money": {"category": "Transfer", "subcategory": "Sent", "confidence": 0.7},
    "receive_money": {
        "category": "Income",
        "subcategory": "Received",
        "confidence": 0.7,
    },
    "paybill": {"category": "Bills", "subcategory": "Payment", "confidence": 0.7},
    "merchant_payment": {
        "category": "Shopping",
        "subcategory": "Merchant",
        "confidence": 0.7,
    },
    "airtime": {"category": "Mobile", "subcategory": "Airtime", "confidence": 0.8},
    "withdrawal": {"category": "Cash", "subcategory": "Withdrawal", "confidence": 0.8},
    "fuliza": {"category": "Financial", "subcategory": "Loan", "confidence": 0.85},
}


def categorize_transaction(txn: Dict[str, Any]) -> Dict[str, Any]:
    """Categorize a single transaction using M-PESA specific patterns."""
    description = txn.get("description", txn.get("narration", ""))
    counterparty = txn.get("counterparty", "")
    transaction_type = txn.get("transaction_type", "").lower()
    amount = float(txn.get("amount", 0))

    search_text = f"{description} {counterparty}".lower()

    for merchant, rule in MPESA_MERCHANT_PATTERNS.items():
        if merchant.lower() in search_text:
            txn["category"] = rule["category"]
            txn["subcategory"] = rule["subcategory"]
            txn["confidence"] = rule["confidence"]
            txn["matched_rule"] = merchant
            txn["original_description"] = description
            return txn

    if transaction_type in TYPE_CATEGORY_MAP:
        rule = TYPE_CATEGORY_MAP[transaction_type]
        txn["category"] = rule["category"]
        txn["subcategory"] = rule["subcategory"]
        txn["confidence"] = rule["confidence"]
    else:
        if amount < 0:
            txn["category"] = "Expense"
            txn["subcategory"] = "Other"
        else:
            txn["category"] = "Income"
            txn["subcategory"] = "Other"
        txn["confidence"] = 0.5

    txn["original_description"] = description
    return txn


def get_category_stats(transactions: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate category statistics from a list of transactions."""
    stats = {
        "total_by_category": {},
        "expense_by_category": {},
        "income_by_category": {},
        "total_expenses": 0,
        "total_income": 0,
        "net_cashflow": 0,
    }

    for txn in transactions:
        category = txn.get("category", "Uncategorized")
        subcategory = txn.get("subcategory", "Other")
        amount = float(txn.get("amount", 0))
        txn_type = txn.get("transaction_type", "").lower()

        full_category = f"{category}/{subcategory}"
        stats["total_by_category"][full_category] = (
            stats["total_by_category"].get(full_category, 0) + amount
        )

        if txn_type in [
            "sent",
            "send_money",
            "paybill",
            "merchant_payment",
            "withdrawal",
        ]:
            stats["expense_by_category"][full_category] = (
                stats["expense_by_category"].get(full_category, 0) + amount
            )
            stats["total_expenses"] += amount
        else:
            stats["income_by_category"][full_category] = (
                stats["income_by_category"].get(full_category, 0) + amount
            )
            stats["total_income"] += amount

    stats["net_cashflow"] = stats["total_income"] - stats["total_expenses"]
    return stats


# ==================== API ENDPOINTS ====================


@app.on_event("startup")
async def startup_event():
    logger.info("Starting Transaction Categorizer Service (MVP Hardened)...")
    logger.info(f"✅ M-PESA specific patterns loaded: {len(MPESA_MERCHANT_PATTERNS)}")
    logger.info("✅ Database initialized")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down Transaction Categorizer Service...")


@app.get("/")
async def root():
    return {
        "service": "Transaction Categorizer",
        "version": "1.0.0",
        "status": "running",
        "mpesa_patterns_loaded": len(MPESA_MERCHANT_PATTERNS),
    }


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "transaction-categorizer",
        "version": "1.0.0",
    }


@app.get("/api/v1/categorizer/categories")
async def get_categories():
    return {
        "merchant_patterns": MPESA_MERCHANT_PATTERNS,
        "type_mapping": TYPE_CATEGORY_MAP,
        "categories": list(
            set([v["category"] for v in MPESA_MERCHANT_PATTERNS.values()])
        ),
    }


@app.post("/api/v1/categorizer/test")
async def test_categorization(transaction: Dict[str, Any]):
    result = categorize_transaction(transaction.copy())
    return {
        "original": transaction,
        "categorized": result,
        "confidence": result.get("confidence", 0),
    }


@app.post("/api/v1/categorizer/batch")
async def batch_categorize(request: Request, db: Session = Depends(get_db)):
    """Categorize a batch of transactions and store in database"""
    data = await request.json()
    tenant_id = request.headers.get("X-Tenant-ID", "default")
    transactions = data.get("transactions", [])
    store_results = data.get("store_results", True)

    logger.info(
        f"Batch categorizing {len(transactions)} transactions for tenant {tenant_id}"
    )

    categorized = []
    for txn in transactions:
        categorized_txn = categorize_transaction(txn.copy())
        categorized.append(categorized_txn)

        if store_results:
            try:
                db_txn = CategorizedTransactionDB(
                    id=str(uuid.uuid4()),
                    tenant_id=tenant_id,
                    original_description=categorized_txn.get(
                        "original_description", categorized_txn.get("description", "")
                    ),
                    amount=categorized_txn.get("amount", 0),
                    transaction_type=categorized_txn.get("transaction_type", "unknown"),
                    transaction_date=datetime.fromisoformat(
                        categorized_txn.get(
                            "transaction_date", datetime.now().isoformat()
                        )
                    ),
                    category=categorized_txn.get("category", "Other"),
                    subcategory=categorized_txn.get("subcategory", "Other"),
                    confidence=categorized_txn.get("confidence", 0.0),
                    rules_applied=categorized_txn.get("matched_rule", "unknown"),
                    phone_number=categorized_txn.get("phone_number", ""),
                    reference=categorized_txn.get("reference", ""),
                )
                db.add(db_txn)
            except Exception as e:
                logger.error(f"Failed to store transaction: {e}")

    if store_results:
        db.commit()
        logger.info(f"Stored {len(categorized)} categorized transactions")

    stats = get_category_stats(categorized)

    return {
        "categorized_transactions": categorized,
        "stats": stats,
        "count": len(categorized),
        "tenant_id": tenant_id,
    }


@app.get("/api/v1/categorizer/stats/{tenant_id}")
async def get_tenant_stats(
    tenant_id: str,
    db: Session = Depends(get_db),
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
):
    """Get category statistics for a tenant from stored transactions"""
    try:
        query = db.query(CategorizedTransactionDB).filter(
            CategorizedTransactionDB.tenant_id == tenant_id
        )

        if start_date:
            query = query.filter(
                CategorizedTransactionDB.transaction_date
                >= datetime.fromisoformat(start_date)
            )
        if end_date:
            query = query.filter(
                CategorizedTransactionDB.transaction_date
                <= datetime.fromisoformat(end_date)
            )

        transactions = query.all()

        stats = {
            "total_income": 0.0,
            "total_expenses": 0.0,
            "by_category": {},
            "by_subcategory": {},
            "transaction_count": len(transactions),
            "net_cashflow": 0.0,
        }

        for txn in transactions:
            amount = float(txn.amount)
            if txn.transaction_type in [
                "sent",
                "send_money",
                "paybill",
                "merchant_payment",
                "withdrawal",
            ]:
                stats["total_expenses"] += amount
            else:
                stats["total_income"] += amount

            stats["by_category"][txn.category] = (
                stats["by_category"].get(txn.category, 0.0) + amount
            )

            subcat_key = f"{txn.category}/{txn.subcategory}"
            stats["by_subcategory"][subcat_key] = (
                stats["by_subcategory"].get(subcat_key, 0.0) + amount
            )

        stats["net_cashflow"] = stats["total_income"] - stats["total_expenses"]

        return stats

    except Exception as e:
        logger.error(f"Stats error: {e}")
        return {
            "total_income": 0.0,
            "total_expenses": 0.0,
            "by_category": {},
            "by_subcategory": {},
            "transaction_count": 0,
            "net_cashflow": 0.0,
            "error": str(e),
        }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("src.main:app", host="0.0.0.0", port=8009, reload=True)
