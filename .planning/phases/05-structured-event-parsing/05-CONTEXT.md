# Phase 5: Structured Event Parsing - Context

**Gathered:** 2026-01-26
**Status:** Ready for planning

<domain>
## Phase Boundary

Parse simulation logs into normalized, version-aware event models so tests can consume consistent events for labware load, tip pickup/drop, and liquid handling actions.

</domain>

<decisions>
## Implementation Decisions

### Event model scope
- Normalize core liquid handling events only: labware load, tip pickup/drop, aspirate, dispense.
- Include mix as a first-class event in Phase 5.
- Aspirate/dispense should default to a single normalized action, but validate against CSV layout during research to confirm whether substep splitting is needed.

### Normalization fields
- Require full identifiers on every event (labware id + slot + pipette id; include tiprack when relevant).
- Normalize volumes to a single numeric value in microliters.
- Do not include timestamps; use sequence order only.

### Log source coverage
- Treat combined stdout + stderr as the authoritative input stream.

### Claude's Discretion
- Whether to model aspirate/dispense as substeps if research finds CSV layout requires it.
- Whether to expose blow out/touch tip as separate events in Phase 5.
- How strict to be when required fields are missing (error vs null).
- Whether to prefer JSON logs when available.
- How to handle unknown log lines (error vs warn/skip).
- Whether to normalize field names across simulator versions.

</decisions>

<specifics>
## Specific Ideas

- Single normalized aspirate/dispense is preferred unless CSV layout dictates substep handling; confirm in research.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 05-structured-event-parsing*
*Context gathered: 2026-01-26*
