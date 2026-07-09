# Portable DESIGN.md Template

Use this structure for the repository-root `DESIGN.md`. Replace bracketed guidance with evidence; omit unsupported sections rather than inventing content.

```markdown
# Design System: [Product or Repository]

## Audit Scope

- Inspected: `[paths, packages, representative components]`
- Not inspected: `[unavailable or out-of-scope areas]`
- Styling stack: `[frameworks and libraries]`

## Confidence Legend

- **Observed:** directly supported by source.
- **Inferred:** repeated evidence suggests intent; verify before redesign.
- **Unknown:** source does not establish the decision.

## Visual Language

[Observed atmosphere, density, hierarchy, and recurring composition. Cite evidence.]

## Color Tokens

| Role | Canonical token | Value or modes | Evidence | Confidence |
| --- | --- | --- | --- | --- |

### Drift

- `[near-duplicate or one-off value]` — `[where used and recommended treatment]`

## Typography

| Role | Family | Size/scale | Weight | Leading | Evidence |
| --- | --- | --- | --- | --- | --- |

## Spacing, Shape, and Elevation

- Base rhythm: `[observed scale]`
- Container and section spacing: `[rules]`
- Radii: `[control, container, pill roles]`
- Borders and shadows: `[hierarchy and evidence]`

## Components and States

| Component | Variants | States observed | Missing states | Evidence |
| --- | --- | --- | --- | --- |

## Layout and Responsive Behavior

- Grid and containment: `[rules]`
- Breakpoints: `[values and behavior changes]`
- Collapse and reading order: `[rules]`
- Overflow strategy: `[tables, media, dense content]`

## Motion

[Durations, easing, animated properties, purpose, and reduced-motion support.]

## Accessibility-Relevant Styling

[Contrast evidence, focus treatment, target sizes, non-color cues, and known gaps.]

## Inconsistencies and Risks

1. `[conflict]` — evidence, impact, and confidence.

## Implementation Guidance

### Preserve

- `[coherent convention already in use]`

### Normalize

- `[proposed consolidation, clearly separated from current facts]`

### Unknowns Requiring Product or Design Input

- `[decision the source cannot answer]`
```
