"""Validation engine for E2E agentic test scenarios.

Checks scenario results against expected outcomes defined in JSON scenario files.
Supports file existence, TOML value checks, file content checks, response content
checks, CSV row counts, and simulation log validation.
"""

from __future__ import annotations

import glob
import json
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping


@dataclass
class CheckResult:
    """Result of a single validation check."""

    name: str
    passed: bool
    message: str
    hard: bool = True  # Hard = file/TOML check; Soft = response heuristic


@dataclass
class ValidationReport:
    """Aggregated results from all validation checks for a scenario."""

    scenario_id: str
    scenario_name: str
    checks: list[CheckResult] = field(default_factory=list)
    agent_response: str = ""
    error: str | None = None

    @property
    def passed(self) -> bool:
        if self.error:
            return False
        return all(c.passed for c in self.checks)

    @property
    def hard_passed(self) -> bool:
        if self.error:
            return False
        return all(c.passed for c in self.checks if c.hard)

    @property
    def soft_passed(self) -> bool:
        return all(c.passed for c in self.checks if not c.hard)

    @property
    def total(self) -> int:
        return len(self.checks)

    @property
    def pass_count(self) -> int:
        return sum(1 for c in self.checks if c.passed)

    @property
    def fail_count(self) -> int:
        return sum(1 for c in self.checks if not c.passed)


def _resolve_toml_path(document: Mapping[str, Any], dotted_path: str) -> Any:
    """Walk a nested TOML document using a dotted path string."""

    segments = dotted_path.split(".")
    current: Any = document
    for segment in segments:
        if isinstance(current, Mapping):
            if segment not in current:
                raise KeyError(f"Key '{segment}' not found at '{dotted_path}'")
            current = current[segment]
        else:
            raise KeyError(f"Path '{dotted_path}' does not resolve (hit non-mapping)")
    return current


