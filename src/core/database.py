# transaction-categorizer/src/core/database.py - COMPLETE VERSION

"""
Database setup for transaction categorizer.
"""

import os
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    create_engine,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from .config import settings

# Create engine
DATABASE_URL = settings.DATABASE_URL

# Configure engine based on database type
if "sqlite" in DATABASE_URL:
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    # PostgreSQL specific configuration
    engine = create_engine(
        DATABASE_URL,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
        pool_recycle=3600,
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class CategorizedTransaction(Base):
    """Stored categorized transaction record."""

    __tablename__ = "categorized_transactions"
    __table_args__ = (
        Index("ix_categorized_tenant_date", "tenant_id", "transaction_date"),
        Index("ix_categorized_tenant_category", "tenant_id", "category"),
        Index("ix_categorized_tenant_merchant", "tenant_id", "merchant"),
        Index("ix_categorized_confidence", "tenant_id", "confidence"),
        Index("ix_categorized_created_at", "tenant_id", "created_at"),
        UniqueConstraint(
            "transaction_id", "tenant_id", name="uq_categorized_transaction"
        ),
    )

    # Primary key
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String(36), nullable=False)

    # Original transaction data
    transaction_id = Column(String(36), nullable=False)  # ✅ Added for deduplication
    original_description = Column(Text, nullable=False)  # ✅ Changed to Text
    amount = Column(Float, nullable=False)
    transaction_type = Column(String(20), nullable=False)
    transaction_date = Column(DateTime, nullable=False)

    # Categorization results
    category = Column(String(50), nullable=False, default="Other")
    confidence = Column(Float, default=0.0)
    confidence_level = Column(String(20), nullable=True)  # ✅ Added: high, medium, low
    rules_applied = Column(Text, nullable=True)  # ✅ Changed to Text

    # Merchant information
    merchant = Column(String(200), nullable=True)  # ✅ Added
    merchant_normalized = Column(String(200), nullable=True)  # ✅ Added

    # Metadata
    phone_number = Column(String(20), nullable=True)
    reference = Column(String(100), nullable=True)
    source = Column(String(50), nullable=True)  # ✅ Added: mpesa, bank, etc.

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )  # ✅ Added

    # Kafka tracking
    kafka_offset = Column(Integer, nullable=True)
    kafka_partition = Column(Integer, nullable=True)

    # Processing metadata
    processing_version = Column(String(20), default="1.0")  # ✅ Added
    processing_duration_ms = Column(Float, nullable=True)  # ✅ Added


class CategoryRule(Base):
    """Categorization rules stored in database."""

    __tablename__ = "category_rules"
    __table_args__ = (
        Index("ix_category_rules_tenant", "tenant_id"),
        Index("ix_category_rules_priority", "tenant_id", "priority"),
        Index("ix_category_rules_active", "tenant_id", "is_active"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(String(36), nullable=True)  # NULL = global rule

    name = Column(String(100), nullable=False)
    pattern = Column(String(500), nullable=False)
    category = Column(String(50), nullable=False)
    confidence = Column(Float, default=0.9)
    priority = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)

    # Additional metadata
    description = Column(Text, nullable=True)  # ✅ Added
    created_by = Column(String(100), nullable=True)  # ✅ Added
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )  # ✅ Added


