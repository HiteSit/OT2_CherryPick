# Phase 4: Log Capture Baseline - Research

**Researched:** 2026-01-26
**Domain:** opentrons_simulate CLI log capture + pytest fixture baselines
**Confidence:** MEDIUM

## Summary

Phase 4 focuses on capturing deterministic simulation logs by running `simulate_protocol.sh`, which regenerates `CherryPick_OT2.py` via `uv run python helper_cherry_pick.py` and then runs `opentrons_simulate`. The canonical runner already emits step markers and routes the labware path from its machine configuration, so fixtures should wrap this script and capture both stdout and stderr for each CSV/settings combination.

The installed simulator reports `opentrons_simulate 8.7.0` and its CLI options show that custom labware is supplied with `--custom-labware-path` (`-L`) and that only explicitly provided directories are searched (not subdirectories). Tests should therefore validate that the resolved labware directory exists and contains required JSON labware files before running fixtures, and record the simulator version and labware path in metadata for reproducibility.

Capturing fixtures should emphasize reproducible metadata and clear failure context: keep stdout/stderr as raw files (or optionally normalized), and fail tests on warnings or non-zero return codes with the captured output attached. Simulation output patterns could not be validated in this environment because no Opentrons labware directory is available, so the final normalization rules should be confirmed by running fixtures on a machine with labware JSONs.

**Primary recommendation:** Wrap `simulate_protocol.sh` with a pytest fixture runner that writes per-fixture stdout/stderr plus metadata (CSV, settings variant, simulator version, labware path) and fails fast on warnings or errors.

## Standard Stack

The established libraries/tools for this domain:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python | 3.12 | Test/runtime environment | Project requires >=3.12 in `pyproject.toml`. |
| pytest | 8.4.2 | Test runner for fixtures | Existing test suite is pytest-based. |
| opentrons_simulate | 8.7.0 | CLI simulator to generate logs | Provides simulation output and exit codes. |
| simulate_protocol.sh | repo script | Canonical helper+simulate runner | Required by phase decisions for fixture capture. |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| subprocess (stdlib) | n/a | Run script and capture stdout/stderr | Use for invoking `simulate_protocol.sh`. |
| json (stdlib) | n/a | Store fixture metadata | Use for metadata sidecar files. |
| pathlib (stdlib) | n/a | File/dir management | Use for fixture directories and paths. |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Raw stdout/stderr fixtures | `pytest-regressions` snapshots | Adds dependency; not currently in stack. |
| `simulate_protocol.sh` | Direct `opentrons_simulate` calls | Violates phase decision and misses helper step. |

**Installation:**
```bash
uv run opentrons_simulate -v
```

## Architecture Patterns

### Recommended Project Structure
```
tests/
├── fixtures/
│   └── simulation/
│       ├── <fixture-id>/
│       │   ├── stdout.txt
│       │   ├── stderr.txt
│       │   └── metadata.json
│       └── manifest.json
└── e2e/
    └── configs/
```

### Pattern 1: Fixture capture via simulate_protocol.sh
**What:** Run `simulate_protocol.sh` for each CSV/settings variant, capturing stdout/stderr, and emit metadata for reproducibility.
**When to use:** Any baseline fixture creation or refresh cycle.
**Example:**
```python
# Source: tests/e2e/conftest.py (subprocess pattern)
result = subprocess.run(
    ["bash", "simulate_protocol.sh", str(csv_path)],
    capture_output=True,
    text=True,
    cwd=repo_root,
    timeout=120,
)
```

### Pattern 2: Settings profile swaps for fixture matrix
**What:** Since `simulate_protocol.sh` reads repo-root `settings.toml`, copy a profile into place before each run and restore afterward.
**When to use:** Capturing fixtures across mode boundaries and labware layouts.
**Example:**
```python
# Source: tests/e2e/conftest.py (settings copy pattern)
shutil.copy2(settings_profile, repo_root / "settings.toml")
```

### Anti-Patterns to Avoid
- **Direct `opentrons_simulate` calls:** Skips the helper regeneration step required by the phase decision.
- **Ignoring stderr:** Simulator warnings can appear on stderr and must be captured to fail tests correctly.

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Process execution + capture | Custom pipes/threads | `subprocess.run(..., capture_output=True, text=True)` | Handles stdout/stderr reliably. |
| Fixture metadata serialization | Ad-hoc text blobs | JSON sidecar files | Easier to parse, diff, and extend. |
| Labware path selection | Hardcoded absolute paths in tests | Parse `simulate_protocol.sh` machine config + overrides | Matches canonical runner and avoids drift. |

