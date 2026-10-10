import requests
import json

# Test batch categorization
url = "http://localhost:8009/api/v1/categorizer/batch"
headers = {
    "Content-Type": "application/json",
    "X-Tenant-ID": "test123"
}

data = {
    "transactions": [
        {
            "description": "Pay Bill to 888880 - KPLC PREPAID",
            "amount": 50.00,
            "transaction_type": "sent",
            "counterparty": "KPLC",
            "transaction_date": "2026-06-08T10:00:00"
        },
        {
            "description": "Funds received from JOHN DOE",
            "amount": 1500.00,
            "transaction_type": "received",
            "counterparty": "JOHN DOE",
            "transaction_date": "2026-06-08T09:00:00"
        },
        {
            "description": "Merchant Payment to Naivas Supermarket",
            "amount": 250.00,
            "transaction_type": "sent",
            "counterparty": "Naivas",
            "transaction_date": "2026-06-08T08:00:00"
        }
    ]
}

print("Testing batch categorization...")
response = requests.post(url, json=data, headers=headers)
print(f"Status: {response.status_code}")
print("Response:")
print(json.dumps(response.json(), indent=2))

# Test getting categories
print("\n" + "="*50)
print("Getting available categories...")
url_categories = "http://localhost:8009/api/v1/categorizer/categories"
response = requests.get(url_categories)
print(f"Status: {response.status_code}")
data = response.json()
print(f"Total merchant patterns: {len(data.get('merchant_patterns', {}))}")
print(f"Categories available: {data.get('categories', [])[:10]}...")

# Test tenant stats
print("\n" + "="*50)
print("Getting tenant statistics...")
url_stats = "http://localhost:8009/api/v1/categorizer/stats/test123"
response = requests.get(url_stats)
print(f"Status: {response.status_code}")
print(json.dumps(response.json(), indent=2))
