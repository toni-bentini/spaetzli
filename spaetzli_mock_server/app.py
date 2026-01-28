"""FastAPI application for the mock premium server."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import config
from .routes import api_router, nest_router

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if config.debug else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    logger.info("🍝 Spaetzli Mock Premium Server starting...")
    logger.info(f"   Listening on {config.host}:{config.port}")
    logger.info(f"   Signature validation: {'enabled' if config.validate_signatures else 'disabled'}")
    logger.info(f"   Data directory: {config.data_dir.absolute()}")
    yield
    logger.info("🍝 Spaetzli Mock Premium Server shutting down...")


app = FastAPI(
    title="Spaetzli - Rotki Premium Mock Server",
    description="Mock server for Rotki premium features",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware - allow all origins for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include routers
app.include_router(api_router)
app.include_router(nest_router)


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "ok",
        "service": "spaetzli-mock-premium",
        "version": "0.1.0",
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


# Error handlers
@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """Handle uncaught exceptions."""
    logger.exception(f"Unhandled error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": str(exc)},
    )
