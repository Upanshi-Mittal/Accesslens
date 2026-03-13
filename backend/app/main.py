from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exception_handlers import http_exception_handler
from contextlib import asynccontextmanager
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from prometheus_fastapi_instrumentator import Instrumentator
import logging
import time
from typing import Dict, Any, List

from .api.routes import router
from .core.browser_manager import browser_manager
from .core.report_storage import report_storage
from .middleware import RateLimitMiddleware, rate_limiter
from .engines.registry import EngineRegistry
from .engines.wcag_engine import WCAGEngine
from .engines.contrast_engine import ContrastEngine
from .engines.structural_engine import StructuralEngine
from .core.logging_config import setup_logging


setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan context manager.
    Handles startup and shutdown events.
    """

    logger.info("Starting AccessLens API...")

    # Initialize browser manager
    await browser_manager.initialize(headless=True)
    logger.info("Browser manager initialized")

    # Initialize rate limiter cleanup task
    await rate_limiter.start_cleanup_task()
    logger.info("Rate limiter initialized")

    # Initialize report storage
    await report_storage.initialize()
    app.state.report_storage = report_storage
    logger.info("Report storage initialized")

    # Initialize engine registry
    app.state.engine_registry = EngineRegistry()

    # Register engines
    wcag = WCAGEngine()
    contrast = ContrastEngine()
    structural = StructuralEngine()
    
    app.state.engine_registry.register(wcag)
    app.state.engine_registry.register(contrast)
    app.state.engine_registry.register(structural)
    
    # Register aliases to prevent "Engine not found" warnings
    app.state.engine_registry._engines["wcag"] = wcag
    app.state.engine_registry._engines["contrast"] = contrast
    app.state.engine_registry._engines["structural"] = structural

    logger.info(f"Registered {len(app.state.engine_registry.get_all())} engines (with aliases)")

    yield

    # Cleanup
    logger.info("Shutting down AccessLens API...")
    await browser_manager.close()
    await rate_limiter.shutdown()
    await report_storage.close()
    logger.info("Cleanup complete")


app = FastAPI(
    title="AccessLens API",
    description="Layered accessibility auditing framework",
    version="1.0.0",
    lifespan=lifespan
)

# Add rate limiting middleware FIRST (before CORS and other middleware)
app.add_middleware(RateLimitMiddleware)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Prometheus metrics
Instrumentator().instrument(app).expose(app)

# Security headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' cdn.jsdelivr.net; "
        "style-src 'self' 'unsafe-inline' cdn.jsdelivr.net; "
        "img-src 'self' data: fastapi.tiangolo.com; "
        "connect-src 'self' cdn.jsdelivr.net;"
    )
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    return response

# Include API routes
app.include_router(router, prefix="/api/v1")


@app.get("/")
async def root():
    """
    Root endpoint with API information.
    """
    return {
        "name": "AccessLens API",
        "version": app.version,
        "documentation": "/docs",
        "endpoints": {
            "health": "/health",
            "metrics": "/metrics",
            "api_v1": "/api/v1"
        }
    }


@app.get("/health")
async def health_check():
    """
    Health check endpoint for monitoring.
    """
    return {
        "status": "healthy",
        "version": app.version,
        "timestamp": time.time(),
        "engines": [
            {
                "name": engine.name,
                "version": engine.version,
                "capabilities": engine.capabilities
            }
            for engine in app.state.engine_registry.get_all()
        ]
    }


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    if isinstance(exc, HTTPException):
        return await http_exception_handler(request, exc)
    
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc) if app.debug else "An unexpected error occurred"
        }
    )