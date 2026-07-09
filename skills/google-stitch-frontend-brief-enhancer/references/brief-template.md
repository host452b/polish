# Frontend Implementation Brief Template

Replace bracketed guidance with known information. Keep unknowns explicit; omit irrelevant categories.

```markdown
# Frontend Brief: [Surface or Feature]

## Original Request

> [Preserve the user's wording]

## Outcome

[What should become easier, clearer, faster, or more trustworthy for the user?]

## Decision Status

### Confirmed Requirements

- [User-provided fact or repository-backed constraint]

### Reversible Assumptions

- [Recommended default] — rationale and how to change it later

### Unresolved Decisions

- [Question whose answer materially changes behavior, scope, content, or brand]

## Context and Constraints

- Audience: [confirmed or unknown]
- Platform and stack: [evidence]
- Existing design contract: [path or none]
- Existing components to reuse: [paths or unknown]
- Content and data constraints: [real sources and prohibited invention]
- Out of scope: [explicit boundary]

## Information Architecture

1. **[Region]:** purpose, content hierarchy, and primary action.

Explain reading order and why each region exists. Do not add regions solely to fill a template.

## Component Contract

| Component | Purpose | Variants | Relevant states | Existing source |
| --- | --- | --- | --- | --- |

Consider default, hover, focus-visible, active, selected, disabled, loading, empty, validation, error, success, and partial-data states only where meaningful.

## Visual Direction

- Atmosphere and hierarchy: [observable description]
- Color roles: [existing tokens or labeled proposal]
- Typography: [existing tokens or unresolved]
- Spacing and shape: [system rules]
- Elevation and imagery: [purpose and constraints]

## Responsive Behavior

| Width or condition | Required behavior |
| --- | --- |

Specify ordering, collapse, overflow, navigation, target size, and content priority—not merely “responsive.”

## Accessibility

- Keyboard path and focus visibility: [requirements]
- Accessible names and relationships: [requirements]
- Contrast and non-color cues: [requirements]
- Target size and error communication: [requirements]
- Reduced-motion behavior: [requirements]

## Motion and Feedback

[What changes, why motion helps, bounded duration, animated properties, and fallback.]

## Content Integrity

- Approved copy/data sources: [sources]
- Placeholders: [explicit labels]
- Claims, metrics, customers, and capabilities must not be invented.

## Acceptance Criteria

- [ ] At `[viewport/condition]`, `[element]` changes to `[observable result]`.
- [ ] Keyboard users can `[task]` in `[order]` with visible focus.
- [ ] Every applicable state in the component contract is implemented and distinguishable.
- [ ] Existing `[behavior/data contract]` remains unchanged.
- [ ] All colors, type, spacing, and radii use `[existing or approved token source]`.
- [ ] No unapproved product facts or content appear.

## Handoff

- Files or surfaces expected to change: [known paths or discovery task]
- Required verification: [typecheck, tests, visual viewports, accessibility checks]
- Decisions still blocking implementation: [items or none]
```
