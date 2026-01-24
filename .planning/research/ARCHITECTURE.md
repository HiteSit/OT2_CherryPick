# Architecture Research

**Domain:** OT-2 simulation log parsing + test refactor
**Researched:** 2026-01-24
**Confidence:** MEDIUM

## Standard Architecture

### System Overview

```
┌────────────────────────────────────────────────────────────────────┐
│                        Orchestrators / Tools                        │
├────────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────────────┐  ┌───────────────────┐   │
│  │ CLI Script  │  │ MCP Simulation Tool │  │ GUI Workflow      │   │
│  │ simulate_*  │  │ ot2_simulate_*      │  │ (FastAPI)         │   │
│  └──────┬──────┘  └─────────┬───────────┘  └─────────┬─────────┘   │
│         │                   │                        │             │
├─────────┴───────────────────┴────────────────────────┴─────────────┤
│                         Simulation Core Layer                        │
├────────────────────────────────────────────────────────────────────┤
│  ┌────────────────┐  ┌──────────────────────┐  ┌────────────────┐  │
│  │ simulate_*     │  │ log parser (NEW)     │  │ result mapper  │  │
│  │ core/sim.py    │  │ core/sim_log.py      │  │ core/validate  │  │
│  └──────┬─────────┘  └──────────┬───────────┘  └────────┬───────┘  │
│         │                        │                       │          │
├─────────┴────────────────────────┴───────────────────────┴─────────┤
│                       External Execution + Storage                   │
├────────────────────────────────────────────────────────────────────┤
│  ┌────────────────────┐  ┌─────────────────────────────┐           │
│  │ opentrons_simulate  │  │ logs/last_simulation.json   │           │
│  └────────────────────┘  └─────────────────────────────┘           │
└────────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Typical Implementation |
|-----------|----------------|------------------------|
| CLI script | Run helper + simulation; user-facing messages | `simulate_protocol.sh` with env wiring |
| Simulation tool | MCP entry point for simulation | `tools/simulation_tools.py` |
| Simulation core | Invoke `opentrons_simulate`, capture stdout/stderr | `core/simulation.py` |
| Log parser (NEW) | Parse stdout to structured events | `core/simulation_log.py` |
| Result mapper (NEW) | Map parsed events to CSV transfers | `core/validation.py` or new `core/transfer_map.py` |
| Log store | Persist last simulation | `logs/last_simulation.json` |

## Recommended Project Structure

```
src/ot2_cherrypick_mcp/
├── core/
│   ├── simulation.py            # runs opentrons_simulate, captures output
│   ├── simulation_log.py         # NEW: parse stdout into structured events
│   ├── transfer_mapping.py       # NEW: CSV row ↔ simulation event matching
│   └── validation.py             # uses transfer mapping to assert expectations
├── tools/
│   └── simulation_tools.py       # MCP tool wrapper, can expose parsed output
└── resources/
    └── log_resources.py          # read-only access to last_simulation.json
tests/
├── fixtures/
│   └── simulation_logs/          # NEW: captured stdout samples
├── test_simulation_tools.py      # extend: parser + mapping integration
├── test_simulation_parser.py     # NEW: pure parser unit tests
└── test_validation_distribution.py # extend: mapping expectations
```

### Structure Rationale

- **`core/`:** keep parsing and mapping in core layer to share between CLI, MCP, and GUI workflows.
- **`tests/fixtures/`:** stable stdout samples prevent brittle tests that depend on opentrons_simulate changes.

## Architectural Patterns

### Pattern 1: Parse-Then-Map Pipeline

**What:** Convert raw stdout to normalized events, then map events to expected CSV transfers.
**When to use:** When stdout structure is semi-stable but needs normalization.
**Trade-offs:** Adds one more step, but isolates parsing from business logic.

**Example:**
```python
events = parse_simulation_stdout(stdout)
matches = map_events_to_transfers(events, transfers)
assert_matches(matches)
```

### Pattern 2: Dependency-Injection Runner for Simulation

**What:** Pass a runner callable into `simulate_protocol` to avoid shelling out in tests.
**When to use:** Unit tests for error handling and log parsing.
**Trade-offs:** Extra parameter plumbing, but avoids flaky subprocess tests.

**Example:**
```python
def runner(cmd):
    return CompletedProcess(cmd, 0, stdout=sample, stderr="")
