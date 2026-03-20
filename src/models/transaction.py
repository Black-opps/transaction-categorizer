"""
Pydantic models for transaction categorization.
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict
from datetime import datetime
from uuid import UUID, uuid4
from enum import Enum


class TransactionType(str, Enum):
    """Transaction direction types."""
    INCOME = "income"
    EXPENSE = "expense"
    TRANSFER = "transfer"
    UNKNOWN = "unknown"


class Category(str, Enum):
    """Available transaction categories."""
    REVENUE = "Revenue"
    INVENTORY = "Inventory"
    RENT = "Rent"
    SALARIES = "Salaries"
    TRANSPORT = "Transport"
    UTILITIES = "Utilities"
    OTHER = "Other"


class Transaction(BaseModel):
    """Raw transaction model (tenant_id is provided at request level for batches)."""
    id: Optional[UUID] = None
    amount: float
    description: str
    phone_number: Optional[str] = None
    transaction_date: datetime
    transaction_type: TransactionType = TransactionType.UNKNOWN
    reference: Optional[str] = None

    @field_validator("amount")
    @classmethod
    def amount_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Amount must be positive")
        return v


class CategorizedTransaction(Transaction):
    """Transaction after categorization."""
    tenant_id: UUID
    category: Category = Category.OTHER
    confidence: float = Field(0.0, ge=0.0, le=1.0)
    category_rules_applied: List[str] = Field(default_factory=list)
    categorized_at: datetime = Field(default_factory=datetime.utcnow)


class CategorizationRequest(BaseModel):
    """Request for batch transaction categorization."""
    tenant_id: UUID
    transactions: List[Transaction]


class CategorizationResponse(BaseModel):
    """Response from batch categorization."""
    categorized_transactions: List[CategorizedTransaction]
    stats: Dict[str, int]
    processing_time_ms: float


class CategorizationRule(BaseModel):
    """Single categorization rule."""
    id: UUID = Field(default_factory=uuid4)
    name: str = ""
    category: Category
    patterns: List[str]
    confidence: float = Field(1.0, ge=0.0, le=1.0)
    is_active: bool = True
    priority: int = 0