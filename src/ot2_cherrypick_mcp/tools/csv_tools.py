"""CSV helper tools for the MCP server."""

from __future__ import annotations

import csv
import io
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from fastmcp import FastMCP

from ..utils.errors import ConfigurationError
from ..utils.paths import resolve_project_path

CSV_BASE_HEADERS = [
    "Source Labware",
    "Source Well",
    "Dest Labware",
    "Dest Well",
]

CSV_VOLUME_HEADERS = [
    "Volume (ul)",
    "Distribution Volume (ul)",
]

CSV_HEADERS = CSV_BASE_HEADERS + [
    "Volume (ul)",
    "Source Bottom",
    "Dest Top",
    "Tip Action",
]

DEFAULT_CSV_DIR = Path("CSVs")

__all__ = [
    "register_csv_tools",
    "generate_csv_template",
    "insert_home_rows",
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

    # Check base required columns
    required_columns = CSV_BASE_HEADERS + ["Tip Action"]
    missing_base = [column for column in required_columns if column not in header]
    if missing_base:
        raise ConfigurationError(
            f"csv_content is missing required columns: {', '.join(missing_base)}\n"
            f"All required columns: {', '.join(CSV_BASE_HEADERS + ['Tip Action'])}\n"
            f"Use ot2_generate_csv_template to create a properly formatted CSV skeleton."
        )

    # Check that at least one volume column exists
    has_volume = any(vol_col in header for vol_col in CSV_VOLUME_HEADERS)
    if not has_volume:
        raise ConfigurationError(
            f"csv_content must have at least one volume column: {', '.join(CSV_VOLUME_HEADERS)}\n"
            f"Use ot2_generate_csv_template to create a CSV with correct structure."
        )

    output_directory = resolve_project_path(output_dir)
    output_directory.mkdir(parents=True, exist_ok=True)

    target_path = output_directory / filename
    target_path.write_text(content + ("\n" if not content.endswith("\n") else ""), encoding="utf-8")

    return {"csv_file": str(target_path)}


def insert_home_rows(
    *,
    csv_path: str | Path,
    every_n_transfers: int,
) -> Dict[str, object]:
    """Insert HOME control rows into an existing CSV every *every_n_transfers* transfers.

    HOME rows trigger ``protocol.home()`` on the OT-2 to correct precision
    drift during long runs.  The firmware requires a fresh tip after homing,
    so any transfer row immediately following an inserted HOME row has its
    ``Tip Action`` forced to ``new``.

    Existing HOME rows in the CSV are counted but **not** duplicated.
    """

    if every_n_transfers <= 0:
        raise ConfigurationError("every_n_transfers must be a positive integer")

    resolved = resolve_project_path(csv_path)
    if not resolved.exists():
        raise ConfigurationError(f"CSV file not found: {resolved}")

    text = resolved.read_text(encoding="utf-8")
    reader = csv.DictReader(io.StringIO(text))
    if reader.fieldnames is None:
        raise ConfigurationError("CSV file has no header row")

    headers = list(reader.fieldnames)
    rows: list[dict[str, str]] = list(reader)

    def _is_home(row: dict[str, str]) -> bool:
        values = [v.strip().upper() for v in row.values() if v and v.strip()]
        return bool(values) and all(v == "HOME" for v in values)

    home_row = {col: "HOME" for col in headers}

    output: list[dict[str, str]] = []
    transfer_count = 0
    homes_inserted = 0
    tip_actions_forced: list[int] = []

    for row in rows:
        if _is_home(row):
            # Keep existing HOME rows; reset counter
            output.append(row)
            transfer_count = 0
            continue

        transfer_count += 1

        if transfer_count > every_n_transfers:
            output.append(home_row.copy())
            homes_inserted += 1
            transfer_count = 1  # current row is the first after HOME

            # Force Tip Action: new on this row
            if "Tip Action" in row and row.get("Tip Action", "").strip().lower() != "new":
                tip_actions_forced.append(len(output) + 1)  # 1-based CSV row number (header=1)
                row = {**row, "Tip Action": "new"}

        output.append(row)

    # Write back
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=headers, lineterminator="\n")
    writer.writeheader()
    writer.writerows(output)
    resolved.write_text(buf.getvalue(), encoding="utf-8")

    return {
        "csv_file": str(resolved),
        "original_transfer_rows": len(rows),
        "home_rows_inserted": homes_inserted,
        "tip_actions_forced_to_new": tip_actions_forced,
        "total_rows_now": len(output),
    }


