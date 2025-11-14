"""
System endpoints: health plus editor-specific helpers.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from ..dependencies import get_state_store
from ..schemas import ShellSettings, ShellSettingsBrowseRequest, ShellSettingsUpdate
from ..state import FileStateStore

router = APIRouter(tags=["system"])


@router.get("/health")
def healthcheck() -> dict[str, str]:
    """Basic health probe."""

    return {"status": "ok"}


@router.get("/shell-settings", response_model=ShellSettings)
def read_shell_settings(store: FileStateStore = Depends(get_state_store)) -> ShellSettings:
    """Return the Windows-specific configuration used by the shell runner."""

    return ShellSettings(**store.get_shell_settings())


@router.put("/shell-settings", response_model=ShellSettings)
def update_shell_settings_endpoint(
    payload: ShellSettingsUpdate,
    store: FileStateStore = Depends(get_state_store),
) -> ShellSettings:
    """Persist new shell runner settings (labware and deployment directories)."""

    return ShellSettings(
        **store.update_shell_settings(
            target_protocol_src_win=payload.target_protocol_src_win,
            labware_path_win=payload.labware_path_win,
        )
    )


@router.post("/shell-settings/browse", response_model=ShellSettings)
def browse_shell_settings(
    payload: ShellSettingsBrowseRequest,
    store: FileStateStore = Depends(get_state_store),
) -> ShellSettings:
    """Open a native folder picker for the requested shell setting field."""

    return ShellSettings(**store.browse_and_update_shell_settings(payload.field))
