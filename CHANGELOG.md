# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.3.0] - 2026-03-06

### Added

- Protocol name-based UUID reuse: deployment now scans existing protocol slots by `protocolName` metadata and overwrites in place instead of creating a new UUID directory every time. Multiple matches resolve to the most recently modified slot.

## [1.2.1] - 2026-03-06

### Changed

- Documentation updated to describe the `OPENTRONS_DIR` environment variable, auto-derived subdirectories, and auto-UUID deployment across all guides (configuration reference, MCP tools reference, GUI guide, README).

## [1.2.0] - 2026-03-06

### Added

- Auto-UUID deployment that creates UUID-based protocol directories under the Opentrons App and runs `opentrons.cli analyze` to pre-generate analysis JSON.
- CHANGELOG.md following Keep a Changelog format.

### Changed

- Unified `OPENTRONS_DIR` environment variable replaces separate `LABWARE_PATH` and protocol path variables; labware and protocol subdirectories are now auto-derived.
- GUI shell settings consolidated from dual fields (`target_protocol_src_win` + `labware_path_win`) into a single `opentrons_dir_win` field.
- Docker Compose updated to use a single `OPENTRONS_DIR` mount.
- Test suite updated for `OPENTRONS_DIR` env var migration.

### Fixed

- Sanitized hardcoded user paths in test fixtures and workspace.
- All license references corrected from MIT to GPL-3.0-or-later.

### Removed

- Removed `.mcp.json` and `simulate_protocol.sh` from version control (machine-specific files); `simulate_protocol.sh` re-added with placeholder paths.

## [1.1.0] - 2026-02-28

### Changed

- Renamed CSV columns `Source Height`/`Dest Height` to `Source Bottom`/`Dest Bottom` for clarity.

### Fixed

- Separated merged `.gitignore` entries for `CLAUDE.md` and `test_gui_state_*/`.
- Added `.mcp.json` and `test_gui_state_*` temporary directories to `.gitignore`.
- Clarified `.env` variable naming and default port behavior in README.

## [1.0.0] - 2026-02-28

### Added

- **Core Protocol System**
  - Complete OT-2 cherry-pick protocol generator compiling TOML config and CSV transfers into a self-contained Python protocol.
  - Five pipette modes: `single_X1`, `multi_X1`, `multi`, `distribution`, and dual-pipette.
  - Liquid handling presets (standard, viscous, slippery) with runtime resolution.
  - Automatic volume splitting for transfers exceeding pipette capacity.
  - HOME control row support for returning pipette to a safe position.
  - Configurable post-dispense mixing, air gaps, push-out, tip wicking, and delays.
  - Per-row tip action control (`new`/`keep`/`drop`) replacing global `tip_reuse`.
  - Customizable protocol name displayed on the OT-2 touchscreen.
  - Heater-Shaker module support.

- **MCP Server (AI-Native Interface)**
  - FastMCP 2.0 server with 22 tools, 7 resources, and 3 prompts.
  - Tools covering project init, config update, CSV management, protocol generation, simulation, validation, deployment, labware management, and workflow orchestration.
  - Resources exposing settings, labware catalog, deck layout, liquid handling config, CSV list, simulation logs, and calibration offsets.
  - Shorthand path aliases for common settings.
  - Runtime project directory switching with recent project history.
  - Validated with mcp-use and Mistral LLM integration tests.

- **GUI (Web Application)**
  - React + TypeScript frontend with a 4-step wizard: Deck Setup, Settings, CSV, Review/Execute.
  - FastAPI backend with workspace isolation (`gui_state/`).
  - CSV editor with spreadsheet and text views.
  - Labware scanner discovering both custom and official labware.
  - Per-slot offset editing with persist-to-database toggle.
  - Liquid handling preset selector with save-as-preset dialog.
  - Shell runner integration for `opentrons_simulate`.
  - Protocol deployment to Opentrons App directory.

- **Labware System**
  - Offset database (`offset_database.toml`) for per-slot calibration offsets.
  - Official labware list (`opentrons_labware_official.txt`).
  - Labware scanner auto-discovering custom labware JSON files.
  - Direct use of Opentrons load names (labware catalog removed from `labware_dict.toml`).

- **Docker**
  - Production Docker Compose setup with backend and frontend containers.
  - OCI labels, GHCR image tags, and healthcheck directives.
  - GitHub Actions CI/CD workflow for Docker image publishing.

- **Testing**
  - Approximately 400 test cases across unit, integration, E2E, FastAPI, and MCP layers.
  - JSON-driven E2E scenario runner with simulation fixtures.
  - Transfer event matching and diagnostic policy evaluation.
  - Unified test fixtures with manifest v2.0.

- **Validation**
  - Pipette volume range checks per CSV row.
  - Multi-mode labware compatibility validation.
  - Air gap plus volume capacity validation.
  - Deck slot conflict detection.

- **Documentation**
  - Comprehensive README with scientific framing.
  - Configuration reference, GUI guide, and liquid handling guide.
  - MCP tools reference covering all 22 tools.

[Unreleased]: https://github.com/HiteSit/OT2_CherryPick/compare/v1.3.0...HEAD
[1.3.0]: https://github.com/HiteSit/OT2_CherryPick/compare/v1.2.1...v1.3.0
[1.2.1]: https://github.com/HiteSit/OT2_CherryPick/compare/v1.2.0...v1.2.1
[1.2.0]: https://github.com/HiteSit/OT2_CherryPick/compare/v1.1.0...v1.2.0
[1.1.0]: https://github.com/HiteSit/OT2_CherryPick/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/HiteSit/OT2_CherryPick/releases/tag/v1.0.0
