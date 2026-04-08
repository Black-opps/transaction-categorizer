"""
Database setup for transaction categorizer.
"""
from sqlalchemy import create_engine, Column, String, Float, DateTime, Integer, Boolean, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import uuid

from .config import settings

# Create engine (SQLite for development)
DATABASE_URL = settings.DATABASE_URL  # Use the attribute from settings

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class CategorizedTransaction(Base):
    """Stored categorized transaction record."""
    __tablename__ = "categorized_transactions"
    __table_args__ = (
        Index('ix_categorized_tenant_date', 'tenant_id', 'transaction_date'),
        Index('ix_categorized_tenant_category', 'tenant_id', 'category'),
    )
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String(36), nullable=False)
    original_description = Column(String(500), nullable=False)
    amount = Column(Float, nullable=False)
    transaction_type = Column(String(20), nullable=False)
    transaction_date = Column(DateTime, nullable=False)
    
    # Categorization results
    category = Column(String(50), nullable=False, default="Other")
    confidence = Column(Float, default=0.0)
    rules_applied = Column(String(500))
    
    # Metadata
    phone_number = Column(String(20), nullable=True)
    reference = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime, default=datetime.utcnow)
    
    # Kafka tracking
    kafka_offset = Column(Integer, nullable=True)
    kafka_partition = Column(Integer, nullable=True)


class CategoryRule(Base):
    """Categorization rules stored in database."""
    __tablename__ = "category_rules"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    pattern = Column(String(500), nullable=False)
    category = Column(String(50), nullable=False)
    confidence = Column(Float, default=0.9)
    priority = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    tenant_id = Column(String(36), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)
    print("Database tables created/verified")
    
    # Insert default rules if none exist
    db = SessionLocal()
    if db.query(CategoryRule).count() == 0:
        default_rules = [
            CategoryRule(name="Salary", pattern=r"\b(salary|wage|payroll|payment received)\b", category="Revenue", confidence=0.95, priority=10),
            CategoryRule(name="M-PESA Received", pattern=r"\b(mpesa from|received from)\b", category="Revenue", confidence=0.85, priority=9),
            CategoryRule(name="Inventory", pattern=r"\b(stock|inventory|supplies|wholesale)\b", category="Inventory", confidence=0.9, priority=8),
            CategoryRule(name="Rent", pattern=r"\b(rent|lease|property)\b", category="Rent", confidence=0.95, priority=10),
            CategoryRule(name="Salaries", pattern=r"\b(salary|staff|employee|wage)\b", category="Salaries", confidence=0.95, priority=10),
            CategoryRule(name="Transport", pattern=r"\b(transport|fuel|uber|taxi|delivery)\b", category="Transport", confidence=0.85, priority=7),
            CategoryRule(name="Utilities", pattern=r"\b(kplc|electricity|water|internet|safaricom)\b", category="Utilities", confidence=0.9, priority=8),
        ]
        for rule in default_rules:
            db.add(rule)
        db.commit()
        print("Default rules inserted")
    db.close()