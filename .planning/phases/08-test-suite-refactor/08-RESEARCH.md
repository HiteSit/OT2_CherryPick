# Phase 08: Test Suite Refactor - Research

**Researched:** 2026-01-27
**Domain:** Pytest test suite organization, fixtures, and simulation log harness
**Confidence:** MEDIUM

## Summary

This research focused on restructuring the pytest test suite to align with the phase decisions: grouping by feature domain, separating unit vs integration, and colocating simulation log fixtures with the suites that use them. The current repo already centralizes simulation log parsing/matching under `tests/simulation_logs/` and fixture capture under `tests/fixtures/simulation/`, but paths are hard-coded and will need a shared utility when relocated.

Pytest’s fixture system and standard test discovery rules are the backbone for reusable harnesses. Official pytest guidance recommends keeping tests outside application code and, for new projects, using the importlib import mode to avoid test module name collisions. These details matter when restructuring test folders to avoid import surprises.

**Primary recommendation:** Keep pytest as the sole test runner, move fixtures into feature-domain directories with shared utilities in a dedicated support module, and update all path constants via a single fixture-path resolver.

## Standard Stack

The established libraries/tools for this domain:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| pytest | 8.4.2 (repo pin) | Test runner, fixtures, markers, discovery | Project already uses pytest across unit, integration, and e2e suites; official docs define the expected discovery and fixture patterns. |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| mcp-use | >=1.3.7,<2 | MCP integration test harness | Required for integration tests that spin MCP agents in `tests/conftest.py`. |
| langchain-mistralai | >=0.2.12,<0.3 | LLM client used by MCP tests | Needed for MCP integration tests using `ChatMistralAI`. |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| pytest | unittest | Loses fixture system, markers, and test discovery behavior already used throughout the suite. |

**Installation:**
```bash
uv add pytest
```

## Architecture Patterns

### Recommended Project Structure
```
tests/
├── unit/
│   ├── simulation_logs/      # parser, normalization, matching, policies
│   ├── transfer_mapping/     # CSV expectations, mapping logic
│   └── mcp_tools/            # pure unit tests for MCP tool helpers
├── integration/
│   ├── simulation_logs/      # fixture-driven validation
│   │   ├── fixtures/          # colocated raw + normalized fixtures
│   │   ├── conftest.py
│   │   └── test_*.py
│   ├── workflow/             # e2e workflow tests (current e2e suite)
│   └── api/                  # FastAPI integration tests
├── support/
│   ├── paths.py              # fixture root + settings root resolution
│   ├── fixtures.py           # load_manifest, capture_fixture
│   └── simulation.py         # parser setup, normalization helpers
└── conftest.py               # shared pytest fixtures (root)
```

### Pattern 1: Centralized fixture path resolution
**What:** One module defines fixture roots, manifest path, and settings roots, so refactors only change a single source.
**When to use:** Any test or helper that loads fixtures, reads settings profiles, or writes normalized artifacts.
**Example:**
```python
# Source: https://docs.pytest.org/en/stable/explanation/goodpractices.html
# (Use this pytest structure, then keep fixture paths centralized)
```

### Pattern 2: Factory fixtures for scenario setup
**What:** Provide fixture factories that return functions for per-test setup (e.g., fixture loaders or parser builders).
**When to use:** When tests need multiple scenarios in one module or must override defaults without global state.
**Example:**
```python
# Source: https://docs.pytest.org/en/stable/how-to/fixtures.html
import pytest

@pytest.fixture
def make_fixture_loader():
    def _make_loader(fixture_id):
        return fixture_id  # replace with actual loader
    return _make_loader
```

### Anti-Patterns to Avoid
- **Hard-coded fixture roots in multiple modules:** makes refactors brittle and easy to break when directory layout changes.
- **Mixed responsibilities in conftest:** keep global fixtures minimal; put domain-specific helpers in `tests/support` to avoid fixture pollution.

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Test discovery rules | Custom test runner | pytest discovery | Pytest’s discovery rules are well-defined and already assumed by the suite. |
| Temporary directories | Manual temp dir creation | pytest `tmp_path` fixture | Built-in lifecycle and cleanup reduce flaky tests. |
| Fixture scoping | Custom global state | pytest fixture scopes | Official fixture scopes avoid shared state leaks. |

