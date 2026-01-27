# Roadmap: OT2 CherryPick GUI Enhancement

## Overview

The project now focuses on validating OT-2 simulation behavior by turning simulator output into structured, testable evidence. v2.0 introduces a log capture and parsing pipeline that lets tests prove CSV-driven transfers, liquid handling policies, and mode behavior match intent.

## Milestones

- ✅ **v1.0 CSV File Selector** - Phases 1-3 (shipped 2026-01-21)
- 📋 **v2.0 Simulation Log Validation** - Phases 4-8 (planned)

## Phases

<details>
<summary>✅ v1.0 CSV File Selector (Phases 1-3) - SHIPPED 2026-01-21</summary>

### Phase 1: Core Selection
**Goal**: Users can select CSV files from a searchable dropdown and see content immediately loaded
**Plans**: 3 plans

Plans:
- [x] 01-01-PLAN.md — File selector with search, clear, refresh, and immediate content loading

### Phase 2: Data Safety
**Goal**: Users are protected from accidentally losing unsaved changes when switching files
**Plans**: 1 plan

Plans:
- [x] 02-01-PLAN.md — Dirty state detection and UnsavedChangesModal with Discard/Cancel actions

### Phase 3: Polish
**Goal**: Empty state handled gracefully with appropriate user feedback
**Plans**: 1 plan

Plans:
- [x] 03-01-PLAN.md — Empty state detection with disabled dropdown and emphasized upload button

</details>

### 📋 v2.0 Simulation Log Validation (Planned)

**Milestone Goal:** Tests can prove CSV-driven OT-2 transfers match simulator behavior, with structured logs, mode-aware expectations, and actionable diagnostics.

#### Phase 4: Log Capture Baseline
**Goal**: Simulation output is captured as reusable fixtures and failures surface simulator errors clearly
**Depends on**: Phase 3
**Requirements**: LOG-01, DIAG-01
**Success Criteria** (what must be TRUE):
  1. Test runner captures `opentrons_simulate` stdout/stderr into fixtures that are reused for repeatable validation runs
  2. Simulation warnings or errors fail tests with clear context pointing to the offending log output
**Plans**: 1 plan

Plans:
- [x] 04-01-PLAN.md — Capture simulation logs as reusable fixtures
- [x] 04-02-PLAN.md — Capture baseline simulation fixtures (core set)
- [x] 04-03-PLAN.md — Capture baseline simulation fixtures (remaining set)

#### Phase 5: Structured Event Parsing
**Goal**: Simulation logs are parsed into normalized, version-aware event models for downstream assertions
**Depends on**: Phase 4
**Requirements**: PARSE-01, COMP-01
**Success Criteria** (what must be TRUE):
  1. Test suite can load a simulation log and expose structured events for labware load, pick up tip, aspirate, dispense, and drop tip actions
  2. Parser selects the correct log adapter based on simulator/API version so tests parse multiple versions consistently
**Plans**: 2 plans

Plans:
- [x] 05-01-PLAN.md — Define raw event models and v8.7.0 log adapter
- [x] 05-02-PLAN.md — Normalize events and add versioned parsing entrypoint

#### Phase 6: Transfer Mapping Validation
**Goal**: Expected CSV transfers are validated against parsed events with mode-aware expectations
**Depends on**: Phase 5
**Requirements**: MAP-01, MODE-01
**Success Criteria** (what must be TRUE):
  1. Tests compare expected CSV transfers to parsed events and pass only when the simulator executed matching transfers
  2. Expectations adjust correctly for single, multi, and multi_X1 runs so multi-channel transfers validate by column behavior
**Plans**: 2 plans

Plans:
- [x] 06-01-PLAN.md — Build CSV expectations (mode + distribution aware)
- [x] 06-02-PLAN.md — Match expectations to simulator events with diagnostics

#### Phase 7: Diagnostics + Policy Checks
**Goal**: Validation failures provide semantic diagnostics and cover liquid handling policy rules
**Depends on**: Phase 6
**Requirements**: DIAG-02, DIAG-03, POL-01
**Success Criteria** (what must be TRUE):
  1. Failed tests summarize expected vs observed transfers in a semantic failure report
  2. Test output reports coverage metrics for which CSV actions were validated
  3. Tests confirm tip reuse, mix, and air gap behaviors match settings/CSV intent
**Plans**: 2 plans

Plans:
- [x] 07-01-PLAN.md — Add semantic transfer diagnostics + CSV row coverage metrics
- [x] 07-02-PLAN.md — Add tip reuse, mix, and air gap policy checks with evidence gating

#### Phase 8: Test Suite Refactor
**Goal**: Test suite structure is reorganized and hardened after core validation work
**Depends on**: Phase 7
**Requirements**: REF-01
**Success Criteria** (what must be TRUE):
  1. Test directories and fixtures are reorganized so simulation log fixtures and parsers live in clear, reusable locations
  2. Test harness exposes shared utilities for log capture, parser setup, and fixture normalization
**Plans**: 7 plans

Plans:
- [ ] 08-01-PLAN.md — Add shared support utilities for fixture paths and capture
- [ ] 08-02-PLAN.md — Move simulation fixtures and capture tests into integration suite
- [ ] 08-03-PLAN.md — Add shared parser setup and fixture normalization helpers
- [ ] 08-04-PLAN.md — Move core parsing modules and adapters into unit package
- [ ] 08-05-PLAN.md — Move matching/diagnostics/expectations/policies into unit package
- [ ] 08-06-PLAN.md — Move simulation log tests into unit/simulation_logs
- [ ] 08-07-PLAN.md — Move transfer mapping tests into unit/transfer_mapping

## Progress

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1. Core Selection | v1.0 | 1/1 | Complete | 2026-01-20 |
| 2. Data Safety | v1.0 | 1/1 | Complete | 2026-01-20 |
| 3. Polish | v1.0 | 1/1 | Complete | 2026-01-21 |
| 4. Log Capture Baseline | v2.0 | 3/3 | Complete | 2026-01-26 |
| 5. Structured Event Parsing | v2.0 | 2/2 | Complete | 2026-01-27 |
| 6. Transfer Mapping Validation | v2.0 | 2/2 | Complete | 2026-01-27 |
| 7. Diagnostics + Policy Checks | v2.0 | 2/2 | Complete | 2026-01-27 |
| 8. Test Suite Refactor | v2.0 | 0/7 | Not started | - |

---
*Roadmap created: 2026-01-20*
*Last updated: 2026-01-27 - Phase 7 diagnostics + policy checks completed*
