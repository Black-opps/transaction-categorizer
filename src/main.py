# transaction-categorizer/src/main.py - COMPLETE FIXED VERSION

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

# ============================================================
# ✅ FIXED: Use settings.DATABASE_URL instead of hardcoded
# ============================================================
DATABASE_URL = settings.DATABASE_URL
logger.info(f"🔧 Connecting to database: {DATABASE_URL}")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ==================== MODELS ====================


class CategorizedTransactionDB(Base):
    __tablename__ = "categorized_transactions"
    __table_args__ = {"extend_existing": True}

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String(36), nullable=False)
    original_description = Column(String(500), nullable=False)
    amount = Column(Float, nullable=False)
    transaction_type = Column(
        String(100), nullable=False
    )  # ✅ Increased to 100 characters
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


# ============================================================
# ✅ COMPLETE M-PESA TRANSACTION TYPE CATEGORY MAPPING
# ============================================================

MPESA_TRANSACTION_TYPE_MAP = {
    # ✅ INCOME TYPES
    "RECEIVED": {"category": "Income", "subcategory": "Received", "confidence": 0.95},
    "RECEIVED MONEY": {
        "category": "Income",
        "subcategory": "Received",
        "confidence": 0.95,
    },
    "RECEIVE_MONEY": {
        "category": "Income",
        "subcategory": "Received",
        "confidence": 0.95,
    },
    "AGENT DEPOSIT": {
        "category": "Income",
        "subcategory": "Cash Deposit",
        "confidence": 0.95,
    },
    "BUSINESS PAYMENT": {
        "category": "Income",
        "subcategory": "Business",
        "confidence": 0.9,
    },
    "BUSINESS PAYMENT FROM": {
        "category": "Income",
        "subcategory": "Business",
        "confidence": 0.9,
    },
    "BANK TRANSFER": {
        "category": "Income",
        "subcategory": "Bank Transfer",
        "confidence": 0.9,
    },
    "TRANSFER FROM BANK": {
        "category": "Income",
        "subcategory": "Bank Transfer",
        "confidence": 0.9,
    },
    "PROMOTION": {"category": "Income", "subcategory": "Promotion", "confidence": 0.85},
    "PROMOTION PAYMENT": {
        "category": "Income",
        "subcategory": "Promotion",
        "confidence": 0.85,
    },
    "FUNDS RECEIVED FROM": {
        "category": "Income",
        "subcategory": "Received",
        "confidence": 0.85,
    },
    # ✅ OUTGOING TYPES
    "SENT": {"category": "Expense", "subcategory": "Other", "confidence": 0.8},
    "SEND MONEY": {"category": "Transfer", "subcategory": "Sent", "confidence": 0.95},
    "SEND_MONEY": {"category": "Transfer", "subcategory": "Sent", "confidence": 0.95},
    "CUSTOMER TRANSFER TO": {
        "category": "Transfer",
        "subcategory": "Sent",
        "confidence": 0.9,
    },
    # ✅ BILLS & PAYMENTS
    "LIPA NA M-PESA (PAYBILL)": {
        "category": "Bills",
        "subcategory": "Paybill",
        "confidence": 0.95,
    },
    "PAYBILL": {"category": "Bills", "subcategory": "Paybill", "confidence": 0.95},
    "PAY BILL": {"category": "Bills", "subcategory": "Paybill", "confidence": 0.9},
    # ✅ SHOPPING / BUY GOODS
    "LIPA NA M-PESA (BUY GOODS)": {
        "category": "Shopping",
        "subcategory": "Merchant",
        "confidence": 0.95,
    },
    "BUY GOODS": {
        "category": "Shopping",
        "subcategory": "Merchant",
        "confidence": 0.95,
    },
    "MERCHANT PAYMENT": {
        "category": "Shopping",
        "subcategory": "Merchant",
        "confidence": 0.9,
    },
    "MERCHANT PAYMENT TO": {
        "category": "Shopping",
        "subcategory": "Merchant",
        "confidence": 0.9,
    },
    # ✅ CASH WITHDRAWAL
    "AGENT WITHDRAWAL": {
        "category": "Cash",
        "subcategory": "Withdrawal",
        "confidence": 0.95,
    },
    "WITHDRAWAL": {"category": "Cash", "subcategory": "Withdrawal", "confidence": 0.9},
    # ✅ MOBILE / AIRTIME
    "AIRTIME": {"category": "Mobile", "subcategory": "Airtime", "confidence": 0.95},
    "AIRTIME PURCHASE": {
        "category": "Mobile",
        "subcategory": "Airtime",
        "confidence": 0.95,
    },
    # ✅ FINANCIAL / LOAN
    "FULIZA": {"category": "Financial", "subcategory": "Loan", "confidence": 0.95},
    "FULIZA_REVERSAL": {
        "category": "Financial",
        "subcategory": "Loan Reversal",
        "confidence": 0.9,
    },
    "OD LOAN REPAYMENT": {
        "category": "Financial",
        "subcategory": "Loan Repayment",
        "confidence": 0.9,
    },
    # ✅ FEES
    "CHARGES": {
        "category": "Fees",
        "subcategory": "Transaction Fee",
        "confidence": 0.95,
    },
    "PAY MERCHANT CHARGE": {
        "category": "Fees",
        "subcategory": "Transaction Fee",
        "confidence": 0.95,
    },
    "PAY BILL CHARGE": {
        "category": "Fees",
        "subcategory": "Transaction Fee",
        "confidence": 0.95,
    },
    # ✅ OTHERS (catch-all)
    "OTHERS": {"category": "Other", "subcategory": "Uncategorized", "confidence": 0.5},
}