def register_csv_tools(mcp: FastMCP) -> None:
    """Register CSV-related tools with FastMCP."""

    @mcp.tool(
        name="ot2_generate_csv_template",
        description="""Generate a CSV skeleton file with proper column structure for liquid transfers.

WHEN TO USE: To create a new CSV template that the user then fills in with specific well
positions and volumes. If you already have complete CSV data as a string, use
ot2_upload_csv_content instead.

LABWARE NAMING: Source and destination labware names must match settings.toml deck layout
in the format "labware_id_slot" (e.g., "tube_rack_96_1500ul_4" for tube_rack_96_1500ul in slot 4).
Check status://deck-layout to see current labware assignments.

HEIGHT COLUMNS: Use EITHER Height (mm from bottom) OR Top (mm from rim) - never both.
  - source_height: mm from well bottom (e.g., 2.0)
  - dest_top: mm from well rim, negative goes down (e.g., -3.0)

EXAMPLE:
ot2_generate_csv_template(
    filename="cherry_pick.csv", transfers=96,
    source_labware="tube_rack_96_1500ul_4",
    dest_labware="384_ppv_55ul_2",
    default_volume=50.0, source_height=2.0, dest_top=-3.0
)
""",
        annotations={
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": False,
            "openWorldHint": False
        }
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
        name="ot2_upload_csv_content",
        description="""Save CSV content string to a file on disk for protocol generation.

WHEN TO USE: When you have CSV data already constructed as a string (from user input,
computation, or pasted content). If you need to create a template to fill later, use
ot2_generate_csv_template instead.

Validates that required columns are present: Source Labware, Source Well, Dest Labware,
Dest Well, Tip Action, and at least one volume column (Volume (ul) or Distribution Volume (ul)).

REQUIRED COLUMNS: Source Labware, Source Well, Volume (ul), Dest Labware, Dest Well, Tip Action
OPTIONAL COLUMNS: Source Bottom, Source Top, Dest Bottom, Dest Top, Mix Volume, Mix Height,
Flow Aspirate, Flow Dispense, Air Gap, Air Gap Rate

After saving, use the file with ot2_generate_protocol(csv_path="CSVs/filename.csv").

EXAMPLE:
ot2_upload_csv_content(
    csv_content="Source Labware,Source Well,Volume (ul),Dest Labware,Dest Well,Source Bottom,Dest Top,Tip Action\\ntube_rack_96_1500ul_4,A1,50,384_ppv_55ul_2,B1,2,-5,new",
    filename="my_transfers.csv"
)
""",
        annotations={
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False
        }
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

    @mcp.tool(
        name="ot2_list_csv_files",
        description="""List all CSV transfer files available in the project.

WHEN TO USE: To see which CSV files exist before calling ot2_generate_protocol
or ot2_full_workflow. Also useful to verify a CSV was created successfully
after ot2_generate_csv_template or ot2_upload_csv_content.

Returns a list of file paths that can be passed to csv_path parameters.
""",
        annotations={
            "readOnlyHint": True,
            "openWorldHint": False
        }
    )
    def list_csv_files_tool() -> Dict[str, object]:
        files = list_csv_files()
        return {
            "csv_files": files,
            "count": len(files),
            "message": f"Found {len(files)} CSV file(s)." if files else "No CSV files found. Use ot2_generate_csv_template or ot2_upload_csv_content to create one.",
        }

    @mcp.tool(
        name="ot2_insert_home_rows",
        description="""Insert HOME control rows into a CSV to re-home the robot periodically.

WHEN TO USE: When the user wants to correct precision drift during long protocols
by re-homing the robot every N transfers. Common phrases:
- "home every 20 transfers"
- "add homing rows to my CSV"
- "re-home the robot periodically"

WHAT IT DOES:
1. Reads an existing CSV file
2. Inserts a HOME row (all columns = "HOME") every N transfer rows
3. Forces Tip Action: new on rows immediately after each HOME (firmware requirement)
4. Preserves existing HOME rows without duplication
5. Writes the modified CSV back to disk

EXAMPLE:
ot2_insert_home_rows(csv_path="CSVs/cherry_pick.csv", every_n_transfers=20)

CONSTRAINTS:
- The row after HOME MUST pick up a new tip (firmware requirement).
  This tool automatically sets Tip Action: new on those rows.
- Existing HOME rows in the CSV reset the counter but are not duplicated.

AFTER USING: Run ot2_validate_configuration or ot2_full_workflow to verify the CSV.
""",
        annotations={
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": False,
            "openWorldHint": False
        }
    )
    def insert_home_rows_tool(
        csv_path: str,
        every_n_transfers: int,
    ) -> Dict[str, object]:
        return insert_home_rows(
            csv_path=csv_path,
            every_n_transfers=every_n_transfers,
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
            "keep",
        ]
