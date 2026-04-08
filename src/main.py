"""
Transaction Categorizer Microservice - Main entry point.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import logging

from .core.config import settings
from .core.database import init_db
from .api.routes import router
from .consumers.kafka_consumer import consumer

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize database
init_db()
logger.info("Database initialized")

# Create FastAPI app
app = FastAPI(
    title="Transaction Categorizer Service",
    description="ML-powered transaction categorization for M-PESA transactions",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(router)


@app.on_event("startup")
async def startup_event():
    """Start Kafka consumer on app startup."""
    logger.info("Starting Transaction Categorizer Service...")
    asyncio.create_task(consumer.start())
    logger.info("Kafka consumer started")


@app.on_event("shutdown")
async def shutdown_event():
    """Stop Kafka consumer on app shutdown."""
    logger.info("Shutting down...")
    await consumer.stop()


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "Transaction Categorizer Service",
        "version": "1.0.0",
        "status": "operational",
        "environment": settings.ENVIRONMENT,
        "docs": "/docs",
        "health": "/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.API_PORT,
        reload=settings.DEBUG
    )