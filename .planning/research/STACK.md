# Stack Research

**Domain:** Simulation log parsing + test verification for OT2 CherryPick
**Researched:** 2026-01-24
**Confidence:** MEDIUM

## Recommended Stack

### Core Technologies

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| Python | 3.12.x | Runtime for parsing + tests | Matches current project baseline and Opentrons tooling requirements. |
| Pydantic | 2.12.5 | Typed log/event models + validation | Produces strict, inspectable log schemas that align with FastAPI/FastMCP conventions and makes parsing errors explicit. |
| pytest | 8.4.2 | Test runner for parsing + workflow verification | Already in use; supports plugin ecosystem for snapshot/regression testing. |

### Supporting Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pytest-regressions | 2.9.1 | Snapshot/regression checks for parsed log artifacts | Use for golden JSON/YAML artifacts from simulation parsing to lock expected outputs. |
| pytest-mock | 3.15.1 | Mocking subprocess + file IO | Use to stub `opentrons_simulate` calls and file system writes without hitting the robot stack. |

### Development Tools

| Tool | Purpose | Notes |
|------|---------|-------|
| uv | Dependency + venv management | Keep using `uv run` for simulations/tests; add new libs with `uv add`. |
| opentrons_simulate | Ground-truth simulator output | Capture stdout/stderr for parsing; treat as external system boundary in tests. |

## Installation

```bash
# Core
uv add "pydantic>=2.12.5,<3"

# Supporting
uv add --optional dev "pytest-regressions>=2.9.1,<3" "pytest-mock>=3.15.1,<4"
```

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| Pydantic | attrs + cattrs | Use if you want lighter-weight models and are willing to manage validation rules manually. |
| pytest-regressions | syrupy | Use if you prefer snapshot diffs tied to pytest assertions rather than data-regression fixtures. |

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| Heavy parser generators (pyparsing, lark) | Opentrons logs are line-oriented; a full grammar adds maintenance burden. | stdlib `re` + Pydantic models. |
| Raw text golden files without normalization | Minor formatting/log order changes create noisy diffs. | pytest-regressions with normalized JSON/YAML output. |

## Stack Patterns by Variant

**If parsing remains line-oriented stdout/stderr:**
- Use stdlib `re` + Pydantic models
- Because the log format is stable enough for regex capture + validation

**If Opentrons adds structured JSON logs later:**
- Keep Pydantic models but swap parser to direct JSON load
- Because regression fixtures stay the same while parser changes

## Version Compatibility

| Package A | Compatible With | Notes |
|-----------|-----------------|-------|
| pydantic@2.12.5 | Python 3.12 | Matches project runtime; FastAPI already aligns with Pydantic v2. |
| pytest-regressions@2.9.1 | pytest 8.x | Requires Python >=3.10; compatible with existing pytest version. |
| pytest-mock@3.15.1 | pytest 8.x | Thin wrapper; no additional runtime deps. |

## Sources

- https://pypi.org/project/pydantic/ — latest version + release date (HIGH)
- https://pypi.org/project/pytest-regressions/ — latest version + release date (HIGH)
- https://pypi.org/project/pytest-mock/ — latest version + release date (HIGH)

---
*Stack research for: simulation log parsing + test verification*
*Researched: 2026-01-24*
