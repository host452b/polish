---
name: google-stitch-extract-frontend-design-system
description: Use when an existing frontend repository needs its visual language, design tokens, styling inconsistencies, component patterns, or responsive rules documented directly from source code, including when the application cannot build or run.
---

# Extract Frontend Design System

## Overview

Reverse-engineer the design system from source without requiring a working build. Produce an evidence-backed `DESIGN.md` that another agent can use without rereading the repository.

## Workflow

1. **Map coverage.** Identify frameworks, styling systems, package boundaries, entry points, global styles, theme files, shared components, and representative pages. Record what was inspected and what was unavailable.
2. **Load the relevant reference.** Read only the matching guide: [React/Tailwind](references/react-tailwind.md), [Vue](references/vue.md), [Svelte](references/svelte.md), [Angular](references/angular.md), or [plain CSS/Sass/Less](references/plain-css.md). Use multiple guides only for a mixed stack.
3. **Collect evidence.** Extract declared and actually used colors, type styles, spacing, radii, borders, elevation, breakpoints, layout primitives, imagery, motion, and component states. Cite file paths, selectors, token names, or components.
4. **Normalize carefully.** Separate aliases from duplicates, declared tokens from one-off values, and global rules from component exceptions. Flag near-duplicates and contradictions; do not silently choose a winner.
5. **Explain intent.** Label each conclusion as **Observed**, **Inferred**, or **Unknown**. Infer atmosphere and hierarchy only from repeated evidence. Never invent missing fonts, breakpoints, states, or brand rationale.
6. **Write the contract.** Create or update root-level `DESIGN.md` using [design-md-template.md](references/design-md-template.md). Preserve coherent existing conventions and list proposed normalization separately.
7. **Verify coverage.** Confirm the document covers tokens, typography, components and states, layout, responsiveness, motion, accessibility-relevant styling, inconsistencies, and implementation guidance.

## Quick Reference

| Evidence | What to capture |
| --- | --- |
| Theme/config | canonical token names, aliases, modes |
| Global CSS | resets, variables, base typography, breakpoints |
| Shared components | variants, states, composition rules |
| Representative pages | grid, density, hierarchy, exceptions |
| Inline or arbitrary values | drift, intentional exceptions, migration candidates |

## Common Mistakes

- Running or repairing the application when source inspection is sufficient.
- Listing values without semantic roles or provenance.
- Treating every declared token as used.
- Collapsing close colors or spacing values without evidence.
- Describing one page as the whole product.
- Mixing current facts with redesign recommendations.