**Key insight:** The canonical runner already defines how to regenerate and simulate; tests should wrap it rather than reimplementing its behavior.

## Common Pitfalls

### Pitfall 1: Labware directory not present or incomplete
**What goes wrong:** `opentrons_simulate` fails because custom labware JSONs are missing.
**Why it happens:** `--custom-labware-path` only searches provided directories and not subdirectories, and the WSL path may not exist on CI machines.
**How to avoid:** Validate that the resolved labware directory exists and contains the required JSON files before running fixtures; decide on fail-fast vs skip in planning.
**Warning signs:** stderr contains labware-not-found errors or missing-definition warnings.

### Pitfall 2: Output normalization hides actionable errors
**What goes wrong:** Over-normalizing logs removes warning/error context needed for diagnosis.
**Why it happens:** Aggressive filtering to make fixtures deterministic can strip simulator stack traces or warning tags.
**How to avoid:** Store raw stdout/stderr alongside any normalized output, and fail tests on warnings/errors using raw context.
**Warning signs:** Failing tests show generic mismatch but no simulator error excerpt.

### Pitfall 3: Fixture drift from helper regeneration
**What goes wrong:** Fixtures are captured without re-running `helper_cherry_pick.py`, so protocol changes are not reflected.
**Why it happens:** Direct simulation calls bypass the helper step.
**How to avoid:** Always use `simulate_protocol.sh`, which explicitly regenerates the protocol.
**Warning signs:** Fixtures pass despite changes to `settings.toml` or CSV inputs.

## Code Examples

Verified patterns from project sources:

### Subprocess capture for helper and simulate
```python
# Source: tests/e2e/conftest.py
result = subprocess.run(
    ["uv", "run", "opentrons_simulate", str(protocol_path)],
    capture_output=True,
    text=True,
    cwd=project_root,
    timeout=120,
)
```

### Simulation command used by canonical runner
```bash
# Source: simulate_protocol.sh
uv run python helper_cherry_pick.py -l labware_dict.toml -s settings.toml -c "$CSV_FILE" -p CherryPick_OT2.py
opentrons_simulate --custom-labware $LABWARE_PATH CherryPick_OT2.py
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Ad-hoc manual simulation runs | Scripted helper + simulate pipeline | Unknown | Ensures protocol regeneration before simulation. |
| Unversioned log output | Metadata + simulator version recorded | 2026 phase decision | Enables reproducible baselines. |

**Deprecated/outdated:**
- Using direct `opentrons_simulate` without helper regeneration (project-specific; contradicts phase decision).

## Open Questions

1. **Exact stdout/stderr patterns from `simulate_protocol.sh`**
   - What we know: Script emits step markers and runs `opentrons_simulate` with captured stdout/stderr.
   - What's unclear: Exact warning/error formatting and whether warnings land in stdout or stderr.
   - Recommendation: Run fixture capture on a machine with valid labware JSONs and catalog real outputs before finalizing normalization rules.

2. **Labware path availability in CI/local environments**
   - What we know: Script resolves Windows paths to WSL and supports overrides; tests currently auto-detect labware in `tests/e2e/conftest.py`.
   - What's unclear: Whether CI will have a labware directory or should skip/xfail.
   - Recommendation: Decide fail-fast vs skip behavior and document it in fixtures metadata.

## Sources

### Primary (HIGH confidence)
- `simulate_protocol.sh` (repo) - canonical helper + simulate command sequence and labware path resolution.
- `tests/e2e/conftest.py` (repo) - subprocess capture pattern and settings profile management.
- `src/ot2_cherrypick_mcp/core/simulation.py` (repo) - log capture schema and command assembly.
- `opentrons_simulate -h` (local CLI, 2026-01-26) - CLI options including `--custom-labware-path` and output mode.
- `opentrons_simulate -v` (local CLI, 2026-01-26) - version 8.7.0.

### Secondary (MEDIUM confidence)
- https://docs.opentrons.com/v2/advanced_control/command_line.html (opentrons_execute CLI overview).

### Tertiary (LOW confidence)
- https://docs.opentrons.com/v2/simulation.html (docs page did not contain simulate CLI details).

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - versions validated from repo and local CLI.
- Architecture: MEDIUM - based on repo patterns and phase decisions; requires validation with real simulator output.
- Pitfalls: MEDIUM - inferred from CLI help and repo patterns, pending output verification.

**Research date:** 2026-01-26
**Valid until:** 2026-02-25
