"""
Quantum Estate X — FastAPI Application Entry Point.

Configures CORS, registers all API routers, and exposes the health
check endpoint.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.core.config import settings
from backend.app.api.routes_land import router as land_router
from backend.app.api.routes_quantum import router as quantum_router
from backend.app.api.routes_workflow import router as workflow_router
from backend.app.api.routes_geospatial import router as geospatial_router
from backend.app.api.routes_map import router as map_router
from backend.app.api.routes_optimization import router as optimization_router

# ═══════════════════════════════════════════════════════════════════════
# APPLICATION FACTORY
# ═══════════════════════════════════════════════════════════════════════

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=settings.APP_DESCRIPTION,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS Middleware ───────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Register Routers ─────────────────────────────────────────────────
app.include_router(land_router)
app.include_router(quantum_router)
app.include_router(workflow_router)
app.include_router(geospatial_router)
app.include_router(map_router)
app.include_router(optimization_router)


# ═══════════════════════════════════════════════════════════════════════
# HEALTH CHECK
# ═══════════════════════════════════════════════════════════════════════


@app.get("/", tags=["Health"])
async def health_check() -> dict:
    """
    Root health-check endpoint.

    Returns application metadata and operational status.
    """
    return {
        "status": "operational",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "description": settings.APP_DESCRIPTION,
        "endpoints": {
            "docs": "/docs",
            "parcels": "/api/parcels",
            "infrastructure": "/api/parcels/infrastructure",
            "optimize": "/api/quantum/optimize",
            "benchmark": "/api/quantum/benchmark/{budget_crore}",
            "workflow": "/api/workflow/pune-development",
        },
    }
