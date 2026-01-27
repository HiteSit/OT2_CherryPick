# Phase 6: Transfer Mapping Validation - Research

**Researched:** 2026-01-27
**Domain:** CSV transfer expectations vs parsed simulator events
**Confidence:** MEDIUM

## Summary

Phase 6 needs a matcher that compares CSV-driven transfer expectations to normalized aspirate/dispense events parsed from `opentrons_simulate` logs. Existing fixtures show mode-specific log patterns (single_X1, multi_X1, multi) and special cases (distribution rows, HOME control rows, air gaps). The matcher should operate on normalized events (already enriched with labware_id, slot, pipette_id) and enforce strict CSV order. Because simulator output does not expand multi-channel columns into A-H wells, the multi-mode matcher should treat each CSV row as a single column-level transfer (based on the row label in the CSV), not eight discrete transfers.

Key implementation implication: the matching logic must account for air gap and volume splitting without applying tolerance. Instead, it should derive expected event volumes from CSV + settings (e.g., dispense volume = CSV volume + air gap when air gap is configured) and allow a CSV transfer to map across multiple events when the protocol splits volume or distribution patterns produce multiple dispenses.

## Verified Simulator Output Patterns

### Multi mode (8-channel)
Fixture: `tests/fixtures/simulation/multi-multi/stdout.txt`

- Log includes: `Multi mode: A1 → 8 source wells, A1 → 8 dest wells`
- Aspirate/dispense lines reference only the A-row well (e.g., `A1`, `B1`), not A-H.
- Air gap appears as a separate log line: `Air gap of 30.0 uL`.
- Dispense volume includes air gap (example: CSV volume 30 + air gap 30 → dispense 60).

**Implication:** Do NOT expand multi-mode CSV rows into 8 explicit transfers; match against a single column-level transfer using the row letter given in CSV.

### Multi_X1 mode
Fixture: `tests/fixtures/simulation/basic-multi_x1/stdout.txt`

- Log shows standard aspirate/dispense per CSV row.
- `Configure pipette ... SINGLE layout` appears, but transfers behave like single_X1.

**Implication:** Treat multi_X1 as single-row, no column expansion.

### Distribution rows
Fixture: `tests/fixtures/simulation/distribution-multi/stdout.txt`

- One aspirate for the total volume, followed by multiple dispenses per destination well.
- Distribution volumes are logged individually (equal and geometric patterns), e.g. `[100.0, 50.0, 25.0, 12.5]`.

**Implication:** Expand a CSV distribution row into multiple expected dispense transfers (one per dest well), while allowing a single aspirate event to cover the group.

### HOME control rows
Fixture: `tests/fixtures/simulation/home-control-single_x1/stdout.txt`

- Log includes `Row X: HOME control - Re-homing robot...` and no aspirate/dispense for that row.
- After HOME, a tip drop occurs and the next row must use `Tip Action: new` (enforced by validation).

**Implication:** Skip HOME rows in expectation building; do not expect transfer events for them.

## Expected Transfer Modeling

### CSV parsing rules
- Labware fields are `labware_id_slot` (e.g., `tube_rack_96_1500ul_4`). Split into base `labware_id` and `slot`.
- Distribution rows are detected when `Dest Well` contains `|` OR `Distribution Volume (ul)` is populated (same as validation logic).
- Dest wells for distribution use pipe-delimited list (e.g., `A1|A2|A3`).
- HOME rows are detected when all non-empty columns equal `HOME` (case-insensitive).

### Mode-aware expectations
- `single_X1`: Each CSV row becomes one expected transfer.
- `multi_X1`: Same as `single_X1` (no column expansion).
- `multi`: Each CSV row represents a column-level transfer. Expect only the row/well specified in CSV (do not expand to A-H).

### Air gap handling
- If CSV specifies `Air Gap`, simulator adds a separate `Air gap of X uL` line and dispenses `volume + air_gap`.
- Expected dispense volume should equal `csv_volume + air_gap` (no tolerance), while aspirate volume remains `csv_volume`.

### Volume splitting
- When requested volume exceeds pipette capacity, protocol may split into multiple aspirate/dispense events.
- Matching should allow multiple dispense events to satisfy one expected transfer as long as total volume sums exactly.

## Suggested Structure (Tests)

Recommended module layout:

```
tests/simulation_logs/
  expectations.py   # CSV -> ExpectedTransfer (mode-aware, distribution-aware)
  matching.py       # ExpectedTransfer + events -> MatchResult
  __init__.py        # export new functions
tests/test_transfer_mapping.py
```

Fixtures to exercise behavior:
- `basic-single_x1` (baseline mapping)
- `basic-multi_x1` (single-like behavior)
- `multi-multi` (column-level matching + air gap)
- `distribution-multi` (distribution expansion + shared aspirate)
- `home-control-single_x1` (HOME row ignored)

## Sources

- `tests/fixtures/simulation/multi-multi/stdout.txt`
- `tests/fixtures/simulation/distribution-multi/stdout.txt`
- `tests/fixtures/simulation/basic-multi_x1/stdout.txt`
- `tests/fixtures/simulation/home-control-single_x1/stdout.txt`
- `tests/e2e/configs/*/settings.toml`
- `src/ot2_cherrypick_mcp/core/validation.py` (HOME + distribution detection rules)

## Open Questions

1. How to treat unexpected extra transfer events not represented in CSV (fail, warn, ignore). Left to planner decision per context.
2. Whether split/aggregate matching should be enabled by default for non-distribution rows (recommend: only when needed, driven by volume > pipette capacity).

## Metadata

**Confidence breakdown:**
- Mode-specific behavior: HIGH (fixture-backed)
- Distribution expansion: MEDIUM (fixture-backed, algorithm inferred)
- Volume splitting: LOW (no fixture evidence; protocol behavior inferred)

**Research date:** 2026-01-27
**Valid until:** 2026-02-24