# ✅ MERCHANT/BUSINESS PATTERNS FOR DESCRIPTION-BASED MATCHING
MPESA_MERCHANT_PATTERNS = {
    # Utilities
    "kplc": {"category": "Bills", "subcategory": "Electricity", "confidence": 0.95},
    "kplc prepaid": {
        "category": "Bills",
        "subcategory": "Electricity",
        "confidence": 0.95,
    },
    "electricity": {
        "category": "Bills",
        "subcategory": "Electricity",
        "confidence": 0.9,
    },
    "water": {"category": "Bills", "subcategory": "Water", "confidence": 0.9},
    # Fuel/Transport
    "national oil": {
        "category": "Transport",
        "subcategory": "Fuel",
        "confidence": 0.95,
    },
    "totalenergies": {
        "category": "Transport",
        "subcategory": "Fuel",
        "confidence": 0.95,
    },
    "shell": {"category": "Transport", "subcategory": "Fuel", "confidence": 0.95},
    "wesco oil": {"category": "Transport", "subcategory": "Fuel", "confidence": 0.95},
    # Shopping/Groceries
    "naivas": {"category": "Shopping", "subcategory": "Groceries", "confidence": 0.95},
    "quick mart": {
        "category": "Shopping",
        "subcategory": "Groceries",
        "confidence": 0.95,
    },
    "otomatt": {"category": "Shopping", "subcategory": "Groceries", "confidence": 0.95},
    "supermarket": {
        "category": "Shopping",
        "subcategory": "Groceries",
        "confidence": 0.9,
    },
    # Food/Restaurants
    "java house": {"category": "Food", "subcategory": "Restaurant", "confidence": 0.95},
    "kfc": {"category": "Food", "subcategory": "Restaurant", "confidence": 0.95},
    # Others
    "fuliza": {"category": "Financial", "subcategory": "Loan", "confidence": 0.95},
    "od loan repayment": {
        "category": "Financial",
        "subcategory": "Loan Repayment",
        "confidence": 0.95,
    },
    "pay merchant charge": {
        "category": "Fees",
        "subcategory": "Transaction Fee",
        "confidence": 0.95,
    },
    "business payment from": {
        "category": "Income",
        "subcategory": "Business",
        "confidence": 0.9,
    },
    "funds received from": {
        "category": "Income",
        "subcategory": "Received",
        "confidence": 0.85,
    },
    "customer transfer to": {
        "category": "Transfer",
        "subcategory": "Sent",
        "confidence": 0.9,
    },
}


