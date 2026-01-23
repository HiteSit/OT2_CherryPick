"""
Labware endpoints mirroring the settings functionality.
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


# --- Labware entry CRUD ---

@router.post("/entries")
def add_labware_entry(payload: Dict[str, Any], store: FileStateStore = Depends(get_state_store)) -> dict[str, object]:
    return store.add_labware_entry(payload)


@router.put("/entries/{index}")
def update_labware_entry(index: int, payload: Dict[str, Any], store: FileStateStore = Depends(get_state_store)) -> dict[str, object]:
    try:
        return store.update_labware_entry(index, payload)
    except IndexError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/entries/{index}")
def delete_labware_entry(index: int, store: FileStateStore = Depends(get_state_store)) -> dict[str, object]:
    try:
        return store.remove_labware_entry(index)
    except IndexError as e:
        raise HTTPException(status_code=404, detail=str(e))


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
