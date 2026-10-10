import requests

print("Testing stats endpoint...")
url = "http://localhost:8009/api/v1/categorizer/stats/test123"
response = requests.get(url)

print(f"Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"Total income: {data.get('total_income')}")
    print(f"Total expenses: {data.get('total_expenses')}")
    print(f"Net cashflow: {data.get('net_cashflow')}")
    print(f"Transaction count: {data.get('transaction_count')}")
    print(f"Categories: {list(data.get('by_category', {}).keys())}")
else:
    print(f"Error: {response.text}")
