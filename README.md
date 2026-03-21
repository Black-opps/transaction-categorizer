📊 Transaction Categorizer Service
[<image-card alt="CI - Lint & Test" src="https://github.com/Black-opps/transaction-categorizer/actions/workflows/ci.yml/badge.svg" ></image-card>](https://github.com/Black-opps/transaction-categorizer/actions/workflows/ci.yml)
[<image-card alt="Docker CD - Build & Push" src="https://github.com/Black-opps/transaction-categorizer/actions/workflows/docker-cd.yml/badge.svg" ></image-card>](https://github.com/Black-opps/transaction-categorizer/actions/workflows/docker-cd.yml)
[![CI - Lint & Test](https://github.com/Black-opps/transaction-categorizer/actions/workflows/ci.yml/badge.svg)](https://github.com/Black-opps/transaction-categorizer/actions/workflows/ci.yml)

https://img.shields.io/badge/FastAPI-0.104.0-009688.svg?style=for-the-badge&logo=fastapi
https://img.shields.io/badge/Python-3.12-3776AB.svg?style=for-the-badge&logo=python
https://img.shields.io/badge/Kafka-Ready-231F20.svg?style=for-the-badge&logo=apache-kafka
https://img.shields.io/badge/Docker-Ready-2496ED.svg?style=for-the-badge&logo=docker

Event-driven microservice that consumes parsed M-PESA transactions from Kafka, categorizes them using rule-based logic, and publishes categorized results for downstream analytics.

Part of the larger M-PESA SaaS platform — a multi-tenant, production-ready fintech ecosystem.

📋 Overview
The Transaction Categorizer Service is the intelligence layer that transforms raw M-PESA transaction descriptions into meaningful business categories. It uses a flexible rule-based engine with confidence scoring, making it ideal for both real-time and batch processing scenarios.

Why This Service?
Eliminates manual categorization of thousands of transactions

Enables downstream analytics (cashflow analysis, budgeting, reporting)

Provides auditability with tracked rules and confidence scores

Scales horizontally with event-driven architecture

✨ Features
Core Capabilities
Rule-based categorization — keyword/pattern matching with priority levels

Confidence scoring — each categorization includes a confidence score (0.0–1.0)

Rule tracking — records which rules matched a transaction

Single transaction endpoint — real-time / manual categorization

Batch categorization endpoint — high-throughput processing

Rule management — list, add, and remove categorization rules dynamically

Health checks — monitoring-ready endpoint

OpenAPI documentation — interactive Swagger UI at /api/docs

Architecture-Ready
Kafka consumer (placeholder implemented) — ready to consume from raw-transactions topic

Kafka producer (placeholder) — ready to publish to categorized-transactions topic

Async-first design — built with FastAPI's async capabilities

Pydantic v2 validation — type-safe request/response models

Multi-tenant ready — tenant_id isolation throughout

🏗️ Architecture
text
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│ Kafka Topic │────▶│ Consumer │────▶│ Categorizer │
│ raw-transactions│ │ (placeholder) │ │ Engine │
└─────────────────┘ └─────────────────┘ └─────────────────┘
│
▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│ API Gateway │◀────│ REST API │◀────│ Categorized │
│ (Port 8003) │ │ (Port 8001) │ │ Transactions │
└─────────────────┘ └─────────────────┘ └─────────────────┘
│
▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│ Kafka Topic │────▶│ Producer │────▶│ Cashflow │
│ categorized-tx │ │ (placeholder) │ │ Analyzer │
└─────────────────┘ └─────────────────┘ └─────────────────┘
🛠️ Technology Stack
Layer Technology Purpose
API Framework FastAPI 0.104 High-performance async web framework
Validation Pydantic v2 Type-safe request/response models
Configuration pydantic-settings Environment-based configuration
ASGI Server Uvicorn Production-ready server
Message Broker Kafka (planned) Event streaming for async processing
Cache Redis (optional) Performance optimization
Language Python 3.12 Modern async features
📁 Project Structure
text
transaction-categorizer/
├── src/
│ ├── api/
│ │ ├── **init**.py
│ │ └── routes.py # FastAPI endpoints
│ ├── core/
│ │ ├── **init**.py
│ │ └── config.py # Configuration management
│ ├── models/
│ │ ├── **init**.py
│ │ └── transaction.py # Pydantic models
│ ├── services/
│ │ ├── **init**.py
│ │ ├── categorizer.py # Main categorization logic
│ │ └── rules.py # Rule engine & patterns
│ ├── consumers/
│ │ ├── **init**.py
│ │ └── kafka_consumer.py # Kafka consumer (placeholder)
│ └── main.py # Application entry point
├── tests/ # Test suite
├── data/ # Runtime data storage
├── requirements.txt # Python dependencies
├── Dockerfile # Containerization
├── .env.example # Environment variables template
└── README.md # This file
🚀 Quick Start
Prerequisites
Python 3.12+

Kafka (optional, for event streaming)

Redis (optional, for caching)

Local Development
bash

# 1. Clone the repository

git clone https://github.com/Black-opps/transaction-categorizer.git
cd transaction-categorizer

# 2. Create and activate virtual environment

python -m venv venv

# Windows

.\venv\Scripts\activate

# Linux/macOS

source venv/bin/activate

# 3. Install dependencies

pip install -r requirements.txt

# 4. Configure environment

cp .env.example .env

# Edit .env if needed (KAFKA_BOOTSTRAP_SERVERS, REDIS_URL, etc.)

# 5. Run the service

uvicorn src.main:app --reload --port 8001
Verify Installation
bash

# Health check

curl http://localhost:8001/health

# Service info

curl http://localhost:8001/

# Open Swagger documentation

start http://localhost:8001/api/docs
📡 API Endpoints
Method Endpoint Description
GET / Service information
GET /health Health check
POST /api/v1/categorize/ Categorize batch of transactions
POST /api/v1/categorize/single Categorize single transaction
GET /api/v1/categorize/rules List all active rules
POST /api/v1/categorize/rules Add new categorization rule
DELETE /api/v1/categorize/rules/{rule_id} Remove a rule
GET /api/v1/categorize/stats Categorization statistics
📝 Example Usage
Categorize a Single Transaction
bash
curl -X POST http://localhost:8001/api/v1/categorize/single \
 -H "Content-Type: application/json" \
 -d '{
"tenant_id": "12345678-1234-1234-1234-123456789012",
"amount": 50000,
"description": "Salary payment for staff",
"transaction_date": "2026-03-20T10:00:00Z",
"transaction_type": "expense"
}'
Response:

json
{
"id": "abc123...",
"tenant_id": "12345678-1234-1234-1234-123456789012",
"amount": 50000,
"description": "Salary payment for staff",
"category": "Salaries",
"confidence": 0.95,
"category_rules_applied": ["salary"],
"categorized_at": "2026-03-20T10:00:01Z"
}
Batch Categorization
bash
curl -X POST http://localhost:8001/api/v1/categorize/ \
 -H "Content-Type: application/json" \
 -d '{
"tenant_id": "12345678-1234-1234-1234-123456789012",
"transactions": [
{
"amount": 50000,
"description": "Salary payment",
"transaction_date": "2026-03-20T10:00:00Z",
"transaction_type": "expense"
},
{
"amount": 10000,
"description": "Electricity bill KPLC",
"transaction_date": "2026-03-20T11:00:00Z",
"transaction_type": "expense"
}
]
}'
Response:

json
{
"categorized_transactions": [...],
"stats": {
"Revenue": 0,
"Salaries": 1,
"Utilities": 1,
"Other": 0
},
"processing_time_ms": 12.5
}
📊 Categorization Rules
Default Categories
Category Description Example Keywords
Revenue Income from sales/services salary, payment, received, deposit
Inventory Stock/supplies purchases stock, inventory, supplier, wholesale
Rent Property/office rent rent, lease, property, landlord
Salaries Employee payments salary, wage, payroll, staff
Transport Fuel, taxi, delivery transport, fuel, taxi, uber
Utilities Electricity, water, internet electricity, water, internet, kplc
Other Uncategorized default fallback
Rule Format
json
{
"pattern": "fuel|petrol|diesel",
"category": "Transport",
"confidence": 0.85
}
🐳 Docker Deployment
Build & Run
bash

# Build image

docker build -t transaction-categorizer .

# Run container

docker run -d \
 --name categorizer \
 -p 8001:8001 \
 -e ENVIRONMENT=production \
 -e REDIS_URL=redis://host.docker.internal:6379 \
 transaction-categorizer
Docker Compose
yaml
version: '3.8'
services:
categorizer:
build: .
ports: - "8001:8001"
environment: - ENVIRONMENT=production - REDIS_URL=redis://redis:6379 - KAFKA_BOOTSTRAP_SERVERS=kafka:9092
depends_on: - redis - kafka
🔧 Configuration
Environment Variables
Variable Default Description
API_PORT 8001 Service port
ENVIRONMENT development development/production
REDIS_URL None Redis connection URL
KAFKA_BOOTSTRAP_SERVERS None Kafka brokers
DEFAULT_CATEGORY Other Fallback category
CONFIDENCE_THRESHOLD 0.7 Minimum confidence for auto-categorization
LOG_LEVEL INFO Logging level
CORS_ORIGINS ["http://localhost:3000"] Allowed origins
🧪 Testing
bash

# Run all tests

pytest

# Run with coverage

pytest --cov=src tests/

# Run specific test file

pytest tests/test_categorizer.py -v
🔗 Integration with Other Services
Upstream (Input)
mpesa-transaction-parser — sends raw transactions to Kafka raw-transactions topic

API Gateway — forwards manual categorization requests

Downstream (Output)
cashflow-analyzer — consumes categorized transactions for analytics

API Gateway — serves categorization results to dashboard

Webhook Service — triggers notifications on categorization

📈 Performance
Metric Value
Single transaction < 10ms
Batch (100 transactions) < 100ms
Rules evaluation O(n) where n = number of rules
Concurrent requests Scales with Uvicorn workers
🤝 Contributing
Fork the repository

Create a feature branch (git checkout -b feature/amazing)

Commit your changes (git commit -m 'Add amazing feature')

Push to branch (git push origin feature/amazing)

Open a Pull Request

📝 License
MIT License — see LICENSE for details.

👨‍💻 Author
Wambugu Mucheru

GitHub: @Black-opps

LinkedIn: Jonathan Wambugu

Email: jonahmucheru@gmail.com

🙏 Acknowledgments
Built as part of the M-PESA SaaS platform

Inspired by real-world fintech categorization needs

Powered by FastAPI and the Python ecosystem

⭐ Star this repository if you find it useful!
