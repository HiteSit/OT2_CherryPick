from __future__ import annotations

import json
import io
import urllib.error
from pathlib import Path

import pytest

clown_mode = pytest.importorskip(
    "ot2_cherrypick_mcp.core.clown_mode",
    reason="TODO(source): implement ot2_cherrypick_mcp.core.clown_mode",
)
license_gate = pytest.importorskip(
    "ot2_cherrypick_mcp.core.license_gate",
    reason="TODO(source): implement ot2_cherrypick_mcp.core.license_gate",
)
protocol_generator = pytest.importorskip("ot2_cherrypick_mcp.core.protocol_generator")

CLOWN_SHUFFLE_SEED = clown_mode.CLOWN_SHUFFLE_SEED
ClownModeError = clown_mode.ClownModeError
apply_clown_mode_csv_transform = clown_mode.apply_clown_mode_csv_transform
LicenseGateError = license_gate.LicenseGateError
check_generation_license = license_gate.check_generation_license
resolve_machine_identity = license_gate.resolve_machine_identity
create_json_config = protocol_generator.create_json_config
generate_protocol = protocol_generator.generate_protocol


def test_resolve_machine_identity_reads_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("COMPUTER_ID", "Ric-WorkStation")

    assert resolve_machine_identity() == "Ric-WorkStation"


def test_resolve_machine_identity_requires_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("COMPUTER_ID", raising=False)

    with pytest.raises(LicenseGateError, match="COMPUTER_ID"):
        resolve_machine_identity()


