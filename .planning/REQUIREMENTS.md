# Requirements: OT2 CherryPick GUI Enhancement

**Defined:** 2026-01-24
**Core Value:** Users can select CSV files from a dropdown and immediately see the content loaded in the editor views — no manual path typing, no guessing filenames, with protection against accidental data loss.

## v2.0 Requirements

Requirements for the Simulation Log Validation milestone. Each maps to roadmap phases.

### Test Suite Refactor

- [ ] **REF-01**: Test suite reorganizes directories, fixtures, and harnesses to support simulation log validation

### Log Capture

- [x] **LOG-01**: Test suite captures `opentrons_simulate` stdout/stderr as fixtures for repeatable validation runs

### Parsing

- [x] **PARSE-01**: Test suite parses simulation logs into structured events (labware load, pick up tip, aspirate, dispense, drop tip)

### Transfer Validation

- [x] **MAP-01**: Test suite compares expected transfers from CSV against parsed simulation events

### Mode Handling

- [x] **MODE-01**: Test suite applies mode-aware expectations for single, multi, and multi_X1 runs

### Diagnostics & Reporting

- [x] **DIAG-01**: Simulation errors or warnings cause tests to fail with actionable context
- [ ] **DIAG-02**: Failures summarize expected vs observed transfers (semantic failure report)
- [ ] **DIAG-03**: Test suite reports coverage metrics for validated CSV actions

### Liquid Handling Policies

- [ ] **POL-01**: Test suite validates tip reuse, mix, and air gap behavior against settings/CSV intent

### Compatibility

- [x] **COMP-01**: Test suite supports log adapters keyed by API level or simulator version

## Future Requirements

Deferred beyond v2.0 scope.

### Parsing Stability

- **PARSE-02**: Parser tolerates simulator log format drift without breaking core assertions

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| Full log snapshot diffing | Too brittle to wording changes; prefer semantic assertions |
| Auto-fixing CSV/TOML on test failure | Masks real issues; require explicit edits |
| Dependence on undocumented log phrasing | Breaks on simulator updates; use adapters instead |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| LOG-01 | Phase 4 | Complete |
| DIAG-01 | Phase 4 | Complete |
| PARSE-01 | Phase 5 | Complete |
| COMP-01 | Phase 5 | Complete |
| MAP-01 | Phase 6 | Complete |
| MODE-01 | Phase 6 | Complete |
| DIAG-02 | Phase 7 | Pending |
| DIAG-03 | Phase 7 | Pending |
| POL-01 | Phase 7 | Pending |
| REF-01 | Phase 8 | Pending |

**Coverage:**
- v2.0 requirements: 10 total
- Mapped to phases: 10
- Unmapped: 0

---
*Requirements defined: 2026-01-24*
*Last updated: 2026-01-27 after Phase 5 verification*
