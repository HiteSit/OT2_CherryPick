"""Remote license gate used before protocol generation."""

from __future__ import annotations

import json
import os
import socket
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from importlib.metadata import PackageNotFoundError, version
from typing import Any


LICENSE_SERVER_URL = "https://ot2-license-worker.riccardofusco99.workers.dev"
LICENSE_SERVER_URL_ENV = "OT2_LICENSE_SERVER_URL"
LICENSE_DECISION_PATH = "/v1/license/decision"
LICENSE_APP_NAME = "OT2_CherryPick"
LICENSE_TIMEOUT_SECONDS = 2.0
LICENSE_RETRIES = 2
ALLOWED_MODES = {"normal-mode", "clown-mode"}


class LicenseGateError(RuntimeError):
    """Raised when protocol generation is not licensed."""


@dataclass(frozen=True)
class LicenseDecision:
    """Effective remote decision for the current machine."""

    allowed: bool
    mode: str | None
    reason: str


def get_application_version() -> str:
    """Return the installed package version for the license decision payload."""

    try:
        return version(LICENSE_APP_NAME)
    except PackageNotFoundError:
        return "unknown"


def get_license_server_url() -> str:
    """Return the configured license server URL."""

    return os.getenv(LICENSE_SERVER_URL_ENV, "").strip().rstrip("/") or LICENSE_SERVER_URL


def resolve_machine_identity() -> str:
    """Resolve the deployment-local machine identity."""

    env_identity = os.getenv("COMPUTER_ID", "").strip()
    if not env_identity:
        raise LicenseGateError("COMPUTER_ID is missing.")
    return env_identity


def check_generation_license() -> LicenseDecision:
    """Validate that this machine is allowed to generate a protocol."""

    machine_id = resolve_machine_identity()
    payload = {
        "app": LICENSE_APP_NAME,
        "version": get_application_version(),
        "machine_id": machine_id,
    }
    decision_payload = _post_license_decision(payload)
    decision = _parse_decision(decision_payload, machine_id)
    if not decision.allowed:
        raise LicenseGateError(f"License denied: {decision.reason}")
    return decision


def _post_license_decision(payload: dict[str, str]) -> dict[str, Any]:
    """POST the license decision request with a small fail-closed retry loop."""

    url = f"{get_license_server_url()}{LICENSE_DECISION_PATH}"
    encoded = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    last_error: BaseException | None = None

    for attempt in range(LICENSE_RETRIES + 1):
        request = urllib.request.Request(
            url,
            data=encoded,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": "OT2-CherryPick-LicenseClient/1.0",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=LICENSE_TIMEOUT_SECONDS) as response:
                body = response.read().decode("utf-8")
            parsed = json.loads(body)
            if not isinstance(parsed, dict):
                raise LicenseGateError("License server returned a non-object response.")
            return parsed
        except urllib.error.HTTPError as exc:
            raise LicenseGateError(f"License server returned HTTP {exc.code}.") from exc
        except (OSError, TimeoutError, socket.timeout, urllib.error.URLError, json.JSONDecodeError) as exc:
            last_error = exc
            if attempt < LICENSE_RETRIES:
                time.sleep(0.2)

    raise LicenseGateError("License server is unreachable.") from last_error


def _parse_decision(payload: dict[str, Any], requested_machine_id: str) -> LicenseDecision:
    """Validate the Worker response shape and convert it to a decision object."""

    del requested_machine_id

    legacy_keys = {"status", "active", "machine_id"}
    if legacy_keys & payload.keys():
        raise LicenseGateError("License server returned a legacy decision shape.")

    expected_keys = {"allowed", "mode", "reason"}
    if set(payload) != expected_keys:
        raise LicenseGateError("License server returned an invalid decision shape.")

    allowed = payload["allowed"]
    mode = payload["mode"]
    reason = _string(payload["reason"])

    if not isinstance(allowed, bool):
        raise LicenseGateError("License server returned an invalid allowed flag.")
    if not reason:
        raise LicenseGateError("License server returned an invalid reason.")

    if allowed:
        if not isinstance(mode, str) or mode not in ALLOWED_MODES:
            raise LicenseGateError("License server returned an invalid mode.")
        if reason != "allowed":
            raise LicenseGateError("License server returned an invalid allowed reason.")
    else:
        if mode is not None:
            raise LicenseGateError("License server returned an invalid denied mode.")
        if reason == "allowed":
            raise LicenseGateError("License server returned an invalid denied reason.")

    return LicenseDecision(allowed=allowed, mode=mode, reason=reason)


def _string(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


__all__ = [
    "ALLOWED_MODES",
    "LICENSE_APP_NAME",
    "LICENSE_DECISION_PATH",
    "LICENSE_RETRIES",
    "LICENSE_SERVER_URL",
    "LICENSE_SERVER_URL_ENV",
    "LICENSE_TIMEOUT_SECONDS",
    "LicenseDecision",
    "LicenseGateError",
    "check_generation_license",
    "get_license_server_url",
    "resolve_machine_identity",
]
