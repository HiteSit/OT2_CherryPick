"""
Workflow orchestration endpoints.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from ..dependencies import get_state_store
from ..schemas import ProtocolGenerationRequest, ProtocolGenerationResponse
from ..state import FileStateStore

router = APIRouter(prefix="/workflow", tags=["workflow"])


@router.post("/generate", response_model=ProtocolGenerationResponse)
def generate_protocol_endpoint(
    payload: ProtocolGenerationRequest,
    store: FileStateStore = Depends(get_state_store),
) -> ProtocolGenerationResponse:
    csv_path = store.resolve_csv_path(payload.csv)
    generated = store.run_generate_protocol(csv_path, payload.protocol_path)
    simulation = store.run_simulation(payload.protocol_path) if payload.run_simulation else None
    deployment = (
        store.deploy_protocol(
            payload.protocol_path,
            target_path=payload.target_path,
            copy_to_clipboard=payload.copy_to_clipboard,
        )
        if payload.send_to_opentrons
        else None
    )
    return ProtocolGenerationResponse(generated=generated, simulation=simulation, deployment=deployment)