simulate_protocol(protocol_path, runner=runner)
```

### Pattern 3: Version-Gated Parser

**What:** Detect simulator version or log format markers before parsing.
**When to use:** If opentrons_simulate log formats change across versions.
**Trade-offs:** Requires extra logic, but prevents silent mismatches.

## Data Flow

### Request Flow

```
CSV + settings.toml
    ↓
helper_cherry_pick.py → CherryPick_OT2.py
    ↓
opentrons_simulate
    ↓
stdout/stderr → parse_simulation_stdout()
    ↓
map_events_to_transfers()
    ↓
validation report / test assertions
```

### State Management

```
last_simulation.json
    ↓ (read)
log_resources.py → tools/simulation_tools.py → callers
```

### Key Data Flows

1. **Simulation validation:** stdout → parsed events → expected transfer mapping → pass/fail summary.
2. **Tool feedback:** `simulate_protocol` → log file → MCP resource for UI visibility.

## Scaling Considerations

| Scale | Architecture Adjustments |
|-------|--------------------------|
| 0-1k transfers | parse in-memory, full stdout retained |
| 1k-10k transfers | stream parse, store event summaries only |
| 10k+ transfers | chunked parsing + optional sampling for validation |

### Scaling Priorities

1. **First bottleneck:** regex-heavy parsing → switch to line streaming parser.
2. **Second bottleneck:** huge stdout files → write structured log alongside raw stdout.

## Anti-Patterns

### Anti-Pattern 1: Parsing in Tests Only

**What people do:** embed regex parsing inside each test.
**Why it's wrong:** logic duplication and inconsistent interpretations.
**Do this instead:** shared parser in `core/simulation_log.py` with dedicated unit tests.

### Anti-Pattern 2: Validating Against Raw Strings

**What people do:** assert literal stdout strings or line numbers.
**Why it's wrong:** breaks on minor simulator formatting changes.
**Do this instead:** parse into normalized events with stable fields.

## Integration Points

### External Services

| Service | Integration Pattern | Notes |
|---------|---------------------|-------|
| opentrons_simulate | subprocess via `simulate_protocol` | treat stdout format as semi-stable; add format guards |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| `tools/simulation_tools.py` ↔ `core/simulation.py` | direct function call | extend to return parsed summary optionally |
| `core/simulation.py` ↔ `core/simulation_log.py` | in-memory stdout | parser should be side-effect free |
| `core/validation.py` ↔ `core/transfer_mapping.py` | data objects | keep mapping separate from parsing |
| `tests/*` ↔ fixtures | file-based samples | keep logs versioned by simulator version |

## Suggested Build Order

1. **Create parser module:** add `core/simulation_log.py` + fixtures; unit tests for parsing.
2. **Add transfer mapping layer:** map parsed events to CSV transfers; unit tests with fixture CSVs.
3. **Integrate with validation:** update `core/validation.py` to use mapping output.
4. **Expose summaries:** optional parsed output in `tools/simulation_tools.py` and log resources.
5. **Refactor tests:** replace string assertions with parsed event assertions.

## Sources

- Codebase review: `src/ot2_cherrypick_mcp/core/simulation.py`
- Codebase review: `src/ot2_cherrypick_mcp/tools/simulation_tools.py`
- Codebase review: `simulate_protocol.sh`
- Tests: `tests/test_simulation_tools.py`

---
*Architecture research for: OT-2 simulation log parsing + test refactor*
*Researched: 2026-01-24*
