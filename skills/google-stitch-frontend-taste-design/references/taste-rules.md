# Frontend Taste Rules

Use these rules as a decision library, not a fixed aesthetic preset. Product intent, audience, brand, content, and platform take priority.

## Direction Axes

Set four explicit axes before choosing details:

| Axis | Restrained end | Expressive end |
| --- | --- | --- |
| Atmosphere | utilitarian, quiet, clinical | warm, editorial, playful |
| Density | gallery-airy | cockpit-dense |
| Variance | regular and symmetric | asymmetric and surprising |
| Motion | static and immediate | choreographed and cinematic |

Explain why the selected position supports the product. Do not maximize every axis.

## Color

- Assign colors by role: canvas, surface, primary text, muted text, border, accent, positive, warning, and destructive.
- Prefer one dominant accent unless multiple accents encode real categories or states.
- Use tonal separation and borders before relying on large shadows or glow.
- Avoid pure black, neon gradients, or low-contrast gray-on-gray as unexamined defaults; use them only when brand and contrast evidence support them.
- Test text, icons, focus rings, disabled controls, charts, and status colors in both light and dark modes when both exist.

## Typography

- Build hierarchy through family, weight, size, leading, width, and color—not size alone.
- Keep body copy readable: usually 45–75 characters per line and comfortable leading.
- Use a display face only when its character supports the product; operational software usually benefits from a calm sans and a mono face for code-like data.
- Treat any proposed font as provisional until availability, licensing, language coverage, and performance are checked.
- Avoid defaulting to the same fashionable font for every product, but do not ban a suitable existing brand font.

## Composition and Layout

- Establish a grid, maximum content width, spacing scale, and alignment logic.
- Use asymmetry when it creates emphasis or narrative movement, not merely novelty.
- Avoid repetitive equal-card grids when sequence, comparison, grouping, or progressive disclosure communicates the content better.
- Use cards only when the boundary conveys grouping, action, selection, or elevation. Prefer whitespace, dividers, or background shifts for flat content.
- Give the primary action a clear location. Secondary actions are valid when the user genuinely has a second intent.
- Keep decorative imagery out of the reading and interaction path.

## Components and States

For every relevant interactive component, define:

- Default, hover, focus-visible, active, disabled, and loading behavior.
- Empty, error, success, and partial-data states for data-bearing surfaces.
- Shape, border, fill, elevation, icon treatment, and feedback timing.
- Keyboard order, accessible name, target size, and error association.

Use skeletons only when the final geometry is predictable. Prefer specific inline feedback over generic spinners or toasts.

## Responsive Behavior

- Design the collapse order; do not merely say “make it responsive.”
- Preserve reading order when multi-column layouts become one column.
- Use fluid type and spacing within bounded ranges.
- Keep interactive targets at least 44 by 44 CSS pixels when possible.
- Prevent horizontal overflow; decide whether dense tables scroll, stack, summarize, or switch views.
- Recompose expressive inline imagery on small screens rather than shrinking it into illegibility.

## Motion

- Tie motion to cause: reveal hierarchy, explain continuity, confirm action, or show state change.
- Animate transform and opacity by default; avoid layout-triggering properties when possible.
- Use short, direct feedback for controls and longer choreography only for meaningful scene changes.
- Respect reduced-motion preferences and preserve comprehension without animation.
- Avoid perpetual motion in critical or dense interfaces unless it represents live state and remains calm.

## Content Integrity

- Never fabricate metrics, customers, quotes, certifications, integrations, incident records, or product UI.
- Use explicit placeholders such as `[approved metric]` when real content is missing.
- Avoid generic AI copy such as “revolutionize,” “seamless,” or “next-generation” unless it is approved brand language.
- Do not fill space with fake dashboards or decorative statistics.

## Anti-Generic Review

Question these patterns when they appear without a content reason:

- Purple-blue neon gradients and outer glows.
- Giant centered headlines followed by three identical cards.
- Excessive pills, glass panels, floating nav bars, or rounded containers.
- Emoji as product iconography.
- Stock photography unrelated to the user’s work.
- Identical spacing and hierarchy on every section.
- Decorative scroll cues, custom cursors, and motion loops.

The fix is usually stronger information architecture, composition, and content—not a different effect.

## Final Review Gate

- Can a viewer identify the page purpose and primary action in five seconds?
- Does each visual choice trace to product context or an explicitly labeled assumption?
- Are real content and placeholders distinguishable?
- Are all relevant states covered?
- Does mobile preserve hierarchy and task completion?
- Are focus, contrast, target size, and reduced motion addressed?
- Are repeated components governed by shared tokens?
- Does decoration support meaning rather than compensate for weak structure?
