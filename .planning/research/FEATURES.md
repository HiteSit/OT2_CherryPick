# Feature Research

**Domain:** Simulation log parsing + pytest test refactor for OT-2 CherryPick
**Researched:** 2026-01-24
**Confidence:** MEDIUM (limited official guidance on simulator log format; parser behavior inferred from common testing patterns)

## Feature Landscape

### Table Stakes (Users Expect These)

Features users assume exist. Missing these = product feels incomplete.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Capture `opentrons_simulate` stdout/stderr in tests | Baseline for any simulation-based validation | MEDIUM | Depends on existing simulation runner; needs stable test fixtures. |
| Parse run log into structured events | Raw logs are too noisy for reliable assertions | MEDIUM | Map actions like load labware, pick up tip, aspirate, dispense, drop tip. |
| Validate transfer mapping vs CSV | Core correctness signal for cherry-pick workflows | HIGH | Requires aligning CSV rows with simulated actions (mode-aware). |
| Detect simulation errors/warnings | Users expect tests to fail on invalid configurations | LOW | Treat stderr/errors as test failures; capture warnings separately. |
| Version-tolerant parsing | Opentrons docs warn run log format can change | MEDIUM | Prefer pattern-based parsing and semantic checks over full-string matching. |

### Differentiators (Competitive Advantage)

Features that set the product apart. Not required, but valuable.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Semantic diff report for failures | Faster diagnosis than raw log dumps | MEDIUM | Summaries like “expected 96 transfers, saw 94” with context. |
| Action coverage metrics | Quantifies how much of CSV is validated by simulation logs | MEDIUM | Helps teams trust tests as they scale protocols. |
| Mode-aware assertions (single/multi/multi_X1) | Prevents false positives for multi-channel runs | HIGH | Needs encoding of per-mode expectations. |
| Pipette behavior checks (tip reuse, mix, air gap) | Validates liquid handling policies, not just transfers | HIGH | Requires deeper parsing of action sequencing. |
| Log format adapters by API level | Reduces breakage when Opentrons updates log phrasing | HIGH | Adapter map keyed by API level or simulator version. |

### Anti-Features (Commonly Requested, Often Problematic)

Features that seem good but create problems.

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Full log snapshot diffing | Easy to implement, feels comprehensive | Extremely brittle to wording changes | Parse into structured events and assert semantics only. |
| Auto-fixing CSV/TOML on test failure | Convenience for users | Hides real problems and masks regressions | Emit actionable diagnostics and require explicit edits. |
| Dependence on undocumented log phrasing | Quick regex wins | Breaks with simulator updates; hard to debug | Pattern libraries with fallback handling + version gates. |

## Feature Dependencies

```
[Simulation runner integration]
    └──requires──> [Log capture in tests]
                       └──requires──> [Structured log parser]
                                          └──requires──> [Transfer mapping assertions]

[Expected transfer model from CSV/TOML] ──enhances──> [Transfer mapping assertions]

[Mode-aware expectations] ──enhances──> [Transfer mapping assertions]
```

### Dependency Notes

- **Structured log parser requires log capture:** parsing only works if tests capture stdout/stderr deterministically.
- **Transfer mapping assertions require expected model:** must compute expected actions from CSV + settings first.
- **Mode-aware expectations enhance assertions:** without mode context, multi-channel logs are misinterpreted.

## MVP Definition

### Launch With (v1)

Minimum viable product — what's needed to validate the concept.

- [ ] Log capture in pytest fixtures — foundational for any parsing.
- [ ] Structured parser for key actions — pick up tip, aspirate, dispense, drop tip.
- [ ] CSV-to-action expectation builder — aligns CSV rows to simulated actions.
- [ ] Clear failure messages — highlight first mismatched transfer with context.

### Add After Validation (v1.x)

Features to add once core is working.

- [ ] Mode-aware assertions — only after mode handling is stable.
- [ ] Tip reuse and mixing policy checks — once event model is reliable.

### Future Consideration (v2+)

Features to defer until product-market fit is established.

- [ ] API-level log adapters — only needed if simulator output drifts frequently.
- [ ] Coverage metrics dashboards — valuable but not required for correctness.

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| Log capture in tests | HIGH | MEDIUM | P1 |
| Structured log parser | HIGH | MEDIUM | P1 |
| CSV-to-action expectation builder | HIGH | HIGH | P1 |
| Mode-aware assertions | HIGH | HIGH | P2 |
| Failure report summarization | MEDIUM | MEDIUM | P2 |
| Tip/mix policy checks | MEDIUM | HIGH | P2 |
| Log adapters by API level | MEDIUM | HIGH | P3 |

**Priority key:**
- P1: Must have for launch
- P2: Should have, add when possible
- P3: Nice to have, future consideration

## Competitor Feature Analysis

| Feature | Competitor A | Competitor B | Our Approach |
|---------|--------------|--------------|--------------|
| Run log visibility | Opentrons App run log (human readable) | `opentrons_simulate` CLI output | Parse to structured events and assert semantics. |
| Protocol validation feedback | App-level warnings/errors | CLI exit codes + stderr | Fail tests with precise, CSV-linked diagnostics. |
| Transfer verification | Manual review of log | Manual review of log | Automated checks against CSV expectations. |

## Sources

- https://docs.opentrons.com/v2/new_protocol_api.html (ProtocolContext.commands run log notes; format not guaranteed) — MEDIUM
- https://docs.opentrons.com/v2/new_protocol_api.html#opentrons.protocol_api.ProtocolContext.commands — MEDIUM
- No official docs found for `opentrons_simulate` log line format (flag for validation)

---
*Feature research for: simulation log parsing + test refactor*
*Researched: 2026-01-24*
