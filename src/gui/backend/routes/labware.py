"""
Labware endpoints.
"""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import PlainTextResponse

from ..dependencies import get_state_store
from ..schemas import DocumentPayload, PatchPayload
from ..state import FileStateStore

router = APIRouter(prefix="/labware", tags=["labware"])


@router.get("")
def read_labware(store: FileStateStore = Depends(get_state_store)) -> dict[str, object]:
    return store.get_labware()


@router.get("/raw", response_class=PlainTextResponse)
def read_labware_raw(store: FileStateStore = Depends(get_state_store)) -> str:
    return store.labware_path.read_text(encoding="utf-8")


@router.put("")
def replace_labware(payload: DocumentPayload, store: FileStateStore = Depends(get_state_store)) -> dict[str, object]:
    return store.write_labware(payload.data)


@router.patch("")
def patch_labware(payload: PatchPayload, store: FileStateStore = Depends(get_state_store)) -> dict[str, object]:
    return store.patch_labware(payload.path, payload.value)


@router.post("/reset")
def reset_labware(store: FileStateStore = Depends(get_state_store)) -> dict[str, object]:
    return store.reset_labware()


# --- Available labware scan ---

@router.get("/available")
def get_available_labware(store: FileStateStore = Depends(get_state_store)) -> list[dict]:
    return store.scan_available_labware()


# --- Offset database ---

@router.get("/offsets")
def get_offsets(store: FileStateStore = Depends(get_state_store)) -> dict[str, object]:
    return store.get_offset_database()


@router.post("/offsets")
def save_offset(payload: Dict[str, Any], store: FileStateStore = Depends(get_state_store)) -> dict[str, object]:
    labware_id = payload.get("labware_id", "")
    position_rack = str(payload.get("position_rack", ""))
    if not labware_id or not position_rack:
        raise HTTPException(status_code=400, detail="labware_id and position_rack are required")
    return store.update_offset_entry(
        labware_id=labware_id,
        position_rack=position_rack,
        offset_x=float(payload.get("offset_x", 0.0)),
        offset_y=float(payload.get("offset_y", 0.0)),
        offset_z=float(payload.get("offset_z", 0.0)),
        notes=str(payload.get("notes", "")),
    )


# --- Pipette entry CRUD ---

@router.post("/pipettes")
def add_pipette_entry(payload: Dict[str, Any], store: FileStateStore = Depends(get_state_store)) -> dict[str, object]:
    return store.add_pipette_entry(payload)


@router.put("/pipettes/{index}")
def update_pipette_entry(index: int, payload: Dict[str, Any], store: FileStateStore = Depends(get_state_store)) -> dict[str, object]:
    try:
        return store.update_pipette_entry(index, payload)
    except IndexError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/pipettes/{index}")
def delete_pipette_entry(index: int, store: FileStateStore = Depends(get_state_store)) -> dict[str, object]:
    try:
        return store.remove_pipette_entry(index)
    except IndexError as e:
        raise HTTPException(status_code=404, detail=str(e))
