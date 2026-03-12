"""FastAPI application — entry point for the Animal Welfare Sentiment Tracker."""

import logging
import os
import threading
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ingestion.scheduler import create_scheduler, run_ingestion_pipeline

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

# ── Module-level scheduler reference for shutdown ────────────────────
_scheduler = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown logic."""
    global _scheduler

    # ── Startup ──────────────────────────────────────────────────
    # Tables are managed via Supabase Dashboard / SQL Editor
    logger.info("Using Supabase — tables managed externally")

    # Skip scheduler + pipeline when running tests
    if not os.environ.get("SKIP_PIPELINE"):
        logger.info("Starting scheduler")
        _scheduler = create_scheduler()
        _scheduler.start()

        # Run pipeline in a daemon thread so the server starts serving
        # requests immediately instead of blocking until NLP finishes.
        logger.info("Queuing initial pipeline (background thread)")
        threading.Thread(
            target=run_ingestion_pipeline, daemon=True, name="initial-pipeline"
        ).start()
    else:
        logger.info("SKIP_PIPELINE set — skipping scheduler and initial pipeline")

    yield

    # ── Shutdown ─────────────────────────────────────────────────
    if _scheduler:
        _scheduler.shutdown()
        logger.info("Scheduler stopped")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="Animal Welfare Sentiment Tracker",
        version="0.1.0",
        lifespan=lifespan,
    )

    # ── CORS ─────────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ],
        allow_methods=["GET"],
        allow_headers=["*"],
    )

    # ── Routers (Module 7 — will be added when those files exist) ──
    try:
        from api.routes.metrics import router as metrics_router
        app.include_router(metrics_router, prefix="/overview", tags=["overview"])
    except ImportError:
        logger.debug("metrics router not yet available")

    try:
        from api.routes.sentiment import router as sentiment_router
        app.include_router(sentiment_router, prefix="/sentiment", tags=["sentiment"])
    except ImportError:
        logger.debug("sentiment router not yet available")

    try:
        from api.routes.topics import router as topics_router
        app.include_router(topics_router, prefix="/topics", tags=["topics"])
    except ImportError:
        logger.debug("topics router not yet available")

    try:
        from api.routes.narrative import router as narrative_router
        app.include_router(narrative_router, prefix="/narrative", tags=["narrative"])
    except ImportError:
        logger.debug("narrative router not yet available")

    try:
        from api.routes.articles import router as articles_router
        app.include_router(articles_router, prefix="/articles", tags=["articles"])
    except ImportError:
        logger.debug("articles router not yet available")

    try:
        from api.routes.keywords import router as keywords_router
        app.include_router(keywords_router, prefix="/trending", tags=["trending"])
    except ImportError:
        logger.debug("keywords router not yet available")

    try:
        from api.routes.entities import router as entities_router
        app.include_router(entities_router, prefix="/entities", tags=["entities"])
    except ImportError:
        logger.debug("entities router not yet available")

    try:
        from api.routes.spikes import router as spikes_router
        app.include_router(spikes_router, prefix="/spikes", tags=["spikes"])
    except ImportError:
        logger.debug("spikes router not yet available")

    try:
        from api.routes.sources import router as sources_router
        app.include_router(sources_router, prefix="/sources", tags=["sources"])
    except ImportError:
        logger.debug("sources router not yet available")

    # ── Health check ─────────────────────────────────────────────
    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app


app = create_app()
