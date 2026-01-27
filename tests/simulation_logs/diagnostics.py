from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence

from tests.simulation_logs.expectations import ExpectedTransfer
from tests.simulation_logs.matching import MatchResult


@dataclass(frozen=True)
class RowCoverage:
    total_rows: int
    covered_rows: int
    missing_rows: list[int]

    @property
    def coverage_percent(self) -> float:
        if self.total_rows == 0:
            return 100.0
        return (self.covered_rows / self.total_rows) * 100.0


def _collect_row_indices(transfers: Iterable[ExpectedTransfer]) -> set[int]:
    return {
        transfer.row_index
        for transfer in transfers
        if transfer.row_index is not None
    }


def compute_row_coverage(
    expected_transfers: Sequence[ExpectedTransfer],
    match: MatchResult,
) -> RowCoverage:
    total_rows = _collect_row_indices(expected_transfers)
    missing_rows = _collect_row_indices(match.missing_expected)
    mismatched_rows = _collect_row_indices(match.mismatched_expected)
    uncovered_rows = sorted(total_rows & (missing_rows | mismatched_rows))
    covered_rows = len(total_rows) - len(uncovered_rows)
    return RowCoverage(
        total_rows=len(total_rows),
        covered_rows=covered_rows,
        missing_rows=uncovered_rows,
    )


def format_row_coverage(coverage: RowCoverage) -> str:
    if coverage.total_rows == 0:
        return "Coverage: no CSV rows detected."
    percent = coverage.coverage_percent
    summary = f"Coverage: {coverage.covered_rows}/{coverage.total_rows} rows ({percent:.0f}%)."
    if coverage.missing_rows:
        missing = ", ".join(str(row) for row in coverage.missing_rows)
        return f"{summary} Missing rows: {missing}."
    return summary


def format_transfer_report(
    match: MatchResult,
    expected_transfers: Sequence[ExpectedTransfer],
) -> str:
    coverage = compute_row_coverage(expected_transfers, match)
    return "\n".join([match.report(), format_row_coverage(coverage)])


__all__ = [
    "RowCoverage",
    "compute_row_coverage",
    "format_row_coverage",
    "format_transfer_report",
]
