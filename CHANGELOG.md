# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.6.0] - 2026-05-04

### Added

- Runtime license validation for protocol generation with deterministic public fallback handling.
- Docker activation support via `OT2_LICENSE_MACHINE_ID` and backend startup entrypoint handling.
- Focused unit and end-to-end coverage for the public license-gated generation flow.
- Tracked `docker/.env.example` as the Docker environment template while keeping local `.env` files ignored.

### Changed

- Route the helper script through the shared protocol generation path so runtime validation is consistently applied.
- Stabilize backend/frontend Docker health checks for build-time and runtime validation.

## [1.5.5] - 2026-05-01

### Added

- Local unlock gate (`unlock.key` marker) enforced at runtime startup; backend, MCP server, and Docker entrypoint validate via `ensure_runtime_ready()`.

### Changed

- Refined runtime initialization across backend, MCP server, and Docker image to centralize gate enforcement in `utils/paths.py`.
- Documented the runtime gate as an intentional distribution-control boundary.

## [1.5.4] - 2026-04-29

### Removed

- Untracked `docker/.env.example` from version control (added to `.gitignore`); kept locally as reference.

## [1.5.3] - 2026-04-14

### Changed

- Trimmed `docker/README.md` to architecture and persistence sections, removing fabricated production/security guidance and fixing incorrect volume names.

## [1.5.2] - 2026-04-14

### Changed

- Streamlined README to focus on core concepts and reduced cross-section redundancy.

### Removed

- Legacy standalone docs (`docs/configuration_reference.md`, `docs/gui_guide.md`, `docs/liquid_handling_guide.md`, `docs/mcp_tools_reference.md`) — content consolidated into primary entry points.

## [1.5.1] - 2026-03-31

### Fixed

- Excluded `offset_database.toml` from `ot2_sync_to_gui` — calibration offsets should never be overwritten during MCP-to-GUI sync.

## [1.5.0] - 2026-03-31

### Added

- `ot2_sync_to_gui` MCP tool — push project files into the running Docker GUI container via `docker cp`. Checks Docker/container status before syncing and warns if `shell_settings.json` is missing.
- `ot2_create_shell_settings` MCP tool — create `shell_settings.json` with Opentrons App Windows path for GUI simulation and deployment.
- `ot2_add_deck_entry` MCP tool — add labware/modules to deck layout. Auto-clears the template default deck on first use per project.
- `ot2_remove_deck_entry` MCP tool — remove a deck entry by slot number.
- `ot2_clear_deck` MCP tool — remove all entries from the deck layout.
- `TomlHandler.remove_array_item()` and `TomlHandler.clear_array()` methods for TOML array manipulation.
- `SyncError` exception class for Docker/sync failures.

### Changed

- Rewrote `APP_INSTRUCTIONS` with 6-step `NEW EXPERIMENT SETUP` workflow replacing the old 3-step standard workflow.
- Added multi mode CSV well rules to all relevant tool descriptions and CLAUDE.md (96-well: A-row only; 384-well: A/B-row for odd/even interleaving).
- Updated `ot2_scan_available_labware` description to present custom labware as table and reference `ot2_add_deck_entry`.
- Updated `ot2_set_project_directory` description to proactively show custom labware after switching.

## [1.4.1] - 2026-03-18

### Fixed

- Unified MCP setup instructions in README — Claude Code and Claude Desktop sections now show consistent env vars and path placeholders.

## [1.4.0] - 2026-03-18

### Added

- `ot2_batch_update_settings` MCP tool — apply multiple settings.toml changes in a single atomic write with one backup. Supports all shorthand aliases.
- `ot2_insert_home_rows` MCP tool — insert HOME control rows into a CSV every N transfers to correct precision drift during long protocols. Automatically forces `Tip Action: new` after each HOME row (firmware requirement).

## [1.3.4] - 2026-03-18

### Fixed

- `ot2_scan_available_labware` tool description now documents `OPENTRONS_DIR` env var fallback, preventing LLMs from hallucinating custom labware paths.

## [1.3.3] - 2026-03-18

### Changed

- Updated Claude Code MCP setup instructions from `.mcp.json` config to `claude mcp add` CLI command with global `--scope user` install.

## [1.3.2] - 2026-03-17

### Fixed

- Distribution path now honors `Tip Action: new` by calling `execute_tip_action()` instead of silently reusing the old tip.
- `tip_contacted` flag now correctly set after `distribute()` API call, preventing unnecessary liquid-contact steps.

### Changed

- Removed deprecated `tip_reuse` setting from MCP tools, server, prompts, simulation hints, and docs. Tip management is now exclusively controlled via per-row CSV `Tip Action` column.

### Added

- E2E tip action parsing tests for `single_X1` mode that verify pick-up/drop sequences by parsing `opentrons_simulate` output (11 scenarios covering keep, new, drop, and mixed sequences).
- Regression test for distribution tip action transitions (`new` after `keep`).

## [1.3.1] - 2026-03-12

### Fixed

- Removed incorrect auto-conversion of tip action `keep` to `drop` in `multi_X1` mode. Users can now reuse tips across consecutive transfers in `multi_X1` mode; tips are still force-dropped (not returned) at protocol end since the Opentrons API does not support `return_tip()` in partial nozzle configuration.

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

[Unreleased]: https://github.com/HiteSit/OT2_CherryPick/compare/v1.6.0...HEAD
[1.6.0]: https://github.com/HiteSit/OT2_CherryPick/compare/v1.5.5...v1.6.0
[1.5.5]: https://github.com/HiteSit/OT2_CherryPick/compare/v1.5.4...v1.5.5
[1.5.4]: https://github.com/HiteSit/OT2_CherryPick/compare/v1.5.3...v1.5.4
[1.5.3]: https://github.com/HiteSit/OT2_CherryPick/compare/v1.5.2...v1.5.3
[1.5.2]: https://github.com/HiteSit/OT2_CherryPick/compare/v1.5.1...v1.5.2
[1.5.1]: https://github.com/HiteSit/OT2_CherryPick/compare/v1.5.0...v1.5.1
[1.5.0]: https://github.com/HiteSit/OT2_CherryPick/compare/v1.4.1...v1.5.0
[1.4.1]: https://github.com/HiteSit/OT2_CherryPick/compare/v1.4.0...v1.4.1
[1.4.0]: https://github.com/HiteSit/OT2_CherryPick/compare/v1.3.4...v1.4.0
[1.3.4]: https://github.com/HiteSit/OT2_CherryPick/compare/v1.3.3...v1.3.4
[1.3.3]: https://github.com/HiteSit/OT2_CherryPick/compare/v1.3.2...v1.3.3
[1.3.2]: https://github.com/HiteSit/OT2_CherryPick/compare/v1.3.1...v1.3.2
[1.3.1]: https://github.com/HiteSit/OT2_CherryPick/compare/v1.3.0...v1.3.1
[1.3.0]: https://github.com/HiteSit/OT2_CherryPick/compare/v1.2.1...v1.3.0
[1.2.1]: https://github.com/HiteSit/OT2_CherryPick/compare/v1.2.0...v1.2.1
[1.2.0]: https://github.com/HiteSit/OT2_CherryPick/compare/v1.1.0...v1.2.0
[1.1.0]: https://github.com/HiteSit/OT2_CherryPick/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/HiteSit/OT2_CherryPick/releases/tag/v1.0.0
