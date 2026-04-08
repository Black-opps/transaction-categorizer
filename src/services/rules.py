"""
Rule-based transaction categorization engine.
"""
import re
import logging
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class Category(str, Enum):
    """Available transaction categories."""
    REVENUE = "Revenue"
    INVENTORY = "Inventory"
    RENT = "Rent"
    SALARIES = "Salaries"
    TRANSPORT = "Transport"
    UTILITIES = "Utilities"
    OTHER = "Other"


@dataclass
class Rule:
    """Categorization rule."""
    pattern: str
    category: str
    confidence: float = 0.9
    priority: int = 0
    name: str = ""
    
    def __post_init__(self):
        self.compiled = re.compile(self.pattern, re.IGNORECASE)
        if not self.name:
            self.name = self.pattern[:50]
    
    def matches(self, text: str) -> bool:
        """Check if rule matches the text."""
        return bool(self.compiled.search(text))


class CategorizationRules:
    """Rule-based categorization engine."""
    
    def __init__(self, rules: List[Rule] = None):
        self.rules = rules or []
        self.rules.sort(key=lambda r: r.priority, reverse=True)
    
    def categorize(self, description: str) -> Tuple[str, float, List[str]]:
        """
        Categorize a transaction description.
        
        Returns:
            Tuple of (category, confidence, matched_patterns)
        """
        matched_patterns = []
        best_match = Category.OTHER.value
        best_confidence = 0.0
        
        for rule in self.rules:
            if rule.matches(description):
                matched_patterns.append(rule.pattern)
                if rule.confidence > best_confidence:
                    best_confidence = rule.confidence
                    best_match = rule.category
                if best_confidence >= 0.95:
                    break
        
        return best_match, best_confidence, matched_patterns
    
    def add_rule(self, pattern: str, category: str, confidence: float = 1.0, priority: int = 0) -> Rule:
        """Add a new categorization rule."""
        new_rule = Rule(pattern, category, confidence, priority)
        self.rules.append(new_rule)
        self.rules.sort(key=lambda r: r.priority, reverse=True)
        return new_rule
    
    def get_rules(self) -> List[dict]:
        """Get all rules as dictionaries."""
        return [
            {
                "pattern": r.pattern,
                "category": r.category,
                "confidence": r.confidence,
                "priority": r.priority,
                "name": r.name
            }
            for r in self.rules
        ]


# Default rules
DEFAULT_RULES = [
    Rule(r"\b(salary|wage|payroll|payment received)\b", Category.REVENUE.value, confidence=0.95, priority=10, name="Salary"),
    Rule(r"\b(mpesa from|received from|deposit)\b", Category.REVENUE.value, confidence=0.85, priority=9, name="M-PESA_Received"),
    Rule(r"\b(stock|inventory|supplies|wholesale|purchase)\b", Category.INVENTORY.value, confidence=0.9, priority=8, name="Inventory"),
    Rule(r"\b(rent|lease|property|landlord)\b", Category.RENT.value, confidence=0.95, priority=10, name="Rent"),
    Rule(r"\b(salary|staff|employee|wage|payroll)\b", Category.SALARIES.value, confidence=0.95, priority=10, name="Salaries"),
    Rule(r"\b(transport|fuel|uber|taxi|delivery|petrol)\b", Category.TRANSPORT.value, confidence=0.85, priority=7, name="Transport"),
    Rule(r"\b(kplc|electricity|water|internet|safaricom|airtime|token)\b", Category.UTILITIES.value, confidence=0.9, priority=8, name="Utilities"),
]


def get_default_engine() -> CategorizationRules:
    """Get default rule engine."""
    return CategorizationRules(DEFAULT_RULES)