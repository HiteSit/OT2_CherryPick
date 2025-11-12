"""
System/health endpoints.
"""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(tags=["system"])


@router.get("/health")
def healthcheck() -> dict[str, str]:
    """Basic health probe."""

    return {"status": "ok"}