class Validator:
    """Runs validation checks from a scenario's validation spec against workspace state."""

    def __init__(self, workspace: Path) -> None:
        self.workspace = workspace

    def run_all(
        self,
        validations: dict[str, Any],
        response: str,
    ) -> list[CheckResult]:
        """Execute all validation checks defined in the scenario spec."""

        results: list[CheckResult] = []

        if "files_exist" in validations:
            results.extend(self.check_files_exist(validations["files_exist"]))

        if "files_not_exist" in validations:
            results.extend(self.check_files_not_exist(validations["files_not_exist"]))

        if "toml_values" in validations:
            results.extend(self.check_toml_values(validations["toml_values"]))

        if "file_contains" in validations:
            results.extend(self.check_file_contains(validations["file_contains"]))

        if "file_not_contains" in validations:
            results.extend(self.check_file_not_contains(validations["file_not_contains"]))

        if "response_contains_any" in validations:
            results.extend(
                self.check_response_contains_any(response, validations["response_contains_any"])
            )

        if "response_not_contains" in validations:
            results.extend(
                self.check_response_not_contains(response, validations["response_not_contains"])
            )

        if "csv_row_count" in validations:
            results.extend(self.check_csv_row_count(validations["csv_row_count"]))

        if "simulation_log" in validations:
            results.extend(self.check_simulation_log(validations["simulation_log"]))

        return results

    # ------------------------------------------------------------------
    # File existence checks
    # ------------------------------------------------------------------

    def check_files_exist(self, patterns: list[str]) -> list[CheckResult]:
        results: list[CheckResult] = []
        for pattern in patterns:
            matches = glob.glob(str(self.workspace / pattern))
            passed = len(matches) > 0
            results.append(CheckResult(
                name=f"file_exists:{pattern}",
                passed=passed,
                message=f"Found {len(matches)} match(es)" if passed else f"No files matching '{pattern}'",
                hard=True,
            ))
        return results

    def check_files_not_exist(self, patterns: list[str]) -> list[CheckResult]:
        results: list[CheckResult] = []
        for pattern in patterns:
            matches = glob.glob(str(self.workspace / pattern))
            passed = len(matches) == 0
            results.append(CheckResult(
                name=f"file_not_exists:{pattern}",
                passed=passed,
                message="No files found (expected)" if passed else f"Unexpected files: {matches}",
                hard=True,
            ))
        return results

    # ------------------------------------------------------------------
    # TOML value checks
    # ------------------------------------------------------------------

    def check_toml_values(self, checks: dict[str, dict[str, Any]]) -> list[CheckResult]:
        """Check TOML values. Format: {filename: {dotted.path: expected_value}}."""

        results: list[CheckResult] = []
        for filename, path_checks in checks.items():
            toml_path = self.workspace / filename
            if not toml_path.exists():
                results.append(CheckResult(
                    name=f"toml:{filename}",
                    passed=False,
                    message=f"TOML file not found: {filename}",
                    hard=True,
                ))
                continue

            try:
                document = tomllib.loads(toml_path.read_text(encoding="utf-8"))
            except Exception as exc:
                results.append(CheckResult(
                    name=f"toml:{filename}",
                    passed=False,
                    message=f"Failed to parse TOML: {exc}",
                    hard=True,
                ))
                continue

            for dotted_path, expected in path_checks.items():
                try:
                    actual = _resolve_toml_path(document, dotted_path)
                    passed = actual == expected
                    results.append(CheckResult(
                        name=f"toml:{filename}:{dotted_path}",
                        passed=passed,
                        message=(
                            f"OK: {dotted_path} = {actual!r}"
                            if passed
                            else f"Expected {dotted_path} = {expected!r}, got {actual!r}"
                        ),
                        hard=True,
                    ))
                except KeyError as exc:
                    results.append(CheckResult(
                        name=f"toml:{filename}:{dotted_path}",
                        passed=False,
                        message=str(exc),
                        hard=True,
                    ))
        return results

    # ------------------------------------------------------------------
    # File content checks
    # ------------------------------------------------------------------

    def check_file_contains(self, checks: dict[str, list[str]]) -> list[CheckResult]:
        """Check that files contain expected substrings. Format: {filename: [substrings]}."""

        results: list[CheckResult] = []
        for filename, substrings in checks.items():
            filepath = self.workspace / filename
            if not filepath.exists():
                results.append(CheckResult(
                    name=f"contains:{filename}",
                    passed=False,
                    message=f"File not found: {filename}",
                    hard=True,
                ))
                continue

            content = filepath.read_text(encoding="utf-8")
            for substring in substrings:
                passed = substring in content
                results.append(CheckResult(
                    name=f"contains:{filename}:{substring[:40]}",
                    passed=passed,
                    message=f"Found '{substring[:40]}'" if passed else f"Missing '{substring[:40]}'",
                    hard=True,
                ))
        return results

    def check_file_not_contains(self, checks: dict[str, list[str]]) -> list[CheckResult]:
        results: list[CheckResult] = []
        for filename, substrings in checks.items():
            filepath = self.workspace / filename
            if not filepath.exists():
                # File doesn't exist, so it can't contain anything - pass
                continue

            content = filepath.read_text(encoding="utf-8")
            for substring in substrings:
                passed = substring not in content
                results.append(CheckResult(
                    name=f"not_contains:{filename}:{substring[:40]}",
                    passed=passed,
                    message=(
                        f"Correctly absent: '{substring[:40]}'"
                        if passed
                        else f"Unexpectedly found: '{substring[:40]}'"
                    ),
                    hard=True,
                ))
        return results

    # ------------------------------------------------------------------
    # Response content checks (soft)
    # ------------------------------------------------------------------

    def check_response_contains_any(
        self, response: str, keywords: list[str]
    ) -> list[CheckResult]:
        lowered = response.lower()
        found = [kw for kw in keywords if kw.lower() in lowered]
        passed = len(found) > 0
        return [CheckResult(
            name="response_contains_any",
            passed=passed,
            message=(
                f"Found: {found}"
                if passed
                else f"None of {keywords} found in response"
            ),
            hard=False,
        )]

    def check_response_not_contains(
        self, response: str, keywords: list[str]
    ) -> list[CheckResult]:
        lowered = response.lower()
        found = [kw for kw in keywords if kw.lower() in lowered]
        passed = len(found) == 0
        return [CheckResult(
            name="response_not_contains",
            passed=passed,
            message=(
                "No forbidden keywords found"
                if passed
                else f"Found forbidden keywords: {found}"
            ),
            hard=False,
        )]

    # ------------------------------------------------------------------
    # CSV row count checks
    # ------------------------------------------------------------------

    def check_csv_row_count(self, checks: dict[str, int]) -> list[CheckResult]:
        """Check CSV data row counts. Format: {filename: expected_data_rows}."""

        results: list[CheckResult] = []
        for filename, expected_rows in checks.items():
            filepath = self.workspace / filename
            if not filepath.exists():
                results.append(CheckResult(
                    name=f"csv_rows:{filename}",
                    passed=False,
                    message=f"CSV not found: {filename}",
                    hard=True,
                ))
                continue

            lines = filepath.read_text(encoding="utf-8").strip().splitlines()
            actual_data_rows = max(0, len(lines) - 1)  # Subtract header
            passed = actual_data_rows == expected_rows
            results.append(CheckResult(
                name=f"csv_rows:{filename}",
                passed=passed,
                message=(
                    f"OK: {actual_data_rows} data rows"
                    if passed
                    else f"Expected {expected_rows} data rows, got {actual_data_rows}"
                ),
                hard=True,
            ))
        return results

    # ------------------------------------------------------------------
    # Simulation log checks
    # ------------------------------------------------------------------

    def check_simulation_log(self, checks: dict[str, Any]) -> list[CheckResult]:
        """Check simulation log. Format: {exists: bool, returncode: int}."""

        results: list[CheckResult] = []
        log_path = self.workspace / "logs" / "last_simulation.json"

        if checks.get("exists"):
            passed = log_path.exists()
            results.append(CheckResult(
                name="simulation_log:exists",
                passed=passed,
                message="Log exists" if passed else "Simulation log not found",
                hard=True,
            ))

        if "returncode" in checks and log_path.exists():
            try:
                payload = json.loads(log_path.read_text(encoding="utf-8"))
                actual_rc = payload.get("returncode")
                expected_rc = checks["returncode"]
                passed = actual_rc == expected_rc
                results.append(CheckResult(
                    name="simulation_log:returncode",
                    passed=passed,
                    message=(
                        f"OK: returncode={actual_rc}"
                        if passed
                        else f"Expected returncode={expected_rc}, got {actual_rc}"
                    ),
                    hard=True,
                ))
            except Exception as exc:
                results.append(CheckResult(
                    name="simulation_log:returncode",
                    passed=False,
                    message=f"Failed to read simulation log: {exc}",
                    hard=True,
                ))

        return results
