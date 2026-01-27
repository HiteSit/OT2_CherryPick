# Phase 5: Structured Event Parsing - Research

**Researched:** 2026-01-26
**Domain:** opentrons_simulate text log parsing for OT-2 simulation fixtures
**Confidence:** MEDIUM

## Summary

This phase needs a parser that turns captured simulation log text into normalized event models for labware load, tip pickup/drop, aspirate, dispense, and mix. The current log fixtures are produced by `simulate_protocol.sh` and include protocol comments plus opentrons_simulate action lines. They are text-only and include both stdout and stderr; metadata captures `simulator_version` (currently `opentrons_simulate 8.7.0`).

The standard approach should be an adapter registry keyed by simulator/API version, with each adapter providing regex patterns for known action lines and a normalization layer that enriches events with identifiers from settings (slot -> labware_id, tiprack connection -> pipette_id). The parser must tolerate extra lines (helper output, diagnostic text) and should not fail on unknown lines by default.

**Primary recommendation:** Implement a versioned text-log adapter for `opentrons_simulate 8.7.0` that parses core action lines and enriches them using `settings.toml` to satisfy full identifier requirements.

## Standard Stack

The established libraries/tools for this domain:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python | >=3.12,<3.13 | Runtime for parser and tests | Project baseline in `pyproject.toml` |
| pytest | >=8.4.2,<9 | Test runner and fixtures | Existing test suite standard |
| dataclasses | stdlib | Typed event models | Lightweight, no new deps |
| re | stdlib | Regex log parsing | Required for stable text pattern matching |
| pathlib | stdlib | Fixture and config paths | Consistent path handling |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| tomllib | stdlib | Read settings.toml for context | Needed to map slots/pipettes to IDs |
| json | stdlib | Read fixture metadata | For simulator version and fixture context |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| dataclasses | pydantic v2 | Adds dependency and runtime overhead not needed for tests |
| regex + adapters | parser generator | Overkill for stable, line-based formats |

**Installation:**
```bash
# No new dependencies required for Phase 5
```

## Architecture Patterns

### Recommended Project Structure
```
tests/
├── simulation_logs/
│   ├── adapters/           # version-specific parsers
│   ├── models.py           # event dataclasses
│   ├── normalize.py        # enrichment using settings
│   └── parse.py            # adapter registry + entrypoint
└── fixtures/
    └── simulation/         # captured stdout/stderr + metadata
```

### Pattern 1: Adapter Registry by Simulator/API Version
**What:** Dispatch parsing to a version-specific adapter based on fixture metadata (`simulator_version`) or API level when available.
**When to use:** Always, because Phase 5 requires compatibility across simulator versions (COMP-01).
**Example:**
```python
# Source: tests/fixtures/simulation/basic-single_x1/metadata.json
ADAPTERS = {
    "opentrons_simulate 8.7.0": parse_v8_7_0,
}

def select_adapter(metadata: dict[str, object]) -> Callable[[str], list[Event]]:
    version = str(metadata.get("simulator_version", ""))
    if version in ADAPTERS:
        return ADAPTERS[version]
    return parse_unknown_version  # warn + best-effort
```

### Pattern 2: Normalize Events with Settings Context
**What:** After parsing raw log lines, enrich events with `labware_id`, `slot`, and `pipette_id` using `settings.toml` (slot -> labware_id, tiprack connection -> pipette_id).
**When to use:** Required to satisfy event fields from Phase 5 decisions (full identifiers on every event).
**Example:**
```python
# Source: tests/e2e/configs/single_X1/settings.toml
def map_slot_to_labware(settings: dict) -> dict[str, str]:
    return {entry["position_rack"]: entry["labware_id"] for entry in settings["settings"]["working_plate"]}
```

### Anti-Patterns to Avoid
- **Strictly failing on unknown lines:** Logs include helper output, warnings, and control messages; default to warn+skip.
- **Assuming one aspirate -> one dispense:** Distribution logs show one aspirate followed by multiple dispenses.
- **Ignoring return-to-tiprack drops:** `Returning tip` followed by `Dropping tip into A1...` should not be treated as trash.

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| TOML parsing | Custom key/value parsing | `tomllib` | Avoids edge-case parsing errors |
| Event schema | Raw dicts everywhere | `dataclasses` | Typed, explicit, low overhead |
| Path parsing | Manual string slicing | `pathlib.Path` | Cross-platform path safety |

**Key insight:** Use stdlib tooling and enrich from settings; avoid fragile, ad-hoc parsing of context that already exists in config files.

## Common Pitfalls

### Pitfall 1: Unicode micro sign in labware names
**What goes wrong:** Regex for labware display names fails on `Tip Rack 300 \u00b5L` strings.
**Why it happens:** Logs include human-readable names from opentrons_simulate, not labware IDs.
**How to avoid:** Treat labware names as opaque strings; prefer slot-based mapping to labware_id.
**Warning signs:** Tiprack labware names fail to normalize or map.

