"""
Workflow orchestration endpoints.
"""

from __future__ import annotations

import os

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
    logs: list[str] = []
    deployment = None

    if payload.use_shell_runner:
        script_result, script_logs = store.run_shell_script(csv_path, payload.send_to_opentrons)
        logs.extend(script_logs)
        generated = {
            "protocol_file": str(store.protocol_output),
            "json_size": os.path.getsize(store.protocol_output) if store.protocol_output.exists() else 0,
            "message": "simulate_protocol.sh executed",
        }
        simulation = script_result
    else:
        generated, gen_log = store.run_generate_protocol(csv_path, payload.protocol_path)
        logs.extend(gen_log)
        simulation = None
        if payload.run_simulation:
            simulation, sim_log = store.run_simulation(payload.protocol_path)
            logs.extend(sim_log)

    if payload.send_to_opentrons and payload.target_path and not payload.use_shell_runner:
        deployment, dep_log = store.deploy_protocol(
            payload.protocol_path,
            target_path=payload.target_path,
            copy_to_clipboard=payload.copy_to_clipboard,
        )
        logs.extend(dep_log)
    elif payload.send_to_opentrons and payload.target_path and payload.use_shell_runner:
        deployment, dep_log = store.deploy_protocol(
            payload.protocol_path,
            target_path=payload.target_path,
            copy_to_clipboard=payload.copy_to_clipboard,
        )
        logs.extend(dep_log)

    return ProtocolGenerationResponse(generated=generated, simulation=simulation, deployment=deployment, logs=logs)
