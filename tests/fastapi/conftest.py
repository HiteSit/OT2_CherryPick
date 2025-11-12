import os
import shutil
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from gui.backend.dependencies import get_state_store
from gui.backend.main import create_app
from gui.backend.state import FileStateStore
from ot2_cherrypick_mcp.utils.paths import get_repo_root


@pytest.fixture()
def state_store(monkeypatch):
    """
    Provide a fresh FileStateStore for each test by pointing the backend to a unique workspace.
    """

    workspace_name = f"test_gui_state_{uuid4().hex}"
    monkeypatch.setenv("OT2_GUI_WORKSPACE", workspace_name)

    # Ensure the cached singleton is cleared so the next access honors the env var.
    get_state_store.cache_clear()
    store = FileStateStore()

    # Copy the known-good CSV into the workspace for workflow tests.
    repo_root = get_repo_root()
    example_csv = repo_root / "CSVs" / "example_basic.csv"
    shutil.copy2(example_csv, store.csv_dir / "example_basic.csv")

    yield store

    # Cleanup
    get_state_store.cache_clear()
    if store.workspace_dir.exists():
        shutil.rmtree(store.workspace_dir, ignore_errors=True)


@pytest.fixture()
def client(state_store):
    """
    FastAPI test client wired to the isolated state store.
    """

    app = create_app()
    app.dependency_overrides[get_state_store] = lambda: state_store

    with TestClient(app) as test_client:
        yield test_client
