import asyncio
import json
import uuid
from datetime import datetime
import pika

async def publish_test_transactions():
    """Simulate parser service publishing transactions"""
    
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()
    
    # Declare queue (ensure it exists)
    channel.queue_declare(queue='transactions.parsed', durable=True)
    
    # Sample transactions from your PDF
    test_transactions = [
        {
            "transaction_id": "TEST001",
            "amount": 50.00,
            "description": "Pay Bill to 888880 - KPLC PREPAID",
            "counterparty": "KPLC",
            "transaction_type": "sent",
            "transaction_date": "2026-05-24T20:13:05",
            "reference": "UBONY7L217",
            "phone_number": "2547xxxxxx780"
        },
        {
            "transaction_id": "TEST002",
            "amount": 1500.00,
            "description": "Funds received from JOHN DOE",
            "counterparty": "JOHN DOE",
            "transaction_type": "received",
            "transaction_date": "2026-05-24T15:30:00",
            "reference": "UBONY7M345",
            "phone_number": "2547xxxxxx181"
        },
        {
            "transaction_id": "TEST003",
            "amount": 250.00,
            "description": "Merchant Payment to Naivas Supermarket",
            "counterparty": "Naivas",
            "transaction_type": "sent",
            "transaction_date": "2026-05-24T12:05:14",
            "reference": "UBPNY7MO5W",
            "phone_number": ""
        }
    ]
    
    message = {
        "tenant_id": "test123",
        "data": {
            "transactions": test_transactions,
            "file_name": "test_statement.pdf",
            "upload_id": str(uuid.uuid4())
        },
        "trace_id": str(uuid.uuid4()),
        "meta": {
            "source": "parser",
            "timestamp": datetime.now().isoformat()
        }
    }
    
    channel.basic_publish(
        exchange='',
        routing_key='transactions.parsed',
        body=json.dumps(message),
        properties=pika.BasicProperties(
            delivery_mode=2,  # persistent
            content_type='application/json'
        )
    )
    
    print(f"📤 Published {len(test_transactions)} test transactions to categorizer")
    print(f"   Queue: transactions.parsed")
    print(f"   Tenant: test123")
    
    connection.close()

if __name__ == "__main__":
    asyncio.run(publish_test_transactions())
