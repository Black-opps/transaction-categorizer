# Transaction Categorizer Service

Event-driven microservice that consumes parsed M-PESA transactions from Kafka,  
categorizes them using rule-based logic, and publishes categorized results.

Part of a larger multi-tenant SaaS payment & billing platform.

## Features

- Rule-based transaction categorization (keyword/pattern matching)
- Confidence scoring & rule tracking
- Single transaction endpoint (real-time / manual)
- Batch categorization endpoint
- Manage categorization rules (list / add / remove)
- Health check & OpenAPI documentation (Swagger)
- Ready for Kafka consumer (placeholder implemented)
- Pydantic v2 models, FastAPI, async-ready structure

## Tech Stack

- Python 3.12
- FastAPI
- Pydantic v2 + pydantic-settings
- Uvicorn (ASGI server)
- Kafka (planned consumer)
- Redis (optional cache)
- Port: **8001**

## Quick Start

```bash
# 1. Clone & enter directory
git clone https://github.com/Black-opps/transaction-categorizer.git
cd transaction-categorizer

# 2. Create virtual environment
python -m venv venv
.\venv\Scripts\activate    # Windows
# source venv/bin/activate  # Linux/macOS

# 3. Install dependencies
pip install -r requirements.txt

# 4. (Optional) Create .env file
cp .env.example .env
# edit .env if needed (KAFKA_BOOTSTRAP_SERVERS, etc.)

# 5. Run the service
uvicorn src.main:app --reload --port 8001
```