### Pitfall 2: Leading tabs/indentation in distribution logs
**What goes wrong:** `\tAspirating...` and `\tDispensing...` lines are skipped.
**Why it happens:** Distribution logs indent sub-steps with tabs.
**How to avoid:** Strip leading whitespace before pattern matching.
**Warning signs:** Missing aspirate/dispense events for distribution fixtures.

### Pitfall 3: Drop tip destination ambiguity
**What goes wrong:** All `Dropping tip` lines are treated as trash.
**Why it happens:** Tip return uses the same phrase but includes a well + labware target.
**How to avoid:** Use two patterns (trash vs tiprack) and record return vs discard.
**Warning signs:** Tip reuse tests fail when tips are returned.

### Pitfall 4: Missing labware load events
**What goes wrong:** No labware load events are produced because logs omit them.
**Why it happens:** Current protocol only comments on module init/offsets; base labware load is not logged.
**How to avoid:** Emit synthetic labware load events from `settings.toml` or add protocol comments in a later phase.
**Warning signs:** PARSE-01 tests fail for labware load events.

## Code Examples

Verified patterns from internal fixtures:

### Parse aspirate/dispense action lines
```python
# Source: tests/fixtures/simulation/basic-single_x1/stdout.txt
ASPIRATE_RE = re.compile(
    r"^Aspirating (?P<volume>[0-9.]+) uL from (?P<well>[A-H][0-9]+) of (?P<labware>.+) on slot (?P<slot>[0-9]+) at (?P<rate>[0-9.]+) uL/sec$"
)
DISPENSE_RE = re.compile(
    r"^Dispensing (?P<volume>[0-9.]+) uL into (?P<well>[A-H][0-9]+) of (?P<labware>.+) on slot (?P<slot>[0-9]+) at (?P<rate>[0-9.]+) uL/sec$"
)
```

### Parse tip pickup/drop lines
```python
# Source: tests/fixtures/simulation/basic-multi_x1/stdout.txt
PICK_UP_RE = re.compile(
    r"^Picking up tip from (?P<well>[A-H][0-9]+) of (?P<labware>.+) on slot (?P<slot>[0-9]+)$"
)
DROP_TRASH_RE = re.compile(r"^Dropping tip into Trash Bin on slot (?P<slot>[0-9]+)$")
DROP_RACK_RE = re.compile(
    r"^Dropping tip into (?P<well>[A-H][0-9]+) of (?P<labware>.+) on slot (?P<slot>[0-9]+)$"
)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Raw string assertions in tests | Adapter-based event parsing | Phase 5 (planned) | Enables version-aware, structured assertions |

**Deprecated/outdated:**
- Direct text matching in tests without normalization: too brittle across simulator versions.

## Open Questions

1. **Labware load event sourcing**
   - What we know: Current stdout fixtures do not include explicit labware-load lines.
   - What's unclear: Whether to synthesize events from `settings.toml` or add protocol comments later.
   - Recommendation: Generate synthetic labware load events from `settings.toml` in Phase 5.

2. **Mix event availability**
   - What we know: No `Mixing`/`Mix` lines appear in current fixtures.
   - What's unclear: Whether opentrons_simulate emits mix steps for the current protocol.
   - Recommendation: Define the mix event model now; parse when lines appear, otherwise leave empty.

3. **Strictness for unknown log lines**
   - What we know: Logs include helper output and control lines (e.g., `Row 4: HOME control`).
   - What's unclear: Whether parsing should fail on unknown lines.
   - Recommendation: Default to warn+skip with an opt-in strict mode for future phases.

## Sources

### Primary (HIGH confidence)
- `tests/fixtures/simulation/basic-single_x1/stdout.txt` - core action line formats
- `tests/fixtures/simulation/distribution-multi/stdout.txt` - distribution + indented substeps
- `tests/fixtures/simulation/extreme-single_x1/stdout.txt` - touch tip/delay/move lines
- `tests/fixtures/simulation/basic-single_x1/metadata.json` - simulator version string
- `tests/e2e/configs/single_X1/settings.toml` - slot to labware and pipette connections
- `tests/e2e/configs/multi/settings.toml` - multi-mode pipette connection
- `CherryPick_OT2.py` - protocol comments and labware load behavior
- `simulate_protocol.sh` - log capture sequence and stdout/stderr inputs

### Secondary (MEDIUM confidence)
- None (no external docs consulted for log line formats).

### Tertiary (LOW confidence)
- None.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - confirmed in `pyproject.toml` and existing test patterns
- Architecture: MEDIUM - derived from fixtures and protocol behavior
- Pitfalls: MEDIUM - inferred from fixture variations and protocol output

**Research date:** 2026-01-26
**Valid until:** 2026-02-25
