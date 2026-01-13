# Task Completion Checklist

## After Code Changes

1. **Run simulation** (if protocol-related):
   ```bash
   ./simulate_protocol.sh CSVs/your_file.csv
   ```

2. **Run tests** (if code changes):
   ```bash
   uv run pytest tests/
   ```

3. **Verify no regressions** in existing functionality

## Before Committing (Owner Only)
- Run full test suite
- Verify simulation passes
- Check for sensitive data exposure
- Use conventional commit format

## For Liquid Handling Changes
- Schedule OT-2 dry run before production
- Document dry runs with calibration steps, deck photos, deviations

## Critical Files to Never Edit Manually
- `CherryPick_OT2.py` (embedded JSON section) - always regenerate with helper
- `uv.lock` - managed by uv

## Documentation
- Archive simulation output for review
- Use `projects/<experiment>/` directories for experiment documentation
