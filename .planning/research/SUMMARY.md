# Project Research Summary

**Project:** OT2 CherryPick GUI Enhancement
**Domain:** OT-2 simulation log parsing and test verification
**Researched:** 2026-01-24
**Confidence:** MEDIUM

## Executive Summary

This project is a test validation layer for OT-2 protocol simulations: capture `opentrons_simulate` output, parse it into structured events, and assert that CSV-driven transfer intent matches what the simulator executed. Experts build this by treating the simulator as an external boundary, normalizing logs into a stable event model, and running semantic assertions rather than brittle string diffs.

The recommended approach is a parse-then-map pipeline in the core layer: capture stdout/stderr into fixtures, parse into Pydantic-modeled events, then map events to expected CSV transfers (mode-aware) before validating. Keep parsing in shared core modules so CLI, MCP tools, and GUI workflows all consume identical results. The main risks are log format drift, mode-specific mapping errors, and fixture decay. Mitigate by version-tagged fixtures, normalization of paths/order, and explicit separation between parsing and validation stages.

## Key Findings

### Recommended Stack

Use Python 3.12 with Pydantic v2 for strict, inspectable event models and pytest for regression testing. Add pytest-regressions for stable JSON/YAML snapshots and pytest-mock for subprocess isolation. Avoid heavy parser generators; stick to regex normalization plus schema validation so log changes are easy to adapt. See `.planning/research/STACK.md` for details.

**Core technologies:**
- Python 3.12.x: runtime for parsing and tests — matches project baseline and Opentrons tooling.
- Pydantic 2.12.5: typed event models — strict validation and explicit parse errors.
- pytest 8.4.2: test runner — already in use and supports regression fixtures.

### Expected Features

The MVP focuses on capturing simulation output, parsing core actions, and validating CSV-to-transfer mapping. Differentiators add richer diagnostics and mode-aware assertions once the core pipeline is stable. See `.planning/research/FEATURES.md` for details.

**Must have (table stakes):**
- Capture `opentrons_simulate` stdout/stderr in tests — foundational log input.
- Parse run log into structured events — enables semantic assertions.
- Validate transfer mapping vs CSV — core correctness check.
- Detect simulation errors/warnings — fail tests on invalid configurations.
- Version-tolerant parsing — protects against log phrasing drift.

**Should have (competitive):**
- Mode-aware assertions — prevents false positives in multi-channel runs.
- Semantic diff reporting — faster diagnosis than raw logs.
- Tip reuse/mix/air gap checks — validate liquid handling policies.

**Defer (v2+):**
- Log format adapters by API level — only if simulator output drifts frequently.
- Coverage metrics dashboards — valuable later, not required for correctness.

### Architecture Approach

Centralize parsing and mapping in the core layer, with shared usage across CLI, MCP tools, and GUI workflows. The recommended structure adds a `simulation_log` parser module and a `transfer_mapping` layer before validation, following a parse-then-map pipeline. See `.planning/research/ARCHITECTURE.md` for details.

**Major components:**
1. `core/simulation.py` — run `opentrons_simulate` and capture stdout/stderr.
2. `core/simulation_log.py` — parse stdout into normalized events.
3. `core/transfer_mapping.py` / `core/validation.py` — map events to expected CSV transfers and assert outcomes.
4. `tools/simulation_tools.py` + `resources/log_resources.py` — expose parsed summaries to MCP/GUI.

### Critical Pitfalls

1. **Brittle parsing of human-readable logs** — build version-tolerant event models and fixtures tagged with simulator version.
2. **Assuming one CSV row equals one log line** — implement mode-aware expectations for single/multi/multi_X1.
3. **Mixing parsing with validation logic** — keep parser pure and validate in a separate mapping layer.
4. **Relying on unstable ordering** — assert only required ordering (aspirate before dispense) and compare sets otherwise.
5. **Fixture drift from real configs** — regenerate fixtures from current configs with metadata (settings + simulator version).

## Implications for Roadmap

Based on research, suggested phase structure:

### Phase 1: Log Capture + Fixtures
**Rationale:** All downstream parsing depends on stable, reproducible log inputs.
**Delivers:** Captured stdout/stderr fixtures, simulator version metadata, normalization of paths/line endings.
**Addresses:** Log capture in tests, error/warning detection.
**Avoids:** Fixture drift, cross-platform path failures.

### Phase 2: Parser + Event Model
**Rationale:** Structured events are the foundation for meaningful assertions.
**Delivers:** `simulation_log` parser, Pydantic event schemas, normalized action events.
**Uses:** Python 3.12, Pydantic 2.12.5, pytest-regressions fixtures.
**Implements:** Parse-then-map pipeline in core layer.

### Phase 3: Transfer Mapping + Validation Integration
**Rationale:** Map CSV intent to parsed events before refactoring tests.
**Delivers:** CSV-to-event expectation builder, mode-aware mapping, test harness updates with clear failure summaries.
**Addresses:** Transfer mapping assertions, mode-aware checks, semantic failure reporting.
**Avoids:** CSV/log mismapping, ordering assumptions, parsing/validation entanglement.

### Phase 4: Advanced Diagnostics + Policy Checks
**Rationale:** Differentiators depend on stable core parsing and mapping.
**Delivers:** Tip/mix/air-gap policy validation, coverage metrics, optional API-level log adapters.
**Addresses:** Differentiators and v2+ items.

### Phase Ordering Rationale

- Capture and normalize logs first to prevent brittle, irreproducible tests.
- Parsing and mapping must precede validation and test refactors to keep logic centralized.
- Differentiators only add value after core mapping is reliable and mode-aware.

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 2:** Log format is undocumented; need empirical verification across simulator versions.
- **Phase 3:** Mode semantics (single/multi/multi_X1) require careful mapping validation.
- **Phase 4:** API-level adapters depend on how often simulator output drifts.

Phases with standard patterns (skip research-phase):
- **Phase 1:** Log capture + fixture normalization follows standard testing patterns.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Versions validated via PyPI sources; aligns with current project runtime. |
| Features | MEDIUM | Simulator log format is undocumented; expectations inferred from testing norms. |
| Architecture | MEDIUM | Based on current codebase structure and typical parsing pipelines. |
| Pitfalls | MEDIUM | Derived from domain experience; limited external validation. |

**Overall confidence:** MEDIUM

### Gaps to Address

- Simulator log format stability: validate against actual `opentrons_simulate` outputs and capture version metadata.
- Mode-specific mapping: confirm multi/multi_X1 log patterns and transfer grouping behavior.
- GUI vs repo-root logs: ensure fixtures cover both execution paths and normalize any differences.
- Volume rounding/units: document normalization rules for small-volume transfers.

## Sources

### Primary (HIGH confidence)
- https://pypi.org/project/pydantic/ — current Pydantic version and compatibility.
- https://pypi.org/project/pytest-regressions/ — regression testing tooling.
- https://pypi.org/project/pytest-mock/ — subprocess and file IO mocking support.

### Secondary (MEDIUM confidence)
- https://docs.opentrons.com/v2/new_protocol_api.html — run log notes and API behavior.
- Codebase review: `src/ot2_cherrypick_mcp/core/simulation.py` and `src/ot2_cherrypick_mcp/tools/simulation_tools.py`.
- Existing test suite: `tests/test_simulation_tools.py`.

### Tertiary (LOW confidence)
- Project domain knowledge — pitfalls and testing patterns inferred from local workflows.

---
*Research completed: 2026-01-24*
*Ready for roadmap: yes*
