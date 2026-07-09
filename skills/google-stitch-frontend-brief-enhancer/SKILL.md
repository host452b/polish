---
name: google-stitch-frontend-brief-enhancer
description: Use when a frontend request is too vague to implement without inventing visual, structural, interaction, responsive, accessibility, content, or acceptance-criteria decisions.
---

# Frontend Brief Enhancer

## Overview

Turn vague UI language into a bounded, implementation-ready brief. Increase specificity without converting guesses into requirements or starting implementation.

## Workflow

1. **Preserve the request.** Quote the user's goal and non-negotiable wording. Inspect `DESIGN.md`, existing components, screenshots, or product copy when available.
2. **Classify every decision.** Separate **Confirmed requirements**, **Reversible assumptions**, and **Unresolved decisions**. Never invent features, workflows, data, metrics, customers, brand assets, or business rules.
3. **Translate vague language.** Convert words such as “premium,” “modern,” or “clean” into observable hierarchy, spacing, typography, color roles, composition, and interaction behavior. Use [ui-ux-keywords.md](references/ui-ux-keywords.md) for precise terms, not decoration by thesaurus.
4. **Specify the experience.** Cover purpose, audience, platform, page structure, content hierarchy, components, relevant states, responsiveness, accessibility, motion, content constraints, and boundaries. State when a category is not applicable or unknown.
5. **Write acceptance criteria.** Make each criterion observable: named viewport behavior, keyboard path, focus treatment, state coverage, token reuse, content integrity, and preserved behavior. Avoid “looks polished” or “works well.”
6. **Stop at the brief.** Use [brief-template.md](references/brief-template.md). Do not write code, install packages, or silently resolve decisions that would materially change scope.

## Decision Rules

| Situation | Response |
| --- | --- |
| Existing `DESIGN.md` is present | Treat it as the visual contract and cite relevant sections |
| Missing detail is reversible | Recommend one assumption and label it |
| Missing detail changes product behavior | List it as unresolved; do not guess |
| User supplied exact copy or tokens | Preserve them verbatim unless asked to revise |
| Request asks for implementation too | Finish the brief first, then hand it to the implementation workflow |

## Example

Vague: “Make settings feel premium.”

Actionable: “Preserve existing settings and behavior. Use the current token system; strengthen title/section/row hierarchy; define focus, disabled, validation, saving, error, and success treatments where those states exist; specify mobile row collapse and measurable keyboard, contrast, and viewport checks. Brand typography remains unresolved.”

## Common Mistakes

- Smuggling assumptions into imperative requirements.
- Adding imaginary sections to make the brief look complete.
- Describing style without component states or responsive behavior.
- Writing acceptance criteria that cannot be tested.
- Continuing into code before the brief boundary is accepted.
