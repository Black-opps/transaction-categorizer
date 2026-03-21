"""
Main FastAPI application entry point.
"""

import logging
import socket
from datetime import datetime
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .api.routes import router
from .core.config import settings

# ────────────────────────────────────────────────
# Logging
# ────────────────────────────────────────────────
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper()),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

logger = logging.getLogger("app")

# ────────────────────────────────────────────────
# Lifespan
# ────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    logger.info(
        "Service starting",
        extra={
            "service": settings.APP_NAME,
            "env": settings.ENVIRONMENT,
        },
    )

    yield

    logger.info("Service shutting down")


# ────────────────────────────────────────────────
# App
# ────────────────────────────────────────────────
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    docs_url="/api/docs" if settings.ENVIRONMENT != "production" else None,
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(router)

# ────────────────────────────────────────────────
# Root
# ────────────────────────────────────────────────
@app.get("/")
def root():
    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat(),
        "instance": socket.gethostname(),
        "dependencies": {
            "redis": "configured" if settings.REDIS_URL else "not_configured",
            "kafka": "configured" if settings.KAFKA_BOOTSTRAP_SERVERS else "not_configured",
        },
        "docs": f"{settings.API_BASE_URL}api/docs"
        if settings.ENVIRONMENT != "production"
        else None,
    }


# ────────────────────────────────────────────────
# Health
# ────────────────────────────────────────────────
@app.get("/health")
def health():
    return {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat(),
    }


# ────────────────────────────────────────────────
# Debug Config
# ────────────────────────────────────────────────
@app.get("/debug/config")
def debug_config():
    return {
        "environment": settings.ENVIRONMENT,
        "debug": settings.DEBUG,
        "redis": bool(settings.REDIS_URL),
        "kafka": bool(settings.KAFKA_BOOTSTRAP_SERVERS),
    }


# ────────────────────────────────────────────────
# Global Exception Handler
# ────────────────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request, exc: Exception):
    logger.error("Unhandled exception", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )