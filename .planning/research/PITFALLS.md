# Pitfalls Research

**Domain:** OT-2 protocol simulation log parsing and test refactor
**Researched:** 2026-01-24
**Confidence:** MEDIUM

## Critical Pitfalls

### Pitfall 1: Parsing brittle, human-readable log text

**What goes wrong:**
Tests fail whenever opentrons_simulate output changes wording, spacing, or ordering; CI becomes noisy and unreliable.

**Why it happens:**
Developers parse raw stdout with regexes instead of extracting structured events or using stable markers.

**How to avoid:**
Define a minimal, version-tolerant event model (e.g., aspirate/dispense with labware+well+volume), build a parser around stable tokens, and keep a golden set of log fixtures pinned to known opentrons_simulate versions.

**Warning signs:**
Small updates to simulation tooling cause widespread test failures; parsing logic is full of fragile regexes tied to exact phrasing.

**Phase to address:**
Phase 1 (Log inventory + fixture capture) and Phase 2 (Parser design).

---

### Pitfall 2: Assuming one-to-one mapping between CSV rows and log lines

**What goes wrong:**
Tests incorrectly fail for multi-channel or grouped operations because a single CSV row can produce multiple actions or consolidated log lines.

**Why it happens:**
Test design assumes each CSV row equals a single aspirate/dispense pair, ignoring mode-specific semantics.

**How to avoid:**
Define mode-aware expectations (single_X1, multi_X1, multi) and validate semantic outcomes (target wells and volumes) rather than exact line counts.

**Warning signs:**
Tests pass in single mode but fail in multi mode; mismatches cluster around column transfers.

**Phase to address:**
Phase 2 (Expectation model) and Phase 3 (Integration with mode logic).

---

### Pitfall 3: Mixing log parsing with business logic validation

**What goes wrong:**
Tests become a tangled mix of parsing rules and protocol rules, making failures hard to diagnose and refactor.

**Why it happens:**
Parser outputs are not normalized; tests operate on raw tokens instead of a clean semantic model.

**How to avoid:**
Separate parsing into a pure module that emits normalized events, then validate events against CSV intent in a separate layer.

**Warning signs:**
Test failures require stepping through regexes; refactoring protocol behavior breaks parsing in unrelated tests.

**Phase to address:**
Phase 2 (Parser abstraction) and Phase 3 (Test refactor).

---

### Pitfall 4: Relying on unstable ordering in simulation output

**What goes wrong:**
Tests that assert strict ordering fail when the simulator reorders operations (e.g., batching or optimization changes).

**Why it happens:**
Tests check sequences instead of sets or grouped operations where ordering is not meaningful.

**How to avoid:**
Use ordering only where it is required by domain logic (e.g., aspirate before dispense). Otherwise, compare unordered sets or grouped sequences by transfer id.

**Warning signs:**
Intermittent ordering diffs across platforms or opentrons_simulate versions.

**Phase to address:**
Phase 2 (Expectation model) and Phase 3 (Test harness).

---

### Pitfall 5: Test fixtures drift from real protocol generation

**What goes wrong:**
Fixtures no longer reflect current settings.toml, labware definitions, or CSV schemas, so tests pass but do not represent real behavior.

**Why it happens:**
Fixtures are copied once and never regenerated; no linkage to the current helper or MCP workflows.

**How to avoid:**
Add fixture generation scripts (or snapshots) tied to current config, and pin fixture metadata (simulator version, settings snapshot).

**Warning signs:**
Fixture data is not reproducible from current configs; tests do not fail when protocol logic changes.

**Phase to address:**
Phase 1 (Fixture capture) and Phase 4 (CI reproducibility).

---

### Pitfall 6: Overfitting to simulator output instead of intent

**What goes wrong:**
Tests encode simulator quirks instead of verifying CSV intent; refactoring or upgrading sim breaks tests without functional regression.

**Why it happens:**
Test assertions are based on specific log lines or simulator-specific phrases instead of domain-level intent.

**How to avoid:**
Anchor validations to protocol intent (source/dest wells, volumes, tip actions) and treat simulator output as an intermediate signal.

**Warning signs:**
Tests fail when only tooling changes; changes to comments or log formatting cause failures.

**Phase to address:**
Phase 2 (Intent model) and Phase 3 (Test refactor).

---

### Pitfall 7: Ignoring OS/path differences in simulation logs

**What goes wrong:**
Tests fail across Windows/WSL/Linux due to path formats or line endings that the parser assumes.

**Why it happens:**
Parser assumes a single path convention or uses raw substrings without normalization.

**How to avoid:**
Normalize paths and line endings in parser input; treat file path lines as metadata rather than core events.

