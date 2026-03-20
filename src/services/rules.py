# src/services/rules.py
"""
Rule-based transaction categorization engine.
"""
import re
from typing import List, Tuple, Optional
from enum import Enum


class Category(str, Enum):
    """Available transaction categories."""
    REVENUE = "Revenue"
    INVENTORY = "Inventory"
    RENT = "Rent"
    SALARIES = "Salaries"
    TRANSPORT = "Transport"
    UTILITIES = "Utilities"
    OTHER = "Other"


class Rule:
    """Categorization rule."""
    
    def __init__(self, pattern: str, category: Category, confidence: float = 1.0, priority: int = 0):
        self.pattern = re.compile(pattern, re.IGNORECASE)
        self.category = category
        self.confidence = confidence
        self.priority = priority
    
    def matches(self, text: str) -> bool:
        """Check if rule matches the text."""
        return bool(self.pattern.search(text))


# Default categorization rules
DEFAULT_RULES = [
    # Revenue patterns
    Rule(r"\b(salary|wage|payment|received|income|deposit)\b", Category.REVENUE, confidence=0.95, priority=10),
    Rule(r"\b(mpesa from|bank transfer|credit)\b", Category.REVENUE, confidence=0.85, priority=9),
    Rule(r"\b(sale|sales|invoice|payment received)\b", Category.REVENUE, confidence=0.9, priority=10),
    
    # Inventory patterns
    Rule(r"\b(stock|inventory|supplies|raw materials)\b", Category.INVENTORY, confidence=0.9, priority=8),
    Rule(r"\b(supplier|wholesale|purchase order)\b", Category.INVENTORY, confidence=0.85, priority=8),
    Rule(r"\b(shop|store|retail|goods)\b", Category.INVENTORY, confidence=0.8, priority=7),
    
    # Rent patterns
    Rule(r"\b(rent|lease|property|landlord)\b", Category.RENT, confidence=0.95, priority=10),
    Rule(r"\b(premises|office space|shop rent)\b", Category.RENT, confidence=0.9, priority=9),
    
    # Salaries patterns
    Rule(r"\b(salary|wage|payroll|employee)\b", Category.SALARIES, confidence=0.95, priority=10),
    Rule(r"\b(staff|worker|contractor|temporary)\b", Category.SALARIES, confidence=0.85, priority=8),
    
    # Transport patterns
    Rule(r"\b(transport|fuel|petrol|diesel)\b", Category.TRANSPORT, confidence=0.9, priority=8),
    Rule(r"\b(taxi|uber|bolt|delivery)\b", Category.TRANSPORT, confidence=0.85, priority=7),
    Rule(r"\b(maintenance|repair|service)\b", Category.TRANSPORT, confidence=0.7, priority=5),
    
    # Utilities patterns
    Rule(r"\b(electricity|power|kplc)\b", Category.UTILITIES, confidence=0.95, priority=10),
    Rule(r"\b(water|sewer|nwsc)\b", Category.UTILITIES, confidence=0.95, priority=10),
    Rule(r"\b(internet|wifi|broadband|safaricom)\b", Category.UTILITIES, confidence=0.85, priority=8),
    Rule(r"\b(airtime|data bundle|phone bill)\b", Category.UTILITIES, confidence=0.8, priority=7),
]


class CategorizationRules:
    """Rule-based categorization engine."""
    
    def __init__(self, rules: List[Rule] = None):
        self.rules = rules or DEFAULT_RULES.copy()
        # Sort by priority (higher priority first)
        self.rules.sort(key=lambda r: r.priority, reverse=True)
    
    def categorize(self, description: str) -> Tuple[Category, float, List[str]]:
        """
        Categorize a transaction description.
        
        Args:
            description: Transaction description text
            
        Returns:
            Tuple of (category, confidence, matched_patterns)
        """
        matched_patterns = []
        best_match = Category.OTHER
        best_confidence = 0.0
        
        for rule in self.rules:
            if rule.matches(description):
                matched_patterns.append(rule.pattern.pattern)
                if rule.confidence > best_confidence:
                    best_confidence = rule.confidence
                    best_match = rule.category
        
        return best_match, best_confidence, matched_patterns
    
    def add_rule(self, pattern: str, category: Category, confidence: float = 1.0, priority: int = 0) -> Rule:
        """Add a new categorization rule."""
        new_rule = Rule(pattern, category, confidence, priority)
        self.rules.append(new_rule)
        self.rules.sort(key=lambda r: r.priority, reverse=True)
        return new_rule
    
    def remove_rule(self, index: int) -> Optional[Rule]:
        """Remove a rule by index."""
        if 0 <= index < len(self.rules):
            return self.rules.pop(index)
        return None
    
    def get_rules(self) -> List[dict]:
        """Get all rules as dictionaries."""
        return [
            {
                "pattern": r.pattern.pattern,
                "category": r.category.value,
                "confidence": r.confidence,
                "priority": r.priority
            }
            for r in self.rules
        ]