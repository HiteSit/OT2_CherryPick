"""
Settings endpoints.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Path
from fastapi.responses import PlainTextResponse

from ..dependencies import get_state_store
from ..schemas import DocumentPayload, PatchPayload, WorkingPlateEntryPayload, WorkingPlateMovePayload
from ..state import FileStateStore

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("")
def read_settings(store: FileStateStore = Depends(get_state_store)) -> dict[str, object]:
    """Return the current settings TOML as a JSON-friendly dict."""

    return store.get_settings()


@router.get("/raw", response_class=PlainTextResponse)
def read_settings_raw(store: FileStateStore = Depends(get_state_store)) -> str:
    """Return the raw TOML string (preserving formatting)."""

    return store.settings_path.read_text(encoding="utf-8")


@router.put("")
def replace_settings(payload: DocumentPayload, store: FileStateStore = Depends(get_state_store)) -> dict[str, object]:
    """Replace the settings file entirely with the provided document."""

    if "settings" not in payload.data:
        raise HTTPException(status_code=400, detail="Root 'settings' key missing in payload.")
    return store.write_settings(payload.data)


@router.patch("")
def patch_settings(payload: PatchPayload, store: FileStateStore = Depends(get_state_store)) -> dict[str, object]:
    """Apply a precise change via dotted path (e.g., settings.general.tip_reuse)."""

    return store.patch_settings(payload.path, payload.value)


@router.post("/reset")
def reset_settings(store: FileStateStore = Depends(get_state_store)) -> dict[str, object]:
    """Restore the settings file from repository defaults."""

    return store.reset_settings()


@router.post("/working-plate")
def add_working_plate_entry(
    payload: WorkingPlateEntryPayload,
    store: FileStateStore = Depends(get_state_store),
) -> dict[str, object]:
    """Append a new working plate entry."""

    return store.add_working_plate_entry(payload.model_dump(exclude_none=True))


@router.delete("/working-plate/{index}")
def remove_working_plate_entry(
    index: int = Path(..., ge=0),
    store: FileStateStore = Depends(get_state_store),
) -> dict[str, object]:
    """Remove a working plate entry by index."""

    return store.remove_working_plate_entry(index)


@router.post("/working-plate/{index}/move")
def move_working_plate_entry(
    payload: WorkingPlateMovePayload,
    index: int = Path(..., ge=0),
    store: FileStateStore = Depends(get_state_store),
) -> dict[str, object]:
    """Reorder working plate entries."""

    return store.move_working_plate_entry(index, payload.target_index)