**Warning signs:**
Tests only pass on one developer machine; CI failures cite mismatched paths.

**Phase to address:**
Phase 1 (Fixture normalization) and Phase 3 (Cross-platform validation).

---

### Pitfall 8: Conflating parsing failures with protocol failures

**What goes wrong:**
Failing parse is reported as a protocol regression, causing wasted debugging time.

**Why it happens:**
Parsing exceptions are not differentiated from validation assertions in test output.

**How to avoid:**
Use separate error classes and test stages (parse -> normalize -> validate) with explicit failure messages.

**Warning signs:**
Test output does not indicate whether parsing or logic failed; failures are hard to triage.

**Phase to address:**
Phase 2 (Parser/test harness design).

## Technical Debt Patterns

Shortcuts that seem reasonable but create long-term problems.

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Hardcode regexes for exact log lines | Fast initial tests | Fragile with simulator updates | Only for one-off debug scripts |
| Store fixtures without simulator version metadata | Quick setup | Hard to reproduce or update | Never |
| Assert exact line counts for transfers | Simple assertions | Breaks on batching/multi-channel | Only in single_X1 tests |
| Skip normalization of units/volumes | Less code | Hidden mismatches when rounding occurs | Only for exploratory prototyping |

## Integration Gotchas

Common mistakes when connecting to external services.

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| opentrons_simulate | Assume output format is stable across versions | Capture simulator version and update fixtures when version changes |
| MCP workflow | Parse logs from different config roots (repo vs gui_state) without noting source | Include config root in fixture metadata and normalize inputs |
| Windows/WSL paths | Treat path lines as parseable actions | Strip or normalize path lines before event parsing |
| Labware resolution | Assume custom labware paths are always present in logs | Validate labware path presence separately from action parsing |

## Performance Traps

Patterns that work at small scale but fail as usage grows.

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Parsing entire log in memory for every test | Slow tests, high RAM | Stream parse or pre-parse to cached events | Dozens of large fixtures |
| Re-running simulator in unit tests | Slow CI and flaky tests | Use captured fixtures for unit tests, simulator only in integration tests | When CI runs multiple suites |
| Excessive deep comparisons of full event lists | Long diffs and slow asserts | Compare hashed summaries or key fields | Large multi-plate runs |

## Security Mistakes

Domain-specific security issues beyond general web security.

| Mistake | Risk | Prevention |
|---------|------|------------|
| Parsing untrusted log input without limits | DoS via huge log files in CI | Enforce size limits and timeouts when parsing |
| Writing logs to shared temp paths | Leakage of internal paths and experiment names | Store fixtures in repo and avoid temp path leaks |
| Shelling out with unvalidated CSV paths in tests | Command injection in CI | Sanitize or use safe subprocess APIs |

## UX Pitfalls

Common user experience mistakes in this domain.

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| Test failures not mapping back to CSV rows | Hard to debug regressions | Include CSV row id or source/dest in assertion messages |
| Overly verbose parse errors | Noise hides the real failure | Provide concise failure summaries with optional verbose mode |
| Expectation diffs too granular | Long diffs, low signal | Summarize by transfer group or action count |

## "Looks Done But Isn't" Checklist

Things that appear complete but are missing critical pieces.

- [ ] **Parser:** Missing versioning metadata for fixtures -- verify simulator version recorded
- [ ] **Tests:** Only single_X1 mode covered -- verify multi and multi_X1 modes
- [ ] **Normalization:** Volumes not rounded consistently -- verify rounding strategy documented
- [ ] **Integration:** Parser only handles repo-root logs -- verify gui_state workflow

## Recovery Strategies

When pitfalls occur despite prevention, how to recover.

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Brittle parsing breaks after simulator update | MEDIUM | Regenerate fixtures, update parser tokens, add version gate |
| Fixture drift | MEDIUM | Recreate fixtures from current configs and backfill metadata |
| Cross-platform failures | LOW | Normalize paths/line endings, rerun tests on target OS |

## Pitfall-to-Phase Mapping

How roadmap phases should address these pitfalls.

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| Brittle parsing | Phase 2 | Tests pass across simulator minor versions |
| CSV-to-log mismapping | Phase 2 | Mode-aware expectation tests for each mode |
| Fixture drift | Phase 1 | Fixture regeneration script + metadata |
| Ordering assumptions | Phase 2 | Assertions tolerate non-essential ordering |
| Cross-platform parsing | Phase 3 | CI run in at least two OS environments |

## Sources

- Project context and existing OT-2 workflow knowledge (no external sources consulted)

---
*Pitfalls research for: OT-2 simulation log parsing and tests*
*Researched: 2026-01-24*
