import requests
import json

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
    ],
    "store_results": True
}

print("Storing transactions...")
response = requests.post(url, json=data, headers=headers)
print(f"Status: {response.status_code}")
result = response.json()
print(f"Stored: {result.get('count')} transactions")
print(f"Tenant: {result.get('tenant_id')}")
print(f"Net cashflow: {result.get('stats', {}).get('net_cashflow')}")
