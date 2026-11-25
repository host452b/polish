# Quantitative UI/UX Checks and Review Priority

Selective cross-platform review supplement adapted from `nextlevelbuilder/ui-ux-pro-max-skill` (`src/ui-ux-pro-max/templates/base/quick-reference.md`). Use during the review gate or when numeric thresholds and mobile/web platform baselines are needed alongside `taste-rules.md`.

## Review Priority Order (1 -> 10)

Audit highest-impact failures first instead of treating aesthetics and accessibility as equal weight:

| Priority | Category | Impact | Key Checks |
|---|---|---|---|
| 1 | Accessibility | CRITICAL | Contrast >= 4.5:1 (3:1 large text), visible focus rings, keyboard nav, semantic labels |
| 2 | Touch & Interaction | CRITICAL | Target size & spacing, non-hover primary actions, async loading/press feedback |
| 3 | Performance | HIGH | Prevent CLS (< 0.1), reserve media/async space, virtualize long lists, frame budget |
| 4 | Style Selection | HIGH | Coherent style, SVG icons (no emoji), one clear primary CTA per screen |
| 5 | Layout & Responsive | HIGH | Mobile-first collapse, no horizontal scroll, safe areas, `dvh` viewport units |
| 6 | Typography & Color | MEDIUM | Readable mobile size (>= 16px), semantic tokens, tabular numerals for data |
| 7 | Animation | MEDIUM | Transform/opacity only, interruptible, respects `prefers-reduced-motion` |
| 8 | Forms & Feedback | MEDIUM | Visible labels, inline field errors with `aria-describedby`, IME-safe Enter |
| 9 | Navigation | HIGH | Predictable back behavior, bottom nav <= 5 items, deep links |
| 10 | Charts & Data | LOW | Legends, tooltips, never rely on color alone |

## Measurable Cross-Platform Floors

### Accessibility & Input (WCAG 2.2 / HIG / Material)
- **Contrast**: >= 4.5:1 normal text, >= 3:1 large text and focus indicator state contrast.
- **Focus visibility**: sticky headers, overlays, and banners must not obscure the focused element (`focus-not-obscured`).
- **Pointer & touch targets**: >= 24x24 CSS px minimum on web (WCAG 2.2 AA), >= 44x44 pt (Apple HIG) / >= 48x48 dp (Material) for touch targets, with >= 8px/8dp spacing between adjacent targets.
- **Drag & gesture alternatives**: every drag or swipe action must expose a single-pointer/keyboard or visible control alternative; never block OS system gestures.
- **IME-safe Enter shortcuts**: on custom web Enter handlers, guard against `isComposing` / keyCode 229 so CJK composition confirmation never triggers premature submission.

### Web Performance & Layout Stability
- **CLS < 0.1**: declare explicit `width`/`height` or `aspect-ratio` on images and reserve space for async content.
- **Fonts**: use `font-display: swap` or `optional`; preload only critical fonts.
- **Long lists & responsiveness**: virtualize lists with 50+ items; target < 16ms main-thread frame work and < 100ms input feedback.
- **Mobile viewport & wrapping**: prefer `min-h-dvh` over `100vh` on mobile; keep mobile body/input text >= 16px (prevents iOS auto-zoom); wrap long URLs/IDs with `overflow-wrap: anywhere` rather than `word-break: break-all` on prose.
- **Data alignment**: use `font-variant-numeric: tabular-nums` for prices, counters, timers, and numeric columns.

### Mobile, Forms, Navigation & Charts
- **Safe areas**: keep primary actions clear of notches, Dynamic Island, gesture bars, and screen edges.
- **Forms**: use visible labels (never placeholder-only), show specific inline errors near the field connected via `aria-describedby`, validate on blur (not every keystroke), and focus the error summary or first invalid field after a failed submit.
- **Navigation & charts**: cap bottom navigation at <= 5 items; never encode status or chart series by color alone (pair with icon, pattern, or text label).
