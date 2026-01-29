# Phase 12: Fixture Settings Profile Parity Check - Research

**Researched:** 2026-01-29
**Domain:** Simulation log fixture validation and settings profile consistency
**Confidence:** HIGH

## Summary

This phase targets a specific drift risk in the simulation log test pipeline: expectations are built from the fixture manifest settings_profile while parsing and normalization use the fixture metadata settings_profile. The codebase currently treats these as separate sources, so a mismatch can silently skew expected transfers vs parsed events. The goal is to assert parity and fail fast when fixture metadata diverges from manifest intent.

The standard approach in this repo is to centralize fixture identity in `manifest.json` and capture runtime metadata in per-fixture `metadata.json`. Parsing uses metadata to select settings, while expected transfers use manifest entries. The parity check should live in shared fixture utilities or a focused test to enforce that both sources agree for every fixture in the manifest.

**Primary recommendation:** Add a single parity validation that compares `manifest.settings_profile` to `metadata.json.settings_profile` for each fixture and fail tests when they differ.

## Standard Stack

The established libraries/tools for this domain:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python | >=3.12,<3.13 | Test/runtime language | Project baseline in `pyproject.toml` |
| pytest | >=8.4.2,<9 | Test runner and assertions | Existing test suite uses pytest throughout |
| stdlib json/pathlib/dataclasses | N/A | Fixture IO and data modeling | Used in fixture manifest, metadata, and helpers |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| tomllib | stdlib (3.11+) | Load `settings.toml` for normalization | Used by `tests/unit/simulation_logs/normalize.py` |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| stdlib json/pathlib | third-party IO libs | Adds dependency weight without benefit for small fixture IO |

**Installation:**
```bash
# No new packages required for this phase
```

## Architecture Patterns

### Recommended Project Structure
```
tests/
├── support/                     # Fixture and path helpers
├── integration/simulation_logs/ # Manifest + captured fixtures
└── unit/simulation_logs/        # Parsing/normalization/expectations
```

### Pattern 1: Manifest as fixture index, metadata as capture record
**What:** `manifest.json` defines fixture_id + csv + settings_profile; `metadata.json` is the captured run record. Expectations use manifest; parsing uses metadata.
**When to use:** Always, for tests that compare expected transfers to parsed simulation logs.
**Example:**
```python
# Source: tests/support/fixtures.py
def load_manifest(path: Path | None = None) -> list[FixtureEntry]:
    manifest_path = path or MANIFEST_PATH
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    fixtures = data.get("fixtures", [])
    if not isinstance(fixtures, list):
        raise ValueError("Manifest must contain a list under 'fixtures'")
    entries: list[FixtureEntry] = []
    for item in fixtures:
        entries.append(
            FixtureEntry(
                fixture_id=item["fixture_id"],
                csv_path=item["csv_path"],
                settings_profile=item["settings_profile"],
                expect_failure=bool(item["expect_failure"]),
            )
        )
    return entries
```

### Pattern 2: Metadata-driven parsing and normalization
**What:** `parse_fixture` reads `metadata.json` and uses `settings_profile` to load settings for normalization.
**When to use:** Any parsing of captured simulation output.
**Example:**
```python
# Source: tests/unit/simulation_logs/parse.py
settings_profile = metadata.get("settings_profile")
if not settings_profile:
    raise ValueError(f"Fixture metadata missing settings_profile: {fixture_id}")

settings_path = SETTINGS_ROOT / str(settings_profile) / "settings.toml"
settings = load_settings(settings_path)
normalized = normalize_events(raw_events, settings)
```

### Anti-Patterns to Avoid
- **Implicit divergence:** Relying on manifest and metadata independently without validating parity leads to silent mismatch between expected transfers and parsed events.
- **Ad hoc settings loading:** Bypassing `load_settings_profile`/`load_settings` risks inconsistent file paths and settings selection.

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Locating fixture paths | Custom string joins | `tests/support/paths.py` helpers | Centralizes repo path resolution |
| Reading manifest entries | Custom JSON parsing | `tests/support/fixtures.load_manifest` | Consistent validation and dataclass mapping |
| Loading settings for normalization | Custom TOML parsing | `tests/unit/simulation_logs/normalize.load_settings` | Standardizes settings parsing |

**Key insight:** Consistency in fixture IO paths and settings loading is essential for reliable parity checks.

## Common Pitfalls

### Pitfall 1: Manifest/metadata drift
**What goes wrong:** Expected transfers use manifest `settings_profile` but parser normalizes with metadata `settings_profile`; mismatch yields false failures or masked regressions.
**Why it happens:** `metadata.json` is generated during capture and can drift if manifest is edited without re-capturing fixtures.
**How to avoid:** Add a parity assertion comparing both sources for every manifest entry and fail fast.
**Warning signs:** Transfer matching failures that disappear when changing expected settings or re-running capture.

### Pitfall 2: Missing metadata settings_profile
**What goes wrong:** Parsing raises `ValueError` when metadata lacks `settings_profile`.
**Why it happens:** Fixture metadata edited manually or generated by older scripts.
**How to avoid:** Validate metadata shape and keep capture tooling consistent.
**Warning signs:** `Fixture metadata missing settings_profile` errors during tests.

## Code Examples

Verified patterns from repository sources:

### Build expected transfers using manifest settings_profile
```python
# Source: tests/support/simulation.py
def build_expected_transfers_for_entry(entry: FixtureEntry) -> Sequence[ExpectedTransfer]:
    csv_path = resolve_fixture_csv(entry)
    settings = load_settings_profile(entry.settings_profile)
    return expectations_module.build_expected_transfers(csv_path, settings)
```

### Fixture metadata includes settings_profile
```json
// Source: tests/integration/simulation_logs/fixtures/basic-single_x1/metadata.json
{
  "fixture_id": "basic-single_x1",
  "csv": "CSVs/example_basic.csv",
  "settings_profile": "single_X1"
}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| N/A | Manifest used for expectations; metadata used for parsing | Unknown (pre-existing) | Requires parity check to prevent drift |

**Deprecated/outdated:**
- None identified in current repo for this specific flow.

## Open Questions

1. **Should manifest be considered the source of truth or should mismatches be resolved by re-capturing fixtures?**
   - What we know: Manifest defines test intent; metadata reflects capture state.
   - What's unclear: Whether to auto-correct metadata or fail tests requiring manual refresh.
   - Recommendation: Fail tests on mismatch and require explicit re-capture or manifest update.

## Sources

### Primary (HIGH confidence)
- `tests/support/fixtures.py` - manifest schema, fixture capture, metadata writing
- `tests/support/simulation.py` - expectations use manifest settings_profile
- `tests/unit/simulation_logs/parse.py` - parsing uses metadata settings_profile
- `tests/integration/simulation_logs/fixtures/manifest.json` - fixture manifest source

### Secondary (MEDIUM confidence)
- None

### Tertiary (LOW confidence)
- None

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - from `pyproject.toml` and stdlib usage in tests
- Architecture: HIGH - directly from repo test utilities and fixtures
- Pitfalls: HIGH - derived from explicit dual-source settings_profile usage

**Research date:** 2026-01-29
**Valid until:** 2026-02-28
