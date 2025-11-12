"""
CSV workspace management endpoints.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Path
from fastapi.responses import PlainTextResponse

from ..dependencies import get_state_store
from ..schemas import CSVListResponse, CSVUploadPayload
from ..state import FileStateStore

router = APIRouter(prefix="/csvs", tags=["csvs"])


@router.get("", response_model=CSVListResponse)
def list_csvs(store: FileStateStore = Depends(get_state_store)) -> CSVListResponse:
    return CSVListResponse(files=store.list_csv_files())


@router.post("", status_code=201)
def upload_csv(payload: CSVUploadPayload, store: FileStateStore = Depends(get_state_store)) -> dict[str, str]:
    name = store.save_csv(payload.name, payload.content)
    return {"name": name}


@router.get("/{name}", response_class=PlainTextResponse)
def fetch_csv(
    name: str = Path(..., description="CSV filename"),
    store: FileStateStore = Depends(get_state_store),
) -> str:
    return store.load_csv(name)


@router.delete("/{name}", status_code=204)
def delete_csv(
    name: str = Path(..., description="CSV filename"),
    store: FileStateStore = Depends(get_state_store),
) -> None:
    store.delete_csv(name)


@router.get("/{name}/path")
def resolve_csv(
    name: str = Path(..., description="CSV filename or relative path"),
    store: FileStateStore = Depends(get_state_store),
) -> dict[str, str]:
    try:
        resolved = store.resolve_csv_path(name)
    except HTTPException:
        raise
    return {"path": str(resolved)}
