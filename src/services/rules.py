# src/services/rules.py
import re
from typing import List, Optional, Tuple

from src.models.transaction import Category


class MpesaRuleEngine:
    """M-PESA specific categorization rules."""

    # M-PESA specific patterns
    MPESA_PATTERNS = {
        # Revenue
        Category.REVENUE: [
            r"(?:funds received from|payment from|customer paid|received from)",
            r"(?:business payment|salary payment|wage|payroll)",
            r"(?:bank transfer|from bank)",
        ],
        # Fuel (Transport subcategory)
        "Fuel": [
            r"(?:national oil|total|shell|astrol|petrol|diesel|fuel|gas|oil)",
            r"(?:petrol station|filling station|energies)",
        ],
        # Maintenance
        "Maintenance": [
            r"(?:repair|service|spare parts|tyre|battery|garage|mechanic)",
            r"(?:workshop|maintenance|oil change)",
        ],
        # Loan Repayment
        "Loan Repayment": [
            r"(?:loan repayment|fuliza|od loan repayment|credit repayment)",
            r"(?:overdraft|loan payment)",
        ],
        # Parking & Toll
        "Parking & Toll": [
            r"(?:parking|toll|kaps parking|expressway)",
            r"(?:parking fee|toll fee)",
        ],
        # Airtime & Data
        "Airtime & Data": [
            r"(?:airtime|data bundle|internet|safaricom postpaid)",
            r"(?:customer bundle purchase|airtime purchase)",
        ],
        # Shopping
        "Shopping": [
            r"(?:naivas|quickmart|carrefour|tuskys|lilton|supermarket)",
            r"(?:shopping|groceries|store|retail)",
        ],
        # Food & Dining
        "Food & Dining": [
            r"(?:java|kfc|pizza|restaurant|cafe|hotel|lunch|dinner)",
            r"(?:food|meal|coffee|lunch box|takeaway)",
        ],
        # Rent/Lease
        Category.RENT: [
            r"(?:rent|lease|property|landlord)",
            r"(?:apartment|office rent|space)",
        ],
    }

    def categorize(
        self, description: str, amount: float, transaction_type: str
    ) -> Tuple[str, float, List[str]]:
        """
        Categorize based on M-PESA patterns.
        Returns: (category, confidence, matched_rules)
        """
        desc_lower = description.lower()
        matched_rules = []

        # First check for specific M-PESA transaction types
        if "pay bill to 888880" in desc_lower:
            return "Utilities", 0.95, ["paybill_kplc"]
        elif "pay bill to 200200" in desc_lower:
            return "Airtime & Data", 0.95, ["paybill_safaricom"]
        elif "merchant payment to" in desc_lower and "naivas" in desc_lower:
            return "Shopping", 0.95, ["merchant_naivas"]
        elif "customer transfer to" in desc_lower and "fuliza" in desc_lower:
            return "Loan Repayment", 0.95, ["fuliza_repayment"]

        # Check patterns
        for category, patterns in self.MPESA_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, desc_lower, re.IGNORECASE):
                    matched_rules.append(pattern)
                    confidence = 0.85 if len(patterns) > 5 else 0.9
                    return category, confidence, matched_rules

        # Default based on transaction type
        if transaction_type == "income":
            return "Revenue", 0.6, ["default_income"]
        elif transaction_type == "expense":
            return "Other", 0.5, ["default_expense"]

        return "Other", 0.3, ["unknown"]
