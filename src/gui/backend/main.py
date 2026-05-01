"""
FastAPI application entry point for the OT-2 CherryPick GUI backend.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from importlib.metadata import version as pkg_version

from ot2_cherrypick_mcp.utils.paths import require_unlock_key

from .dependencies import get_state_store
from .routes import csvs, labware, settings, system, workflow


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.

    The app exposes configuration-state management endpoints along with
    workflow helpers that wrap the existing protocol generation utilities.
    """
    require_unlock_key()

    app = FastAPI(
        title="OT-2 CherryPick GUI Backend",
        description="REST API for editing configuration state and running workflows.",
        version=pkg_version("OT2_CherryPick"),
    )

    # Basic CORS policy for local GUI prototyping; tighten for production deployments.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Touch the singleton state store early so the workspace is prepared up front.
    get_state_store()

    # Register routers.
    app.include_router(system.router)
    app.include_router(settings.router)
    app.include_router(labware.router)
    app.include_router(csvs.router)
    app.include_router(workflow.router)

    return app


app = create_app()
