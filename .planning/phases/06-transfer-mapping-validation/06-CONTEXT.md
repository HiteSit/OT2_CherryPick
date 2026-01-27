# Phase 6: Transfer Mapping Validation - Context

**Gathered:** 2026-01-27
**Status:** Ready for planning

<domain>
## Phase Boundary

Validate expected CSV transfers against parsed simulator events with mode-aware expectations (single, multi, multi_X1). Focus is on transfer matching and ordering logic only; new capabilities beyond transfer mapping validation are out of scope.

</domain>

<decisions>
## Implementation Decisions

### Match strictness
- A CSV transfer matches only when labware, well, and volume all match.
- Volume matching is exact (no tolerance); mapping must still account for pipette-driven volume splitting and air gap behavior when correlating events.
- Every CSV transfer must match; missing transfers are failures.

### Event aggregation
- Validation requires paired aspirate + dispense events for a transfer (not dispense-only).

### Ordering expectations
- Enforce strict global CSV order for transfer matching.

### Multi-channel expansion
- Multi-channel mapping rules should be determined from simulator output; research-driven decisions are expected.

### Claude's Discretion
- Whether to fail, warn, or ignore extra simulator transfer events not represented in CSV.
- Whether a CSV transfer can map to multiple events, or multiple CSV rows can map to one event.
- Whether aggregation/splitting can cross tips/channels vs same tip/channel only.
- Handling of identical repeated transfers (position-specific vs interchangeable).
- Whether multi mode uses different ordering expectations than single/multi_X1, based on simulator output.
- Multi and multi_X1 expansion details (column expansion rules, row-letter acceptance, grouped vs 8 explicit expectations) based on simulator output.

</decisions>

<specifics>
## Specific Ideas

- Mapping must handle pipette volume splitting and air gap logic when a requested volume exceeds pipette capacity; still enforce exact CSV volume at the expectation level.
- Ensure transfer mapping handles simulator behaviors like home/distribution logic correctly during matching.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 06-transfer-mapping-validation*
*Context gathered: 2026-01-27*