def categorize_transaction(txn: Dict[str, Any]) -> Dict[str, Any]:
    """
    Categorize a single transaction using M-PESA specific patterns.

    Priority:
    1. Explicit transaction_type mapping (highest priority - FIXED)
    2. Merchant/business pattern in description
    3. Fallback based on sent/received
    """
    description = txn.get("description", txn.get("narration", ""))
    counterparty = txn.get("counterparty", "")
    transaction_type = txn.get("transaction_type", "").upper()
    amount = float(txn.get("amount", 0))

    search_text = f"{description} {counterparty}".lower()

    # 1. ✅ Check transaction type mapping FIRST (highest priority - FIXED)
    if transaction_type in MPESA_TRANSACTION_TYPE_MAP:
        rule = MPESA_TRANSACTION_TYPE_MAP[transaction_type]
        txn["category"] = rule["category"]
        txn["subcategory"] = rule["subcategory"]
        txn["confidence"] = rule["confidence"]
        txn["matched_rule"] = f"type:{transaction_type}"
        txn["original_description"] = description
        return txn

    # 2. ✅ Check merchant/business patterns second
    for merchant, rule in MPESA_MERCHANT_PATTERNS.items():
        if merchant.lower() in search_text:
            txn["category"] = rule["category"]
            txn["subcategory"] = rule["subcategory"]
            txn["confidence"] = rule["confidence"]
            txn["matched_rule"] = f"merchant:{merchant}"
            txn["original_description"] = description
            return txn

    # 3. ✅ Check for transaction type in description (fallback)
    for type_key, rule in MPESA_TRANSACTION_TYPE_MAP.items():
        if type_key in description.upper():
            txn["category"] = rule["category"]
            txn["subcategory"] = rule["subcategory"]
            txn["confidence"] = rule["confidence"] * 0.9
            txn["matched_rule"] = f"desc:{type_key}"
            txn["original_description"] = description
            return txn

    # 4. ✅ Fallback based on amount sign
    if amount < 0:
        txn["category"] = "Expense"
        txn["subcategory"] = "Other"
        txn["confidence"] = 0.4
    else:
        txn["category"] = "Income"
        txn["subcategory"] = "Other"
        txn["confidence"] = 0.4

    txn["original_description"] = description
    return txn


