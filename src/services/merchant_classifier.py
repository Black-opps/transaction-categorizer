# transaction-categorizer/src/services/merchant_classifier.py - NEW

from typing import Dict, List, Optional, Tuple

from src.models.transaction import Category


class MerchantClassifier:
    """Classify merchants by name with enhanced mapping"""

    # Merchant → Category mapping
    MERCHANT_MAP = {
        # Groceries & Shopping
        "naivas": Category.SHOPPING,
        "quickmart": Category.SHOPPING,
        "tuskys": Category.SHOPPING,
        "carrefour": Category.SHOPPING,
        "lilton": Category.SHOPPING,
        "supermarket": Category.SHOPPING,
        # Food & Dining
        "kfc": Category.FOOD_DINING,
        "java": Category.FOOD_DINING,
        "pizza": Category.FOOD_DINING,
        "restaurant": Category.FOOD_DINING,
        "cafe": Category.FOOD_DINING,
        "hotel": Category.FOOD_DINING,
        # Transport
        "uber": Category.TRANSPORT,
        "bolt": Category.TRANSPORT,
        "taxi": Category.TRANSPORT,
        "fuel": Category.TRANSPORT,
        "petrol": Category.TRANSPORT,
        "shell": Category.TRANSPORT,
        "total": Category.TRANSPORT,
        # Utilities
        "kplc": Category.UTILITIES,
        "water": Category.UTILITIES,
        "nairobi water": Category.UTILITIES,
        "electricity": Category.UTILITIES,
        "token": Category.UTILITIES,
        # Telecom
        "safaricom": Category.AIRTIME_DATA,
        "airtel": Category.AIRTIME_DATA,
        "telkom": Category.AIRTIME_DATA,
        "airtime": Category.AIRTIME_DATA,
        "data": Category.AIRTIME_DATA,
        # Rent
        "rent": Category.RENT,
        "landlord": Category.RENT,
        "apartment": Category.RENT,
        # Loan Repayment
        "fuliza": Category.LOAN_REPAYMENT,
        "od loan": Category.LOAN_REPAYMENT,
        "loan": Category.LOAN_REPAYMENT,
        # Entertainment
        "netflix": Category.ENTERTAINMENT,
        "spotify": Category.ENTERTAINMENT,
        "cinema": Category.ENTERTAINMENT,
        "movie": Category.ENTERTAINMENT,
        # Healthcare
        "hospital": Category.HEALTHCARE,
        "clinic": Category.HEALTHCARE,
        "pharmacy": Category.HEALTHCARE,
        "doctor": Category.HEALTHCARE,
        # Education
        "school": Category.EDUCATION,
        "tuition": Category.EDUCATION,
        "university": Category.EDUCATION,
        "college": Category.EDUCATION,
    }

    # Normalization rules
    NORMALIZATION_RULES = [
        (" ltd", ""),
        (" limited", ""),
        (" kenya", ""),
        (" store", ""),
        (" supermarket", ""),
        (" restaurant", ""),
        (" hotel", ""),
        (" pharmacy", ""),
    ]

    @classmethod
    def classify(cls, merchant: str) -> Optional[Category]:
        """Classify a merchant"""
        if not merchant:
            return None

        merchant_lower = merchant.lower().strip()

        # Check exact matches first
        for name, category in cls.MERCHANT_MAP.items():
            if name in merchant_lower:
                return category

        return None

    @classmethod
    def classify_with_confidence(
        cls, merchant: str
    ) -> Tuple[Optional[Category], float]:
        """Classify a merchant with confidence score"""
        category = cls.classify(merchant)

        if not category:
            return None, 0.0

        # Calculate confidence based on match quality
        merchant_lower = merchant.lower().strip()
        confidence = 0.7  # Base confidence

        # Exact match gets higher confidence
        for name in cls.MERCHANT_MAP.keys():
            if name == merchant_lower:
                confidence = 0.95
                break
            elif name in merchant_lower and len(name) > 5:
                confidence = 0.85
                break

        return category, confidence

    @classmethod
    def get_normalized_name(cls, merchant: str) -> str:
        """Get normalized merchant name"""
        if not merchant:
            return ""

        merchant_lower = merchant.lower().strip()
        normalized = merchant_lower

        # Apply normalization rules
        for old, new in cls.NORMALIZATION_RULES:
            if normalized.endswith(old):
                normalized = normalized[: -len(old)]

        # Capitalize words
        words = normalized.split()
        normalized = " ".join([w.capitalize() for w in words if w])

        return normalized or merchant

    @classmethod
    def get_categories(cls) -> List[Dict[str, str]]:
        """Get all merchant categories with examples"""
        categories = {}
        for merchant, category in cls.MERCHANT_MAP.items():
            if category.value not in categories:
                categories[category.value] = []
            categories[category.value].append(merchant)

        return [
            {"category": cat, "merchants": merchants[:5]}
            for cat, merchants in categories.items()
        ]
