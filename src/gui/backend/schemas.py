"""
Pydantic schemas for the GUI backend.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator, model_validator


class DocumentPayload(BaseModel):
    """
    Container for replacing an entire TOML document via JSON.
    """

    data: Dict[str, Any]


class PatchPayload(BaseModel):
    """
    Payload for patch operations on TOML documents.
    """

    path: str = Field(..., description="Dot/bracket path (e.g., settings.general.tip_reuse or foo.bar[0].value)")
    value: Any


class CSVUploadPayload(BaseModel):
    """
    Payload for creating/updating CSV transfer maps inside the workspace.
    """
    name: str = Field(..., description="Filename ending with .csv")
    content: str = Field(..., description="Raw CSV content")

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:  # noqa: D417
        if "/" in value or "\\" in value:
            raise ValueError("CSV name must not contain directory separators")
        return value


class WorkingPlateEntryPayload(BaseModel):
    type: str = Field(..., description="Type of entry (source/destination/reservoir/tip/module)")
    labware_id: Optional[str] = Field(None, description="Labware identifier")
    position_rack: Optional[str] = Field(None, description="Deck slot")
    connection: Optional[str] = Field(None, description="Pipette connection or module link")


class WorkingPlateMovePayload(BaseModel):
    target_index: int = Field(..., ge=0, description="Destination index for the working plate entry")


class ProtocolGenerationRequest(BaseModel):
    """
    Request body for running protocol generation (and optionally simulation).
    """

    csv: str = Field(..., description="CSV filename in workspace or relative path")
    protocol_path: Optional[str] = Field(
        None, description="Optional override for protocol output path; defaults to CherryPick_OT2.py"
    )
    run_simulation: bool = Field(
        False, description="If true, run opentrons_simulate after generating the protocol"
    )
    use_shell_runner: bool = Field(
        False,
        description="If true, execute simulate_protocol.sh (takes precedence over built-in simulation)",
    )
    send_to_opentrons: bool = Field(
        False,
        description="If true, deploy the protocol to the provided target path after generation.",
    )
    target_path: Optional[str] = Field(
        None,
        description="Filesystem path for deployment when send_to_opentrons is true.",
    )
    copy_to_clipboard: bool = Field(
        False,
        description="Copy generated protocol to clipboard via deployment helper.",
    )

    @model_validator(mode="after")
    def _validate_target(cls, values: "ProtocolGenerationRequest") -> "ProtocolGenerationRequest":  # noqa: D417
        if values.send_to_opentrons and not values.target_path and not values.use_shell_runner:
            raise ValueError("target_path is required when send_to_opentrons is true.")
        return values


class ProtocolGenerationResponse(BaseModel):
    """
    Response payload summarizing generation (and optional simulation) results.
    """

    generated: Dict[str, Any]
    simulation: Optional[Dict[str, Any]] = None
    deployment: Optional[Dict[str, Any]] = None
    logs: List[str] = Field(default_factory=list)


class CSVListResponse(BaseModel):
    files: List[str]


__all__ = [
    "CSVListResponse",
    "CSVUploadPayload",
    "DocumentPayload",
    "PatchPayload",
    "WorkingPlateEntryPayload",
    "WorkingPlateMovePayload",
    "ProtocolGenerationRequest",
    "ProtocolGenerationResponse",
]
