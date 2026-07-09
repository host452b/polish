---
name: google-stitch-frontend-taste-design
description: Use when creating or reviewing frontend visual direction and the interface risks generic AI styling, weak hierarchy, incoherent color, repetitive layouts, poor typography, or decorative motion without purpose.
---

# Frontend Taste Design

## Overview

Create a coherent visual point of view before polishing components. Be opinionated about hierarchy and composition, but label assumptions and let product context override stylistic defaults.

## Workflow

1. **Establish evidence.** Identify the product goal, audience, real content, existing brand assets, platform, and technical constraints. Separate confirmed facts, reversible assumptions, and missing decisions. Never invent metrics, customers, testimonials, capabilities, or compliance claims.
2. **Choose a direction.** Define atmosphere, density, compositional variance, and motion intensity. Then specify palette roles, type hierarchy, layout rhythm, imagery, elevation, and interaction character. Read [taste-rules.md](references/taste-rules.md) for detailed heuristics.
3. **Make it implementable.** Cover desktop and mobile composition plus default, hover, focus, active, disabled, loading, empty, error, and success states where relevant. Give concrete tokens or bounded ranges, not adjectives alone.
4. **Record durable decisions.** When the direction will guide multiple screens or agents, create or update `DESIGN.md` using [the template](assets/DESIGN.md). Preserve compatible existing tokens unless the user approved a redesign.
5. **Run the review gate.** Check hierarchy at a glance, content truthfulness, contrast, keyboard focus, touch targets, responsive collapse, reduced motion, and consistency across repeated elements.

## Decision Rules

| Situation | Response |
| --- | --- |
| Brand context is missing | Offer one recommended direction and label it provisional |
| Existing design language is coherent | Extend it instead of imposing a fashionable replacement |
| Interface feels generic | Change composition and hierarchy before adding decoration |
| Dense operational UI | Prioritize scanability, alignment, and restrained motion |
| Marketing or editorial UI | Allow more expressive type, imagery, and asymmetry |

## Example

Weak: “Use a modern dark gradient, three feature cards, and smooth animations.”

Strong: “Use a calm, high-contrast operational canvas; organize capabilities as an alternating narrative rather than equal cards; reserve one accent for actions and focus; label the palette and type choices as provisional until brand assets are available.”

## Common Mistakes

- Treating personal taste as a universal ban.
- Choosing fonts or colors without stating whether they are existing tokens or proposals.
- Polishing surfaces before fixing content hierarchy.
- Specifying only the ideal state and ignoring failures, empty data, focus, or mobile.
- Adding motion without explaining what change or relationship it communicates.
