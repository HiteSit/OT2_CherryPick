"""
Labware endpoints mirroring the settings functionality.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
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