def test_check_generation_license_denies_server_rejection(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("COMPUTER_ID", "Ric-WorkStation")
    monkeypatch.setattr(
        "ot2_cherrypick_mcp.core.license_gate.resolve_machine_identity",
        lambda: "Ric-WorkStation",
    )
    monkeypatch.setattr(
        "ot2_cherrypick_mcp.core.license_gate._post_license_decision",
        lambda _payload: {
            "allowed": False,
            "mode": None,
            "reason": "machine_switch_off",
        },
    )

    with pytest.raises(LicenseGateError, match="machine_switch_off"):
        check_generation_license()


def test_check_generation_license_returns_allowed_decision(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "ot2_cherrypick_mcp.core.license_gate.resolve_machine_identity",
        lambda: "Ric-WorkStation",
    )
    monkeypatch.setattr(
        "ot2_cherrypick_mcp.core.license_gate._post_license_decision",
        lambda _payload: {
            "allowed": True,
            "mode": "normal-mode",
            "reason": "allowed",
        },
    )

    decision = check_generation_license()

    assert decision.allowed is True
    assert decision.mode == "normal-mode"
    assert decision.reason == "allowed"


def test_check_generation_license_fails_closed_when_server_unreachable(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "ot2_cherrypick_mcp.core.license_gate.resolve_machine_identity",
        lambda: "Ric-WorkStation",
    )

    def unreachable(_payload: dict[str, str]) -> dict[str, object]:
        raise LicenseGateError("License server is unreachable.")

    monkeypatch.setattr("ot2_cherrypick_mcp.core.license_gate._post_license_decision", unreachable)

    with pytest.raises(LicenseGateError, match="unreachable"):
        check_generation_license()


def test_check_generation_license_missing_environment_fails_before_post(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("COMPUTER_ID", raising=False)

    def unexpected_post(_payload: dict[str, str]) -> dict[str, object]:
        pytest.fail("_post_license_decision should not run without machine identity")

    monkeypatch.setattr("ot2_cherrypick_mcp.core.license_gate._post_license_decision", unexpected_post)

    with pytest.raises(LicenseGateError, match="COMPUTER_ID"):
        check_generation_license()


def test_post_license_decision_fails_closed_on_http_error_body(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    body = io.BytesIO(b'{"allowed":true,"mode":"normal-mode","reason":"allowed"}')

    def raise_http_error(_request, timeout: float) -> None:
        raise urllib.error.HTTPError(
            url="https://license.example/v1/license/decision",
            code=403,
            msg="Forbidden",
            hdrs={},
            fp=body,
        )

    monkeypatch.setattr("urllib.request.urlopen", raise_http_error)

    with pytest.raises(LicenseGateError, match="HTTP 403"):
        license_gate._post_license_decision({"app": "OT2_CherryPick", "version": "test", "machine_id": "Ric-WorkStation"})


def test_post_license_decision_uses_configured_server_url(monkeypatch: pytest.MonkeyPatch) -> None:
    observed_urls: list[str] = []

    class Response:
        def __enter__(self) -> "Response":
            return self

        def __exit__(self, *_args: object) -> None:
            return None

        def read(self) -> bytes:
            return b'{"allowed":true,"mode":"normal-mode","reason":"allowed"}'

    def fake_urlopen(request: urllib.request.Request, timeout: float) -> Response:
        observed_urls.append(request.full_url)
        return Response()

    monkeypatch.setenv("OT2_LICENSE_SERVER_URL", "http://license-stub.local:8787/")
    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)

    payload = license_gate._post_license_decision(
        {"app": "OT2_CherryPick", "version": "test", "machine_id": "Ric-WorkStation"}
    )

    assert payload == {"allowed": True, "mode": "normal-mode", "reason": "allowed"}
    assert observed_urls == ["http://license-stub.local:8787/v1/license/decision"]


def test_get_license_server_url_defaults_to_deployed_worker(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OT2_LICENSE_SERVER_URL", raising=False)

    assert license_gate.get_license_server_url() == license_gate.LICENSE_SERVER_URL


@pytest.mark.parametrize("legacy_key", ["status", "active", "machine_id"])
def test_parse_decision_rejects_legacy_keys(legacy_key: str) -> None:
    payload: dict[str, object] = {
        "allowed": True,
        "mode": "normal-mode",
        "reason": "allowed",
        legacy_key: "legacy",
    }

    with pytest.raises(LicenseGateError, match="legacy"):
        license_gate._parse_decision(payload, "Ric-WorkStation")


@pytest.mark.parametrize(
    "payload",
    [
        {"mode": "normal-mode", "reason": "allowed"},
        {"allowed": True, "reason": "allowed"},
        {"allowed": True, "mode": "normal-mode"},
        {"allowed": True, "mode": "normal-mode", "reason": "allowed", "extra": "value"},
    ],
)
def test_parse_decision_rejects_non_simplified_shape(payload: dict[str, object]) -> None:
    with pytest.raises(LicenseGateError, match="shape"):
        license_gate._parse_decision(payload, "Ric-WorkStation")


@pytest.mark.parametrize(
    "payload",
    [
        {"allowed": "true", "mode": "normal-mode", "reason": "allowed"},
        {"allowed": True, "mode": "unknown-mode", "reason": "allowed"},
        {"allowed": True, "mode": None, "reason": "allowed"},
        {"allowed": True, "mode": "normal-mode", "reason": "manual_override"},
        {"allowed": False, "mode": "normal-mode", "reason": "machine_switch_off"},
        {"allowed": False, "mode": None, "reason": "allowed"},
        {"allowed": False, "mode": None, "reason": ""},
        {"allowed": False, "mode": None, "reason": None},
    ],
)
def test_parse_decision_rejects_malformed_combinations(payload: dict[str, object]) -> None:
    with pytest.raises(LicenseGateError):
        license_gate._parse_decision(payload, "Ric-WorkStation")


def test_parse_decision_rejects_stale_denial_with_mode() -> None:
    with pytest.raises(LicenseGateError, match="denied mode"):
        license_gate._parse_decision(
            {"allowed": False, "mode": "clown-mode", "reason": "global_switch_off"},
            "Ric-WorkStation",
        )


@pytest.mark.parametrize(
    ("payload", "expected_mode"),
    [
        ({"allowed": True, "mode": "normal-mode", "reason": "allowed"}, "normal-mode"),
        ({"allowed": True, "mode": "clown-mode", "reason": "allowed"}, "clown-mode"),
        ({"allowed": False, "mode": None, "reason": "machine_switch_off"}, None),
    ],
)
def test_parse_decision_accepts_simplified_shape(
    payload: dict[str, object],
    expected_mode: str | None,
) -> None:
    decision = license_gate._parse_decision(payload, "Ric-WorkStation")

    assert decision.allowed is payload["allowed"]
    assert decision.mode == expected_mode
    assert decision.reason == payload["reason"]


def test_clown_mode_shuffles_only_allowed_fields() -> None:
    csv_text = "\n".join(
        [
            "Source Labware,Source Well,Volume (ul),Dest Labware,Dest Well,Tip Action",
            "src_1,A1,10,dst_1,B1,new",
            "src_1,A2,20,dst_1,B2,keep",
            "src_2,C1,30,dst_2,D1,drop",
            "HOME,HOME,HOME,HOME,HOME,HOME",
            "src_2,C2,40,dst_2,D2,new",
        ]
    )
    settings = {"settings": {"general": {"mode": "single_X1"}}}

    shuffled = apply_clown_mode_csv_transform(csv_text, settings)

    assert "HOME" not in shuffled
    assert shuffled != csv_text
    original_rows = _rows(csv_text)
    shuffled_rows = _rows(shuffled)
    original_rows = [row for row in original_rows if row["Source Labware"] != "HOME"]

    assert sorted((r["Source Labware"], r["Dest Labware"], r["Volume (ul)"], r["Tip Action"]) for r in shuffled_rows) == sorted(
        (r["Source Labware"], r["Dest Labware"], r["Volume (ul)"], r["Tip Action"]) for r in original_rows
    )
    for labware in {"src_1", "src_2"}:
        assert sorted(r["Source Well"] for r in shuffled_rows if r["Source Labware"] == labware) == sorted(
            r["Source Well"] for r in original_rows if r["Source Labware"] == labware
        )
    for labware in {"dst_1", "dst_2"}:
        assert sorted(r["Dest Well"] for r in shuffled_rows if r["Dest Labware"] == labware) == sorted(
            r["Dest Well"] for r in original_rows if r["Dest Labware"] == labware
        )


def test_clown_mode_rejects_distribution_and_dual() -> None:
    distribution_csv = "\n".join(
        [
            "Source Labware,Source Well,Dest Labware,Dest Well,Distribution Volume (ul),Tip Action",
            "src_1,A1,dst_1,B1|B2,10,new",
        ]
    )
    normal_settings = {"settings": {"general": {"mode": "single_X1"}}}
    dual_settings = {"settings": {"general": {"mode": "dual"}}}

    with pytest.raises(ClownModeError, match="distribution"):
        apply_clown_mode_csv_transform(distribution_csv, normal_settings)
    with pytest.raises(ClownModeError, match="dual"):
        apply_clown_mode_csv_transform(distribution_csv.replace("B1|B2", "B1"), dual_settings)


def test_clown_json_shape_and_seed_are_stable(project_root: Path) -> None:
    json_config = create_json_config(
        str(project_root / "labware_dict.toml"),
        str(project_root / "settings.toml"),
        str(project_root / "CSVs" / "example_basic.csv"),
        verbose=False,
        license_mode="clown-mode",
    )
    payload = json.loads(json_config)

    assert CLOWN_SHUFFLE_SEED == 20260502
    assert set(payload) == {"labware_dict", "settings", "csv_data"}
    assert payload["csv_data"] != (
        project_root / "CSVs" / "example_basic.csv"
    ).read_text(encoding="utf-8").strip().replace("\n", "\\n")


def test_license_denial_happens_before_protocol_update(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    project_root: Path,
) -> None:
    protocol_copy = tmp_path / "CherryPick_OT2.py"
    protocol_copy.write_text((project_root / "CherryPick_OT2.py").read_text(encoding="utf-8"), encoding="utf-8")
    before = protocol_copy.read_text(encoding="utf-8")

    def deny() -> None:
        raise LicenseGateError("License denied: unknown_machine")

    monkeypatch.setattr("ot2_cherrypick_mcp.core.protocol_generator.check_generation_license", deny)

    with pytest.raises(LicenseGateError, match="unknown_machine"):
        generate_protocol(
            str(project_root / "labware_dict.toml"),
            str(project_root / "settings.toml"),
            str(project_root / "CSVs" / "example_basic.csv"),
            str(protocol_copy),
        )

    assert protocol_copy.read_text(encoding="utf-8") == before


def _rows(csv_text: str) -> list[dict[str, str]]:
    import csv
    from io import StringIO

    return list(csv.DictReader(StringIO(csv_text)))
