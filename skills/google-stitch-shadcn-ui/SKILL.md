---
name: google-stitch-shadcn-ui
description: Use when implementing or reviewing a React interface with shadcn/ui and it needs coherent theming, component composition, variants, accessibility, interaction states, responsive behavior, or visual consistency.
---

# shadcn/ui Interface Integration

## Overview

Build product interfaces from owned shadcn/ui source without turning registry primitives into domain components. Start from the project’s real configuration and design contract, then compose accessible states and verify them in context.

## Workflow

1. **Inspect before installing.** Read `components.json`, `package.json`, global CSS, Tailwind configuration, import aliases, installed `components/ui`, existing composed components, project scripts, and `DESIGN.md` when present. Run `scripts/verify-setup.sh` when setup is uncertain.
2. **Reuse the project vocabulary.** Match its registry style, primitive library, icon set, CSS-variable convention, radii, spacing, and dark-mode strategy. Do not introduce a second token system or arbitrary colors.
3. **Choose the boundary.** Keep reusable primitives in `components/ui`. Put product data, copy, routing, permissions, async behavior, and domain-specific composition outside that directory. Wrap or compose primitives rather than embedding business logic into them.
4. **Model states explicitly.** Cover applicable default, hover, focus-visible, active, selected, disabled, loading, empty, validation, error, success, and partial-data states. Preserve accessible names, descriptions, keyboard behavior, focus management, and non-color cues.
5. **Design responsive behavior.** Specify ordering, stacking, overflow, action placement, target size, and information priority at the project’s existing breakpoints. Do not shrink dense desktop UI until it becomes unreadable.
6. **Verify with project commands.** Run the available typecheck, lint, and tests; inspect light/dark themes and narrow/wide viewports; complete keyboard and accessibility checks. Report commands and observed results.

## Reference Routing

- New or uncertain setup: [setup-guide.md](references/setup-guide.md)
- Component selection: [component-catalog.md](references/component-catalog.md)
- Tokens, variants, and composition: [customization-guide.md](references/customization-guide.md)
- Existing-library migration: [migration-guide.md](references/migration-guide.md)
- Complete form composition: [form-pattern.tsx](examples/form-pattern.tsx)

## Decision Rules

| Need | Preferred response |
| --- | --- |
| Primitive already exists | Reuse it; do not reinstall |
| Product-specific variant | Compose or wrap outside `components/ui` |
| Reusable visual variant | Add a typed variant while preserving primitive semantics |
| Registry source needs updating | Review the diff; preserve intentional local changes |
| No design contract exists | Infer from repeated project tokens and label assumptions |

## Common Mistakes

- Installing components before checking the project registry and aliases.
- Editing copied primitives for one screen’s business logic.
- Using one-off class strings instead of tokens and variants.
- Treating a dialog, toast, or card as the default answer to every hierarchy problem.
- Testing only the ideal desktop state.
- Claiming accessibility from the primitive alone after custom composition.