class CategoryStats(Base):
    """Pre-computed category statistics for faster queries."""

    __tablename__ = "category_stats"
    __table_args__ = (
        Index("ix_category_stats_tenant_category", "tenant_id", "category"),
        Index("ix_category_stats_tenant_date", "tenant_id", "period_date"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(String(36), nullable=False)
    category = Column(String(50), nullable=False)
    period_date = Column(DateTime, nullable=False)  # Start of period
    period_type = Column(String(20), nullable=False)  # day, week, month

    total_amount = Column(Float, default=0.0)
    transaction_count = Column(Integer, default=0)
    average_amount = Column(Float, default=0.0)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class MerchantDirectory(Base):
    """Merchant directory for normalization and classification."""

    __tablename__ = "merchant_directory"
    __table_args__ = (
        Index("ix_merchant_tenant_name", "tenant_id", "name"),
        UniqueConstraint("tenant_id", "name", name="uq_merchant_tenant_name"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(String(36), nullable=True)  # NULL = global merchant

    name = Column(String(200), nullable=False)
    normalized_name = Column(String(200), nullable=False)
    category = Column(String(50), nullable=True)

    # Classification
    type = Column(String(50), default="unknown")  # business, utility, person
    confidence = Column(Float, default=0.0)

    # Metadata
    first_seen = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.utcnow)
    transaction_count = Column(Integer, default=0)

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables and default data."""
    # Create tables
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created/verified")

    # Insert default rules if none exist
    db = SessionLocal()
    try:
        if db.query(CategoryRule).filter(CategoryRule.tenant_id.is_(None)).count() == 0:
            default_rules = [
                # Revenue
                CategoryRule(
                    name="Salary/Wages",
                    pattern=r"\b(salary|wage|payroll|payment received|funds received)\b",
                    category="Revenue",
                    confidence=0.95,
                    priority=10,
                    description="Regular income from employment or business",
                ),
                CategoryRule(
                    name="M-PESA Received",
                    pattern=r"\b(mpesa from|received from|customer payment)\b",
                    category="Revenue",
                    confidence=0.85,
                    priority=9,
                    description="M-PESA mobile money received",
                ),
                CategoryRule(
                    name="Bank Transfer Received",
                    pattern=r"\b(bank transfer|from bank|deposit)\b",
                    category="Revenue",
                    confidence=0.90,
                    priority=8,
                    description="Bank transfers and deposits",
                ),
                # Expenses
                CategoryRule(
                    name="Inventory/Stock",
                    pattern=r"\b(stock|inventory|supplies|wholesale|bulk)\b",
                    category="Inventory",
                    confidence=0.90,
                    priority=8,
                    description="Inventory and stock purchases",
                ),
                CategoryRule(
                    name="Rent/Lease",
                    pattern=r"\b(rent|lease|property|landlord|apartment)\b",
                    category="Rent",
                    confidence=0.95,
                    priority=10,
                    description="Rent and lease payments",
                ),
                CategoryRule(
                    name="Employee Salaries",
                    pattern=r"\b(salary|staff|employee|wage|payroll|team)\b",
                    category="Salaries",
                    confidence=0.95,
                    priority=10,
                    description="Employee salaries and wages",
                ),
                CategoryRule(
                    name="Transport",
                    pattern=r"\b(transport|fuel|uber|bolt|taxi|delivery|matatu|petrol|diesel)\b",
                    category="Transport",
                    confidence=0.85,
                    priority=7,
                    description="Transportation costs including fuel",
                ),
                CategoryRule(
                    name="Utilities",
                    pattern=r"\b(kplc|electricity|water|nairobi water|internet|token|bill)\b",
                    category="Utilities",
                    confidence=0.90,
                    priority=8,
                    description="Utility bills and services",
                ),
                CategoryRule(
                    name="Airtime/Data",
                    pattern=r"\b(airtime|data bundle|safaricom postpaid|customer bundle)\b",
                    category="Airtime & Data",
                    confidence=0.90,
                    priority=8,
                    description="Mobile airtime and data purchases",
                ),
                CategoryRule(
                    name="Loan Repayment",
                    pattern=r"\b(fuliza|od loan|loan|credit repayment|overdraft)\b",
                    category="Loan Repayment",
                    confidence=0.90,
                    priority=9,
                    description="Loan and overdraft repayments",
                ),
                CategoryRule(
                    name="Food & Dining",
                    pattern=r"\b(kfc|java|pizza|restaurant|cafe|hotel|lunch|dinner|food|meal)\b",
                    category="Food & Dining",
                    confidence=0.85,
                    priority=6,
                    description="Food purchases and dining out",
                ),
                CategoryRule(
                    name="Shopping",
                    pattern=r"\b(naivas|quickmart|carrefour|tuskys|supermarket|groceries|shopping|retail)\b",
                    category="Shopping",
                    confidence=0.90,
                    priority=7,
                    description="Shopping and retail purchases",
                ),
                CategoryRule(
                    name="Healthcare",
                    pattern=r"\b(hospital|clinic|doctor|pharmacy|medical|health|medicine)\b",
                    category="Healthcare",
                    confidence=0.90,
                    priority=8,
                    description="Medical and healthcare expenses",
                ),
                CategoryRule(
                    name="Education",
                    pattern=r"\b(school|tuition|university|college|fees|education|books)\b",
                    category="Education",
                    confidence=0.90,
                    priority=8,
                    description="Education and training expenses",
                ),
                CategoryRule(
                    name="Entertainment",
                    pattern=r"\b(netflix|spotify|cinema|movie|game|music|concert|club|entertainment)\b",
                    category="Entertainment",
                    confidence=0.85,
                    priority=6,
                    description="Entertainment and leisure activities",
                ),
                CategoryRule(
                    name="Insurance",
                    pattern=r"\b(insurance|premium|coverage|policy)\b",
                    category="Insurance",
                    confidence=0.90,
                    priority=8,
                    description="Insurance premiums",
                ),
                CategoryRule(
                    name="Savings",
                    pattern=r"\b(savings|deposit|account|investment|stock|bond)\b",
                    category="Savings",
                    confidence=0.80,
                    priority=5,
                    description="Savings and investments",
                ),
                CategoryRule(
                    name="Tax",
                    pattern=r"\b(tax|kra|withholding|vat|excise)\b",
                    category="Tax",
                    confidence=0.90,
                    priority=8,
                    description="Tax payments",
                ),
            ]

            for rule in default_rules:
                db.add(rule)

            db.commit()
            print(f"✅ {len(default_rules)} default rules inserted")

        # Initialize merchant directory with common merchants
        if (
            db.query(MerchantDirectory)
            .filter(MerchantDirectory.tenant_id.is_(None))
            .count()
            == 0
        ):
            default_merchants = [
                MerchantDirectory(
                    name="Naivas",
                    normalized_name="Naivas",
                    category="Shopping",
                    type="business",
                    confidence=0.95,
                ),
                MerchantDirectory(
                    name="Quickmart",
                    normalized_name="Quickmart",
                    category="Shopping",
                    type="business",
                    confidence=0.95,
                ),
                MerchantDirectory(
                    name="KPLC",
                    normalized_name="KPLC",
                    category="Utilities",
                    type="utility",
                    confidence=0.95,
                ),
                MerchantDirectory(
                    name="Safaricom",
                    normalized_name="Safaricom",
                    category="Airtime & Data",
                    type="utility",
                    confidence=0.95,
                ),
                MerchantDirectory(
                    name="Uber",
                    normalized_name="Uber",
                    category="Transport",
                    type="business",
                    confidence=0.90,
                ),
                MerchantDirectory(
                    name="Fuliza",
                    normalized_name="Fuliza",
                    category="Loan Repayment",
                    type="utility",
                    confidence=0.95,
                ),
            ]

            for merchant in default_merchants:
                db.add(merchant)

            db.commit()
            print(f"✅ {len(default_merchants)} default merchants inserted")

    except Exception as e:
        db.rollback()
        print(f"❌ Error initializing database: {e}")
        raise
    finally:
        db.close()


# Export for use in other modules
__all__ = [
    "engine",
    "SessionLocal",
    "Base",
    "get_db",
    "init_db",
    "CategorizedTransaction",
    "CategoryRule",
    "CategoryStats",
    "MerchantDirectory",
]
