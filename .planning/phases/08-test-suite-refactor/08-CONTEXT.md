# Phase 8: Test Suite Refactor - Context

**Gathered:** 2026-01-27
**Status:** Ready for planning

<domain>
## Phase Boundary

Reorganize the test suite structure and fixtures, and expose shared utilities for log
capture, parser setup, and fixture normalization. No new validation logic or behaviors
are added in this phase.

</domain>

<decisions>
## Implementation Decisions

### Directory layout
- Group tests by feature domain rather than pipeline stage.
- Co-locate simulation log fixtures with the suites that use them.
- Separate unit and integration tests into top-level folders.

### Fixture organization
- One fixture set per CSV scenario.
- Store both raw simulator logs and normalized artifacts in fixtures.

### Cleanup strategy
- Refactor can move and rename files; remove obsolete items when needed.
- No compatibility shims; update all references.
- Remove old paths immediately in this phase.
- Prefer clarity even if churn is higher.

### Claude's Discretion
- Where parser/adapter-focused tests live within the feature-domain structure.
- Fixture naming convention.
- Fixture update policy (frozen vs regeneration workflow).
- Shared utilities scope, organization, defaults, and stability level.

</decisions>

<specifics>
## Specific Ideas

No specific requirements — open to standard approaches.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 08-test-suite-refactor*
*Context gathered: 2026-01-27*
