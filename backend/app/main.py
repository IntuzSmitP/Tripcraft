"""
TripCraft — FastAPI application entry point.

Configures CORS, includes routes, and sets up structured logging.
"""

from __future__ import annotations

import logging
import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routes.planning import router as planning_router


# ── Logging ─────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s │ %(levelname)-8s │ %(name)s │ %(message)s",
    datefmt="%H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)],
)

# Quieten noisy libraries
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("google").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

# ── App ─────────────────────────────────────────────────────────

app = FastAPI(
    title="TripCraft",
    description=(
        "Multi-step AI travel planning agent powered by Gemini. "
        "Accepts a natural-language travel goal and autonomously "
        "decomposes it into tasks, selects tools, maintains state, "
        "detects invalid assumptions, and produces a structured plan."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS ────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Single-user demo — allow all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routes ──────────────────────────────────────────────────────

app.include_router(planning_router)


# ── Health check ────────────────────────────────────────────────


@app.get("/health", tags=["System"])
async def health_check() -> dict:
    """Simple health check endpoint."""
    return {
        "status": "healthy",
        "service": "TripCraft",
        "model": settings.gemini_model,
    }


@app.on_event("startup")
async def on_startup() -> None:
    logger.info("🚀 TripCraft API started — model=%s", settings.gemini_model)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=True,
    )