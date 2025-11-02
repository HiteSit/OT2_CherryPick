"""CSV helper tools for the MCP server."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Iterable, List, Optional

from fastmcp import FastMCP

from ..utils.errors import ConfigurationError
from ..utils.paths import resolve_project_path

CSV_HEADERS = [
    "Source Labware",
    "Source Well",
    "Volume (ul)",
    "Dest Labware",
    "Dest Well",
    "Source Height",
    "Dest Top",
]

DEFAULT_CSV_DIR = Path("CSVs")

__all__ = [
    "register_csv_tools",
    "generate_csv_template",
    "list_csv_files",
    "save_csv_content",
]


def generate_csv_template(
    *,
    filename: str,
    transfers: int,
    source_labware: str,
    dest_labware: str,
    default_volume: float = 0.0,
    source_height: Optional[float] = None,
    dest_top: Optional[float] = None,
    output_dir: str | Path = DEFAULT_CSV_DIR,
) -> Dict[str, object]:
    """Create a CSV template with the standard cherry-pick columns.

    The generated file contains the header row and the requested number of empty
    transfer rows with optional default values.
    """

    if transfers <= 0:
        raise ConfigurationError("transfers must be a positive integer")

    output_directory = resolve_project_path(output_dir)
    output_directory.mkdir(parents=True, exist_ok=True)

    target_path = output_directory / filename
    if target_path.exists():
        raise ConfigurationError(f"Target CSV already exists at {target_path}")

    rows = _build_rows(
        transfers=transfers,
        source_labware=source_labware,
        dest_labware=dest_labware,
        default_volume=default_volume,
        source_height=source_height,
        dest_top=dest_top,
    )

    with target_path.open("w", encoding="utf-8") as handle:
        handle.write(",".join(CSV_HEADERS) + "\n")
        for row in rows:
            handle.write(",".join(row) + "\n")

    return {
        "csv_file": str(target_path),
        "transfers": transfers,
        "source_labware": source_labware,
        "dest_labware": dest_labware,
    }


def list_csv_files(directory: str | Path = DEFAULT_CSV_DIR) -> List[str]:
    """Return a sorted list of CSV files in the given directory."""

    csv_dir = resolve_project_path(directory)
    if not csv_dir.exists():
        return []

    return sorted(str(path) for path in csv_dir.glob("*.csv"))


def save_csv_content(
    *,
    csv_content: str,
    filename: str,
    output_dir: str | Path = DEFAULT_CSV_DIR,
) -> Dict[str, object]:
    """Persist CSV content to a file for downstream workflow usage."""

    content = csv_content.strip()
    if not content:
        raise ConfigurationError("csv_content must not be empty")

    header = content.splitlines()[0]
    missing = [column for column in CSV_HEADERS if column not in header]
    if missing:
        raise ConfigurationError(
            "csv_content is missing expected columns: " + ", ".join(missing)
        )

    output_directory = resolve_project_path(output_dir)
    output_directory.mkdir(parents=True, exist_ok=True)

    target_path = output_directory / filename
    target_path.write_text(content + ("\n" if not content.endswith("\n") else ""), encoding="utf-8")

    return {"csv_file": str(target_path)}


def register_csv_tools(mcp: FastMCP) -> None:
    """Register CSV-related tools with FastMCP."""

    @mcp.tool(
        name="generate_csv_template",
        description="""Generate CSV template with proper column structure for liquid transfers.

EXAMPLE:
generate_csv_template(
    filename="cherry_pick_384.csv",
    transfers=96,
    source_labware="tube_rack_96_1500ul_4",
    dest_labware="384_ppv_55ul_2",
    default_volume=50.0,
    source_height=2.0,
    dest_top=-3.0
)

REQUIRED COLUMNS: Source Labware, Source Well, Volume (ul), Dest Labware, Dest Well
HEIGHT COLUMNS: Use EITHER Height (from bottom) OR Top (from rim) - never both
  - source_height: mm from bottom (e.g., 2.0)
  - dest_top: mm from rim, negative goes down (e.g., -3.0)

Template creates skeleton CSV that you then populate with specific well positions.
Use files://csvs resource to list generated files.
""",
    )
    def generate_csv_template_tool(  # pragma: no cover - intent tested via helper
        filename: str,
        transfers: int,
        source_labware: str,
        dest_labware: str,
        default_volume: float = 0.0,
        source_height: Optional[float] = None,
        dest_top: Optional[float] = None,
    ) -> Dict[str, object]:
        return generate_csv_template(
            filename=filename,
            transfers=transfers,
            source_labware=source_labware,
            dest_labware=dest_labware,
            default_volume=default_volume,
            source_height=source_height,
            dest_top=dest_top,
        )

    @mcp.tool(
        name="upload_csv_content",
        description="""Save CSV content to disk for protocol generation.

EXAMPLE:
upload_csv_content(
    csv_content="Source Labware,Source Well,Volume (ul),...\\nrow1_data\\nrow2_data",
    filename="my_transfers.csv",
    output_dir="CSVs/"
)

Use when you have CSV data as string (from user, from computation, etc).
Validates header contains required columns before saving.
Saved file can then be used with generate_protocol(csv_path="CSVs/my_transfers.csv").
""",
    )
    def upload_csv_content_tool(  # pragma: no cover - intent tested via helper
        csv_content: str,
        filename: str,
        output_dir: Optional[str] = None,
    ) -> Dict[str, object]:
        return save_csv_content(
            csv_content=csv_content,
            filename=filename,
            output_dir=output_dir or DEFAULT_CSV_DIR,
        )


def _build_rows(
    *,
    transfers: int,
    source_labware: str,
    dest_labware: str,
    default_volume: float,
    source_height: Optional[float],
    dest_top: Optional[float],
) -> Iterable[List[str]]:
    """Create placeholder rows for the template writer."""

    for _ in range(transfers):
        yield [
            source_labware,
            "",
            str(default_volume) if default_volume else "",
            dest_labware,
            "",
            "" if source_height is None else str(source_height),
            "" if dest_top is None else str(dest_top),
        ]
