# Features Research: File Selector Dropdown UX

**Domain:** File selector dropdown for CSV files in desktop/web application
**Researched:** 2026-01-20
**Overall Confidence:** HIGH (well-documented UX patterns)

## Executive Summary

File selector dropdowns are a mature UI pattern with well-established best practices. The user's planned behaviors align well with industry standards. Key considerations are keyboard accessibility, clear state communication, and preventing data loss from accidental selections.

---

## Table Stakes

Features users expect. Missing = product feels broken.

| Feature | Why Expected | Source |
|---------|--------------|--------|
| **Keyboard navigation** | Arrow keys to move, Enter to select, Escape to close | [W3C ARIA APG](https://www.w3.org/WAI/ARIA/apg/patterns/combobox/) |
| **Clear visual state** | Open/closed/selected states must be obvious via caret, border, or color | [Eleken](https://www.eleken.co/blog-posts/dropdown-menu-ui) |
| **Persistent label** | "Select CSV file" label always visible, not just placeholder | [Baymard](https://baymard.com/blog/drop-down-usability) |
| **Loading indication** | Spinner or feedback when file list is refreshing | [UX Planet](https://uxplanet.org/pull-to-refresh-ui-pattern-42a85f671cdf) |
| **Empty state message** | Clear explanation when no files available, not just disabled | [NN/g](https://www.nngroup.com/articles/empty-state-interface-design/) |
| **Screen reader support** | ARIA roles, label announcement, state changes | [W3C ARIA APG](https://www.w3.org/WAI/ARIA/apg/patterns/combobox/examples/combobox-select-only/) |

### Why These Are Non-Negotiable

1. **Keyboard navigation** - Required for accessibility (WCAG 2.1 AA compliance). Users expect arrow keys to work in any dropdown.

2. **Clear visual state** - Users must instantly know: Is dropdown open? What's selected? Is it disabled? Ambiguity causes hesitation.

3. **Empty state message** - A disabled dropdown with no explanation leaves users confused. "No CSV files found in directory" is essential.

---

## Differentiators

Features that elevate UX. Not expected, but appreciated.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| **Filename preview truncation** | Show full name on hover when truncated | Low | Prevents hidden information |
| **Recently selected indicator** | Visual marker on last-used file | Low | Speeds repeat tasks |
| **File metadata tooltip** | Show file size, date modified on hover | Medium | Helps identify correct file |
| **Type-ahead filtering** | Start typing to filter list | Medium | Essential if >10 files |
| **Alphabetical + recent sort** | Recent first, then alphabetical | Low | Best of both worlds |
| **Graceful path display** | Show just filename, full path in tooltip | Low | Reduces visual clutter |

### Recommended Differentiators for This Project

Given the context (CSV files for protocol generation), prioritize:

1. **File metadata tooltip** - Scientists often have multiple similar CSVs. Date modified helps identify the right one.

2. **Type-ahead filtering** - If users accumulate many CSVs over time, typing "multi" to find "multi_channel_test.csv" is valuable.

3. **Filename truncation with hover** - Lab filenames are often descriptive and long (e.g., "2026-01-20_384_plate_cherry_pick_v3.csv").

---

## Anti-Features

Things to explicitly NOT build. Common mistakes in this domain.

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| **Auto-load on page refresh** | Loses user's unsaved work silently | Keep current selection, require explicit action |
| **Remove items instead of disable** | Breaks spatial memory, confuses users | Gray out unavailable options, show why disabled |
| **Generic "Error" message** | User can't fix what they don't understand | Specific: "Directory not found: /path/to/CSVs" |
| **Silent refresh** | User doesn't know list updated | Show refresh indicator, toast notification |
| **Confirm dialog for every selection** | Adds friction to common action | Only confirm when unsaved changes exist |
| **Alphabetical-only sort** | Hides most relevant (recent) files | Recent-first or configurable sort |
| **Force selection on open** | User might just be exploring options | Allow opening dropdown without selecting |
| **Long dropdown (>25 items)** | Overwhelming, hard to scan | Add search/filter for long lists |

### Critical Anti-Patterns to Avoid

**WCAG 3.2.2 "On Input" Violation:**
> "Changing the setting of any user interface component does not automatically cause a change of context unless the user has been advised of the behaviour before using the component."

Your planned "immediate load on selection" is acceptable IF:
1. User is informed that selection loads the file (e.g., label says "Load CSV")
2. The action is reversible (user can select another file)
3. Unsaved changes warning protects data loss

**Do NOT:** Load file AND navigate away, or load file AND close modal, without warning.

---

## Validation: User's Planned Behaviors

| Planned Behavior | Best Practice Alignment | Verdict |
|------------------|------------------------|---------|
| **Immediate load on selection** | Acceptable for low-risk, reversible actions | GOOD - but add unsaved changes check |
| **Manual refresh button** | Better than auto-refresh for non-chronological lists | GOOD |
| **Unsaved changes warning** | Essential for data loss prevention | GOOD - use specific button labels |
| **First file auto-selected on startup** | Debatable - placeholder might be better | NEEDS REVIEW |
| **Disabled + message when empty** | Correct pattern - show WHY disabled | GOOD |

### Detailed Validation

#### 1. Immediate Load on Selection - APPROVED

**Sources agree:** For simple, reversible actions in single-select dropdowns, immediate action is appropriate. Confirm buttons add unnecessary friction.

**Condition:** Must have unsaved changes protection. Your planned "unsaved changes warning" satisfies this.

**Reference:** [UXPin Dropdown Patterns](https://www.uxpin.com/studio/blog/dropdown-interaction-patterns-a-complete-guide/)

#### 2. Manual Refresh Button - APPROVED

**Sources agree:** Visible refresh button is more intuitive than hidden mechanisms for non-chronological lists.

> "A visible refresh button is easier to implement for developer and to use for user (since it's always visible and available)."

**Recommendation:** Place refresh icon next to dropdown (not inside). Show spinner during refresh.

**Reference:** [UX Planet - Pull to Refresh](https://uxplanet.org/pull-to-refresh-ui-pattern-42a85f671cdf)

#### 3. Unsaved Changes Warning - APPROVED

**Sources agree:** Essential for preventing data loss.

**Best practices to follow:**
- Only show when actual changes exist (don't add friction unnecessarily)
- Use specific button labels: "Discard changes" / "Keep editing" (not "Yes/No")
- Primary button should be the safe action (Keep editing)
- Be consistent - always warn when unsaved changes exist

**Reference:** [Cloudscape Design System](https://cloudscape.design/patterns/general/unsaved-changes/)

#### 4. First File Auto-Selected on Startup - NEEDS CONSIDERATION

**Sources diverge:** Native `<select>` defaults to first item, but UX guidance often recommends placeholder instead.

**Arguments for auto-selecting first file:**
- Reduces clicks for users who want the first file
- Maintains state between sessions (if persisted)
- Clear visual that system is ready

**Arguments for placeholder ("Select a CSV file..."):**
- Forces explicit user action
- Prevents accidental loading of wrong file
- Clearer that no file is currently active

**Recommendation:** Given that loading a file is reversible and your unsaved changes protection exists, auto-selecting first file is acceptable. However, consider:
- Persist last selection across sessions (better than always first)
- Show a clear "No file loaded" initial state if you prefer explicit action

#### 5. Disabled + Message When Empty - APPROVED

**Sources agree:** Disabled without explanation is frustrating.

**Best practice:**
- Disable the dropdown
- Show message: "No CSV files found in CSVs/ directory"
- Optionally: Provide action ("Create CSV" button or "Open folder" link)

**Reference:** [Smashing Magazine - Hidden vs Disabled](https://www.smashingmagazine.com/2024/05/hidden-vs-disabled-ux/)

---

## Implementation Recommendations

### Required for Minimum Viable UX

1. **Keyboard support:** Arrow keys navigate, Enter selects, Escape closes
2. **Visual states:** Distinct styling for default, hover, selected, disabled
3. **Empty state:** Disabled dropdown + explanatory message
4. **Unsaved warning:** Modal with "Discard changes" / "Keep editing" buttons
5. **Loading state:** Spinner during refresh, disabled during load

### Recommended Enhancements

1. **Persist last selection** in localStorage/sessionStorage
2. **Truncate long filenames** with ellipsis, show full name on hover
3. **Sort by modified date** (newest first) by default
4. **Add type-ahead** if file list exceeds 10 items

### Accessibility Checklist

- [ ] `aria-label` on dropdown: "Select CSV file to load"
- [ ] `aria-expanded` attribute reflects open/closed state
- [ ] `aria-activedescendant` tracks focused option
- [ ] Disabled state communicated via `aria-disabled`
- [ ] Empty state message has `role="status"` for screen readers

---

## Sources

**Primary (HIGH confidence):**
- [W3C ARIA APG - Combobox Pattern](https://www.w3.org/WAI/ARIA/apg/patterns/combobox/)
- [W3C ARIA APG - Select-Only Combobox](https://www.w3.org/WAI/ARIA/apg/patterns/combobox/examples/combobox-select-only/)
- [NN/g - Dropdown Design Guidelines](https://www.nngroup.com/articles/drop-down-menus/)
- [NN/g - Empty State Interface Design](https://www.nngroup.com/articles/empty-state-interface-design/)
- [NN/g - Confirmation Dialogs](https://www.nngroup.com/articles/confirmation-dialog/)

**Secondary (MEDIUM confidence):**
- [Baymard Institute - Dropdown Usability](https://baymard.com/blog/drop-down-usability)
- [Cloudscape Design System - Unsaved Changes](https://cloudscape.design/patterns/general/unsaved-changes/)
- [UXPin - Dropdown Interaction Patterns](https://www.uxpin.com/studio/blog/dropdown-interaction-patterns-a-complete-guide/)
- [Smashing Magazine - Hidden vs Disabled UX](https://www.smashingmagazine.com/2024/05/hidden-vs-disabled-ux/)

**Tertiary (supporting):**
- [Eleken - Dropdown Menu UI Best Practices](https://www.eleken.co/blog-posts/dropdown-menu-ui)
- [UX Planet - Pull to Refresh Pattern](https://uxplanet.org/pull-to-refresh-ui-pattern-42a85f671cdf)
- [Carbon Design System - Empty States](https://carbondesignsystem.com/patterns/empty-states-pattern/)
