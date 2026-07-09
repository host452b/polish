# Google Stitch Frontend Skills Port Design

## Goal

Adapt four frontend-design skills from the local
`/Users/joejiang/Movies/stitch-skills` source repository into the `polish`
collection as portable skills for Claude Code, OpenCode, Codex, and compatible
agents:

| Source capability | Polish skill |
| --- | --- |
| Taste-led design direction | `google-stitch-frontend-taste-design` |
| Design-system extraction from source | `google-stitch-extract-frontend-design-system` |
| Frontend brief enhancement | `google-stitch-frontend-brief-enhancer` |
| shadcn/ui implementation guidance | `google-stitch-shadcn-ui` |

The `google-stitch-` prefix must appear in both each directory name and its
YAML `name`. Existing skills in both repositories remain unchanged.

## Design Principles

The port is an adaptation, not a byte-for-byte copy:

1. Preserve the source skills' reusable design judgment, workflow, examples,
   and deterministic helpers.
2. Remove all runtime dependence on Stitch MCP, `upload-to-stitch`, Stitch API
   project or screen identifiers, and the `.stitch/` workspace convention.
3. Use a repository-local `DESIGN.md` as the shared contract between the
   taste, extraction, brief, and implementation layers.
4. Keep each `SKILL.md` concise. Move large framework guidance, taste rules,
   keyword catalogs, and examples into one-level `references/` or `assets/`
   files.
5. Write trigger-only descriptions beginning with `Use when...`; do not
   summarize the workflow in frontmatter.
6. Preserve source provenance and Apache-2.0 attribution in the repository's
   third-party notice.

## Skill Boundaries

### `google-stitch-frontend-taste-design`

Use for creating or reviewing visual direction when an interface risks generic
AI styling, weak hierarchy, incoherent color, repetitive cards, poor
typography, or decorative motion without purpose.

The skill will:

- Establish atmosphere, density, variance, color, typography, layout, motion,
  responsiveness, and component-state direction.
- Treat anti-patterns as guardrails rather than universal bans. Decisions must
  reflect product context instead of mechanically forbidding a font or layout.
- Produce or update `DESIGN.md` when a durable design contract is needed.
- Support design review of existing code or screenshots without requiring a
  particular framework.

Detailed taste heuristics belong in a reference file; the main skill retains
only the decision workflow and review gates.

### `google-stitch-extract-frontend-design-system`

Use when an existing frontend repository needs its visual language,
design tokens, inconsistencies, or component patterns documented from source.

The skill will:

- Read source without requiring a successful build.
- Detect framework and styling approach.
- Extract colors, typography, spacing, radii, elevation, motion, breakpoints,
  layout patterns, component states, and accessibility-relevant styling.
- Consolidate near-duplicate tokens and distinguish observed facts from
  inferred intent.
- Write a portable root-level `DESIGN.md`.

Framework-specific extraction details and a strong example `DESIGN.md` belong
in references rather than the main skill.

### `google-stitch-frontend-brief-enhancer`

Use when a frontend request is too vague to implement without inventing visual,
structural, interaction, responsive, or content decisions.

The skill will:

- Preserve user-provided product facts and avoid fabricated metrics or copy.
- Read `DESIGN.md` when present.
- Convert a rough request into an implementation-ready brief covering purpose,
  platform, page structure, content hierarchy, components, states,
  responsiveness, accessibility, motion, and acceptance criteria.
- Separate confirmed requirements, reasonable inferences, and unresolved
  decisions.
- Stop at the brief; it does not implement the interface.

### `google-stitch-shadcn-ui`

Use when implementing or reviewing a React interface that uses shadcn/ui and
needs coherent theming, component composition, variants, accessibility, or
responsive behavior.

The skill will:

- Treat `DESIGN.md` and the enhanced brief as inputs when available.
- Prefer composition over editing registry primitives for product-specific
  behavior.
- Preserve keyboard, focus, ARIA, loading, empty, error, and disabled states.
- Use project-native tokens and variants instead of one-off class strings.
- Include a deterministic setup checker only if it remains useful after
  removing assumptions about a particular MCP environment.

Large component catalogs and framework-specific implementation references
remain progressive-disclosure resources.

## Shared Data Flow

```text
Existing repository ──> google-stitch-extract-frontend-design-system ──> DESIGN.md
New or weak direction ─> google-stitch-frontend-taste-design ──────────> DESIGN.md
User request + DESIGN.md ─> google-stitch-frontend-brief-enhancer ─────> frontend brief
Frontend brief + DESIGN.md ─> google-stitch-shadcn-ui ─────────────────> implementation
```

Each skill must also work independently when its optional upstream artifact is
absent. No skill may silently invoke another skill merely because it exists.

## Test-Driven Skill Authoring

Create and validate one skill at a time.

For each skill:

1. Run a realistic baseline scenario without the new skill and record concrete
   omissions, shortcuts, or rationalizations.
2. Write the minimum skill and runtime/reference closure addressing those
   observed failures.
3. Run the same scenario with the new skill.
4. Add only the guardrails required by newly observed failures.
5. Run structural validation and finish that skill before starting the next.

Baseline scenarios:

- Taste: improve a generic SaaS landing page under time pressure without
  inventing product facts.
- Extraction: audit a mixed Tailwind/CSS-variable repository whose tokens are
  inconsistent and whose app cannot build.
- Brief: turn “make the settings page feel premium” into an actionable brief
  without guessing business requirements.
- shadcn/ui: implement a dense responsive settings surface while preserving
  theming, interaction states, and accessibility.

## Repository Integration

- Add the four canonical directories under `skills/`.
- Add a deterministic `scripts/validate_google_stitch_port.py` that checks
  expected runtime files, matching frontmatter names, relative links, and
  forbidden Stitch/upload dependencies.
- Update English and Chinese README skill lists, descriptions, workflow, and
  structure.
- Update Claude, Codex, Cursor, and marketplace metadata descriptions and
  relevant discovery keywords without changing package name or version.
- Extend `THIRD_PARTY_NOTICES.md` with the source repository URL, source
  commit, Apache-2.0 attribution, and adaptation scope.
- Do not modify the existing untracked `superpowers/` source checkout.

## Validation

Before completion:

1. Run the new port validator.
2. Run `quick_validate.py` for every canonical skill.
3. Parse all JSON manifests and run the plugin validator.
4. Validate any retained shell, JavaScript, or Python helpers.
5. Run the skill behavior scenarios and retain concise evidence of baseline
   failure and post-skill improvement.
6. Run `git diff --check`.
7. Confirm pre-existing commits and the untracked `superpowers/` checkout
   remain untouched.

## Completion Criteria

The port is complete when the four prefixed skills are independently
discoverable, contain no upload or Stitch MCP runtime dependency, compose
through optional `DESIGN.md` and brief artifacts, pass structural and
behavioral validation, preserve source attribution, and leave existing user
work intact.
