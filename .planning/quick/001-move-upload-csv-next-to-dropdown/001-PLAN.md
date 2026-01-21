# Quick Task 001: Move Upload CSV next to dropdown

## Description
Reorganize the CSV Transfer Map panel layout to place the "Upload CSV" FileInput next to the "Select CSV file" dropdown for a cleaner, more tidy UI.

## Tasks

1. **Move FileInput to same row as Select dropdown**
   - Wrap both Select and FileInput in a single Group component
   - Adjust maxWidth of FileInput to fit well (200px)
   - Keep CSV filename TextInput in its own row below

## Files to Modify
- `src/gui/frontend/src/components/wizard/csv/CsvEditor.tsx`

## Expected Outcome
- Row 1: [Select CSV file dropdown] [Upload CSV button] (side by side)
- Row 2: [CSV filename input]
- Row 3: [Add Row] [Remove Row] buttons