**Key insight:** Refactors should leverage pytest’s fixture system instead of creating bespoke test harness state or discovery behavior.

## Common Pitfalls

### Pitfall 1: Path drift after moving fixtures
**What goes wrong:** Modules like `tests/simulation_logs/parse.py` and `tests/fixtures/simulation/capture.py` hard-code fixture roots and settings paths; moving directories breaks parsing and capture.
**Why it happens:** Fixture paths are computed via `Path(__file__).resolve().parents[...]` in multiple files.
**How to avoid:** Centralize fixture root/manifest/settings path resolution in a single support module and import it everywhere.
**Warning signs:** Failing tests with “file not found” for `metadata.json` or settings profiles.

### Pitfall 2: Duplicate test module names after regrouping
**What goes wrong:** Pytest import mode `prepend` can import modules as top-level and collide if names repeat.
**Why it happens:** With default import mode, test modules must have unique names across the tree.
**How to avoid:** Keep unique test file names or add `__init__.py` to package tests; optionally configure `--import-mode=importlib`.
**Warning signs:** Tests imported twice or unexpected `ImportError`/shadowed modules.

### Pitfall 3: Fixture regeneration policy ambiguity
**What goes wrong:** Fixtures are regenerated accidentally and break baseline expectations; or never refreshed when needed.
**Why it happens:** Regeneration is currently toggled via `OT2_REFRESH_SIM_FIXTURES`, but policy is undocumented.
**How to avoid:** Document a fixture update workflow and keep regeneration opt-in.
**Warning signs:** CI diffs in fixture logs without source changes.

## Code Examples

Verified patterns from official sources:

### Shared fixtures in conftest
```python
# Source: https://docs.pytest.org/en/stable/how-to/fixtures.html
import pytest

@pytest.fixture(scope="module")
def smtp_connection():
    return "resource"

def test_uses_fixture(smtp_connection):
    assert smtp_connection == "resource"
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Default `prepend` import mode | `importlib` import mode recommended for new projects | Documented in pytest Good Integration Practices | Avoids module name collisions and `sys.path` surprises during refactors. |

**Deprecated/outdated:**
- `python setup.py test`: pytest docs advise against setuptools-based test commands.

## Open Questions

1. **Fixture naming convention**
   - What we know: Fixtures are keyed by `fixture_id` in `manifest.json` today.
   - What's unclear: Whether to enforce `<scenario>-<mode>` naming across all domains.
   - Recommendation: Standardize on `<scenario>-<mode>` to preserve current readability.

2. **Fixture update policy**
   - What we know: Regeneration is controlled by `OT2_REFRESH_SIM_FIXTURES` in `test_simulation_log_fixtures.py`.
   - What's unclear: Whether to allow automatic regeneration in CI.
   - Recommendation: Keep fixtures frozen; allow manual refresh only via env var and a documented local workflow.

3. **Import mode choice**
   - What we know: pytest recommends importlib for new projects; repo currently uses default mode.
   - What's unclear: Whether changing import mode is acceptable in this refactor.
   - Recommendation: Prefer unique module names and retain current mode unless the planner opts in to importlib.

## Sources

### Primary (HIGH confidence)
- https://docs.pytest.org/en/stable/how-to/fixtures.html - fixture usage, scopes, and conftest patterns
- https://docs.pytest.org/en/stable/explanation/goodpractices.html - test layout, discovery, import mode guidance
- `tests/fixtures/simulation/capture.py` - simulation fixture capture flow and settings profile swap
- `tests/simulation_logs/parse.py` - fixture root and settings root usage
- `tests/fixtures/simulation/manifest.json` - fixture manifest schema
- `pyproject.toml` - pytest and test dependency versions

### Secondary (MEDIUM confidence)
- https://docs.pytest.org/en/stable/reference/reference.html#mark - pytest markers reference

### Tertiary (LOW confidence)
- None

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - repo pins pytest and supporting test dependencies.
- Architecture: MEDIUM - based on repo structure plus pytest guidance; some layout choices are discretionary.
- Pitfalls: MEDIUM - derived from current path coupling and pytest import behavior.

**Research date:** 2026-01-27
**Valid until:** 2026-02-26
