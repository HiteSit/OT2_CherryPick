# Phase 7: Diagnostics + Policy Checks - Context

**Gathered:** 2026-01-27
**Status:** Ready for planning

<domain>
## Phase Boundary

Add semantic diagnostic reporting, coverage metrics, and automated policy checks for tip reuse, mix, and air gap behavior. This phase improves test feedback and policy validation without adding new protocol capabilities.

</domain>

<decisions>
## Implementation Decisions

### Failure severity
- Policy violations should fail tests.
- When logs lack enough evidence to prove a policy, warn and skip (do not fail).

### Coverage metrics
- Coverage is measured by CSV rows covered (baseline metric).

### Policy checks scope
- Tip reuse should validate the full lifecycle (pickup/drop/return) when the simulator output supports it.
- Mix checks should be as comprehensive as simulator output allows.

### Claude's Discretion
- Diagnostic report format (summary style, grouping, raw excerpts, file output formats).
- Coverage details: distribution row counting, reporting granularity, and whether 100% coverage is required.
- Failure severity nuances: mixed-severity policy handling and explicit exception rules (e.g., CSV intent disables a check).
- Air gap validation strictness (presence vs volume vs rate).
- Whether to include additional liquid-handling policies beyond tip reuse/mix/air gap if they are logged.

</decisions>

<specifics>
## Specific Ideas

- Base policy validation strictness on what opentrons_simulate actually outputs; avoid checks that cannot be evidenced.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 07-diagnostics-policy-checks*
*Context gathered: 2026-01-27*