def get_category_stats(transactions: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate category statistics from a list of transactions."""
    stats = {
        "by_category": {},
        "by_subcategory": {},
        "total_income": 0.0,
        "total_expenses": 0.0,
        "net_cashflow": 0.0,
        "transaction_count": len(transactions),
        "category_breakdown": [],
    }

    for txn in transactions:
        category = txn.get("category", "Uncategorized")
        subcategory = txn.get("subcategory", "Other")
        amount = float(txn.get("amount", 0))
        txn_type = txn.get("transaction_type", "").upper()

        # Determine if income or expense
        # Transfers are neutral - they don't affect net flow
        if category == "Transfer":
            continue  # Skip transfers in income/expense totals

        is_income = category == "Income" or txn_type in [
            "RECEIVED",
            "RECEIVED MONEY",
            "RECEIVE_MONEY",
            "AGENT DEPOSIT",
            "BUSINESS PAYMENT",
            "BANK TRANSFER",
            "PROMOTION",
            "FULIZA_REVERSAL",
        ]

        # Track by category
        stats["by_category"][category] = (
            stats["by_category"].get(category, 0.0) + amount
        )

        # Track by subcategory
        key = f"{category}/{subcategory}"
        stats["by_subcategory"][key] = stats["by_subcategory"].get(key, 0.0) + amount

        # Track income/expense totals
        if is_income:
            stats["total_income"] += amount
        else:
            stats["total_expenses"] += amount

    stats["net_cashflow"] = stats["total_income"] - stats["total_expenses"]

    # Build category breakdown for expenses only
    total_expenses = stats["total_expenses"]
    for category, amount in sorted(
        stats["by_category"].items(), key=lambda x: x[1], reverse=True
    ):
        # Skip Income and Transfer categories in expense breakdown
        if category in ["Income", "Transfer"]:
            continue
        percentage = (amount / total_expenses * 100) if total_expenses > 0 else 0
        stats["category_breakdown"].append(
            {
                "category": category,
                "amount": amount,
                "percentage": round(percentage, 1),
            }
        )

    return stats


# ==================== API ENDPOINTS ====================


@app.on_event("startup")
async def startup_event():
    logger.info("🚀 Starting Transaction Categorizer Service (MVP Hardened)...")
    logger.info(
        f"✅ M-PESA transaction types loaded: {len(MPESA_TRANSACTION_TYPE_MAP)}"
    )
    logger.info(f"✅ Merchant patterns loaded: {len(MPESA_MERCHANT_PATTERNS)}")
    logger.info(f"✅ Database connected: {DATABASE_URL}")
    logger.info("✅ Database initialized")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("🛑 Shutting down Transaction Categorizer Service...")


@app.get("/")
async def root():
    return {
        "service": "Transaction Categorizer",
        "version": "1.0.0",
        "status": "running",
        "mpesa_types_loaded": len(MPESA_TRANSACTION_TYPE_MAP),
        "merchant_patterns_loaded": len(MPESA_MERCHANT_PATTERNS),
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
        "transaction_type_map": MPESA_TRANSACTION_TYPE_MAP,
        "merchant_patterns": MPESA_MERCHANT_PATTERNS,
        "categories": list(
            set([v["category"] for v in MPESA_TRANSACTION_TYPE_MAP.values()])
        ),
    }


@app.post("/api/v1/categorizer/test")
async def test_categorization(transaction: Dict[str, Any]):
    """Test categorization on a single transaction."""
    result = categorize_transaction(transaction.copy())
    return {
        "original": transaction,
        "categorized": result,
        "confidence": result.get("confidence", 0),
        "matched_rule": result.get("matched_rule", "none"),
    }


@app.post("/api/v1/categorizer/batch")
async def batch_categorize(request: Request, db: Session = Depends(get_db)):
    """Categorize a batch of transactions and store in database"""
    data = await request.json()
    tenant_id = request.headers.get("X-Tenant-ID", "default")
    transactions = data.get("transactions", [])
    store_results = data.get("store_results", True)

    logger.info(
        f"📊 Batch categorizing {len(transactions)} transactions for tenant {tenant_id}"
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
                logger.error(f"❌ Failed to store transaction: {e}")

    if store_results:
        db.commit()
        logger.info(f"✅ Stored {len(categorized)} categorized transactions")

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
            "category_breakdown": [],
        }

        for txn in transactions:
            amount = float(txn.amount)

            # Skip transfers in income/expense totals
            if txn.category == "Transfer":
                continue

            is_income = txn.category == "Income" or txn.transaction_type in [
                "received",
                "receive_money",
                "received_money",
                "agent_deposit",
                "business_payment",
                "bank_transfer",
                "promotion",
                "fuliza_reversal",
            ]

            stats["by_category"][txn.category] = (
                stats["by_category"].get(txn.category, 0.0) + amount
            )

            subcat_key = f"{txn.category}/{txn.subcategory}"
            stats["by_subcategory"][subcat_key] = (
                stats["by_subcategory"].get(subcat_key, 0.0) + amount
            )

            if is_income:
                stats["total_income"] += amount
            else:
                stats["total_expenses"] += amount

        stats["net_cashflow"] = stats["total_income"] - stats["total_expenses"]

        # Build category breakdown for expenses only
        total_expenses = stats["total_expenses"]
        for category, amount in sorted(
            stats["by_category"].items(), key=lambda x: x[1], reverse=True
        ):
            if category in ["Income", "Transfer"]:
                continue
            percentage = (amount / total_expenses * 100) if total_expenses > 0 else 0
            stats["category_breakdown"].append(
                {
                    "category": category,
                    "amount": amount,
                    "percentage": round(percentage, 1),
                }
            )

        return stats

    except Exception as e:
        logger.error(f"❌ Stats error: {e}")
        return {
            "total_income": 0.0,
            "total_expenses": 0.0,
            "by_category": {},
            "by_subcategory": {},
            "transaction_count": 0,
            "net_cashflow": 0.0,
            "category_breakdown": [],
            "error": str(e),
        }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("src.main:app", host="0.0.0.0", port=8009, reload=True)
