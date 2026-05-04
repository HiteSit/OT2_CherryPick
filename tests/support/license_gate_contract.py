"""Contract helpers for license-gated protocol generation tests."""

from __future__ import annotations

import csv
import importlib
import io
import json
import re
from collections import defaultdict
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

from tests.support.workspace import E2EWorkspace


EXPECTED_LICENSE_MODULE = "ot2_cherrypick_mcp.core.license_gate"
EXPECTED_CLIENT_ATTR = "_post_license_decision"
EXPECTED_CHECK_ATTR = "check_generation_license"
EXPECTED_IDENTITY_ATTR = "resolve_machine_identity"


def import_expected_license_gate() -> ModuleType:
    """Import the planned license-gate module or xfail with a clear source TODO."""
    try:
        return importlib.import_module(EXPECTED_LICENSE_MODULE)
    except ModuleNotFoundError as exc:
        if exc.name == EXPECTED_LICENSE_MODULE:
            pytest.xfail(
                f"TODO(source): implement {EXPECTED_LICENSE_MODULE} "
                "or update tests/support/license_gate_contract.py with the final module path"
            )
        raise


def require_license_attr(module: ModuleType, attr_name: str) -> Any:
    """Return an expected production attribute or xfail with an adjustment TODO."""
    if not hasattr(module, attr_name):
        pytest.xfail(
            f"TODO(source): expose {module.__name__}.{attr_name} "
            "or update tests/support/license_gate_contract.py with the final API name"
        )
    return getattr(module, attr_name)


def _decision_payload(*, allowed: bool, mode: str | None, reason: str | None) -> dict[str, Any]:
    if reason is None:
        reason = "allowed" if allowed else "denied"
    return {
        "allowed": allowed,
        "mode": mode,
        "reason": reason,
    }


def patch_license_client(
    monkeypatch: pytest.MonkeyPatch,
    *,
    allowed: bool,
    mode: str | None,
    reason: str | None = None,
) -> ModuleType:
    """Patch the internal license client for tests that exercise gate policy."""
    module = import_expected_license_gate()
    require_license_attr(module, EXPECTED_CLIENT_ATTR)

    def fake_request(payload: dict[str, str]) -> dict[str, Any]:
        assert payload["machine_id"]
        return _decision_payload(allowed=allowed, mode=mode, reason=reason)

    monkeypatch.setattr(module, EXPECTED_CLIENT_ATTR, fake_request)
    return module


def maybe_patch_license_client(
    monkeypatch: pytest.MonkeyPatch,
    *,
    allowed: bool,
    mode: str | None,
    reason: str | None = None,
) -> None:
    """Patch the license client when it exists; remain a no-op before source wiring."""
    try:
        module = importlib.import_module(EXPECTED_LICENSE_MODULE)
    except ModuleNotFoundError:
        return
    if not hasattr(module, EXPECTED_CLIENT_ATTR):
        return

    def fake_request(payload: dict[str, str]) -> dict[str, Any]:
        assert payload["machine_id"]
        return _decision_payload(allowed=allowed, mode=mode, reason=reason)

    monkeypatch.setattr(module, EXPECTED_CLIENT_ATTR, fake_request)


class _ProtocolLicenseDecision:
    def __init__(self, mode: str) -> None:
        self.allowed = True
        self.mode = mode
        self.reason = "allowed"


def patch_protocol_generation_mode(monkeypatch: pytest.MonkeyPatch, *, mode: str) -> None:
    """Patch the generator's imported license check after the autouse fixture."""
    protocol_generator = importlib.import_module("ot2_cherrypick_mcp.core.protocol_generator")
    if not hasattr(protocol_generator, "check_generation_license"):
        pytest.xfail(
            "TODO(source): wire protocol_generator.check_generation_license "
            "before asserting license-mode E2E behavior"
        )
    monkeypatch.setattr(
        protocol_generator,
        "check_generation_license",
        lambda: _ProtocolLicenseDecision(mode),
    )


def patch_protocol_generation_denial(monkeypatch: pytest.MonkeyPatch, *, reason: str) -> None:
    """Patch the generator's imported license check to fail before file update."""
    license_gate = import_expected_license_gate()
    error_type = require_license_attr(license_gate, "LicenseGateError")
    protocol_generator = importlib.import_module("ot2_cherrypick_mcp.core.protocol_generator")

    def deny() -> None:
        raise error_type(f"License denied: {reason}")

    monkeypatch.setattr(protocol_generator, "check_generation_license", deny)


def generate_protocol_in_process(workspace: E2EWorkspace, csv_path: Path) -> dict[str, Any]:
    """Run the real core generator in-process so monkeypatches affect internals."""
    protocol_generator = importlib.import_module("ot2_cherrypick_mcp.core.protocol_generator")
    return protocol_generator.generate_protocol(
        str(workspace.labware_dict_path),
        str(workspace.settings_path),
        str(csv_path),
        str(workspace.protocol_path),
        verbose=False,
    )


def normalize_embedded_csv_text(text: str) -> str:
    return text.replace("\\n", "\n").replace("\r\n", "\n").replace("\r", "\n").strip()


def read_input_csv_text(csv_path: Path) -> str:
    return normalize_embedded_csv_text(csv_path.read_text(encoding="utf-8"))


def extract_embedded_json(protocol_path: Path) -> dict[str, Any]:
    content = protocol_path.read_text(encoding="utf-8")
    match = re.search(r'_all_values = json\.loads\("""(?P<payload>.*?)"""\)', content, flags=re.DOTALL)
    if not match:
        raise AssertionError(f"Unable to find embedded json.loads payload in {protocol_path}")
    return json.loads(match.group("payload"))


def embedded_csv_text(protocol_path: Path) -> str:
    payload = extract_embedded_json(protocol_path)
    assert set(payload) == {"labware_dict", "settings", "csv_data"}
    return normalize_embedded_csv_text(payload["csv_data"])


def _csv_rows(text: str) -> tuple[list[str], list[dict[str, str]]]:
    reader = csv.DictReader(io.StringIO(normalize_embedded_csv_text(text)))
    if reader.fieldnames is None:
        raise AssertionError("CSV text is missing a header row")
    return list(reader.fieldnames), list(reader)


def _group_multiset(rows: list[dict[str, str]], group_key: str, value_key: str) -> dict[str, list[str]]:
    grouped: dict[str, list[str]] = defaultdict(list)
    for row in rows:
        grouped[row[group_key]].append(row[value_key])
    return {key: sorted(values) for key, values in grouped.items()}


def assert_allowed_clown_mutation(original_text: str, mutated_text: str) -> None:
    """Assert the clown CSV mutation is narrow and deterministic-friendly."""
    original_header, original_rows = _csv_rows(original_text)
    mutated_header, mutated_rows = _csv_rows(mutated_text)

    assert mutated_header == original_header
    assert len(mutated_rows) == len(original_rows)
    assert normalize_embedded_csv_text(mutated_text) != normalize_embedded_csv_text(original_text)

    stable_columns = [
        column
        for column in original_header
        if column not in {"Source Well", "Dest Well"}
    ]
    assert sorted(tuple(row[column] for column in stable_columns) for row in mutated_rows) == sorted(
        tuple(row[column] for column in stable_columns) for row in original_rows
    )

    assert _group_multiset(mutated_rows, "Source Labware", "Source Well") == _group_multiset(
        original_rows, "Source Labware", "Source Well"
    )
    assert _group_multiset(mutated_rows, "Dest Labware", "Dest Well") == _group_multiset(
        original_rows, "Dest Labware", "Dest Well"
    )
