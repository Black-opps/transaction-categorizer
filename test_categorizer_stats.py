import requests
import json

# Test the categorizer stats
url = "http://localhost:8009/api/v1/categorizer/stats/test123"
response = requests.get(url)

print("=" * 50)
print("CATEGORIZER STATS")
print("=" * 50)
print(f"Status: {response.status_code}")

if response.status_code == 200:
    data = response.json()
    print(f"Total transactions: {data.get('transaction_count', 0)}")
    print(f"Total income: {data.get('total_income', 0)}")
    print(f"Total expenses: {data.get('total_expenses', 0)}")
    print(f"Net cashflow: {data.get('net_cashflow', 0)}")
    print(f"Categories: {list(data.get('by_category', {}).keys())}")
    print(f"\nCategory breakdown:")
    for cat, amount in data.get('by_category', {}).items():
        print(f"  {cat}: {amount}")
else:
    print(f"Error: {response.text}")

# Test the parser-categorizer integration with a new CSV
print("\n" + "=" * 50)
print("UPLOADING TEST CSV")
print("=" * 50)

csv_content = """Receipt No,Completion Time,Details,Transaction Status,Paid In,Withdrawn,Balance
TEST001,2026-06-08 10:00:00,Pay Bill to 888880 - KPLC PREPAID,Completed,50,,1000
TEST002,2026-06-08 11:00:00,Merchant Payment to Naivas,Completed,,250,750
TEST003,2026-06-08 12:00:00,Funds received from JOHN DOE,Completed,1500,,2250"""

# Save to temp file
import tempfile
with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
    f.write(csv_content)
    temp_file = f.name

# Upload to parser
parser_url = "http://localhost:8004/api/v1/parser/upload"
headers = {"X-Tenant-ID": "test123"}

with open(temp_file, 'rb') as f:
    files = {"file": ("test.csv", f, "text/csv")}
    response = requests.post(parser_url, files=files, headers=headers)
    
    print(f"Status: {response.status_code}")
    result = response.json()
    print(f"Success: {result.get('success', False)}")
    print(f"Saved: {result.get('saved_count', 0)} transactions")
    print(f"Message: {result.get('message', '')}")

# Clean up
import os
os.unlink(temp_file)
