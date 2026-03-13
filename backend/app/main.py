
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import time
from typing import Dict, Any, List

from .api.routes import router
from .core.browser_manager import browser_manager
from .engines.registry import EngineRegistry
from .engines.wcag_engine import WCAGEngine
from .engines.contrast_engine import ContrastEngine
from .engines.structural_engine import StructuralEngine
from .core.logging_config import setup_logging


setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):


    logger.info("Starting AccessLens API...")


    await browser_manager.initialize(headless=True)
    logger.info("Browser manager initialized")


    app.state.engine_registry = EngineRegistry()


    app.state.engine_registry.register(WCAGEngine())
    app.state.engine_registry.register(ContrastEngine())
    app.state.engine_registry.register(StructuralEngine())

    logger.info(f"Registered {len(app.state.engine_registry.get_all())} engines")

    yield


    logger.info("Shutting down AccessLens API...")
    await browser_manager.close()
    logger.info("Cleanup complete")


app = FastAPI(
    title="AccessLens API",
    description="Layered accessibility auditing framework",
    version="1.0.0",
    lifespan=lifespan
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(router, prefix="/api/v1")


@app.get("/")
async def root():

    return {
        "name": "AccessLens API",
        "documentation": "/docs",
        "endpoints": {
            "health": "/health",
            "api_v1": "/api/v1"
        }
    }


@app.get("/health")
async def health_check():

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
async def global_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc) if app.debug else "An unexpected error occurred"
        }
    )