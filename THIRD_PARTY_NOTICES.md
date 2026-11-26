# Third-Party Notices

## i-have-adhd actionable output

`i-have-adhd-actionable-output` is selectively adapted from
[`ayghri/i-have-adhd`](https://github.com/ayghri/i-have-adhd) at commit
`839872f9d1cd634fed642b4589ce7226199cc15f`, specifically
[`skills/i-have-adhd/SKILL.md`](https://github.com/ayghri/i-have-adhd/blob/839872f9d1cd634fed642b4589ce7226199cc15f/skills/i-have-adhd/SKILL.md).

The adaptation retains answer/action-first presentation, bounded steps,
visible progress, completeness safeguards, task/harness precedence, and
evidence-calibrated language. It combines these into one task-scoped skill.
It removes the presumed diagnosis, hard list-size target, mandatory time
estimates, and default session persistence. Runtime hooks, installers, platform
extensions, and the upstream Git history are not imported. This is a selective
content adaptation, not a verbatim Git cherry-pick or an upstream endorsement.

MIT License

Copyright (c) 2026 Ayoub Ghriss

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

## Superpowers skills

The `superpowers-*` skills in this repository are adapted from [obra/superpowers](https://github.com/obra/superpowers) at commit `d884ae04edebef577e82ff7c4e143debd0bbec99`.

MIT License

Copyright (c) 2025 Jesse Vincent

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

## Google Stitch frontend skills

The following skills are adapted from
[`google-labs-code/stitch-skills`](https://github.com/google-labs-code/stitch-skills)
at commit `3f64079d75d025bc5890c73669f27c26a2d80b31`:

- `google-stitch-frontend-taste-design`
- `google-stitch-extract-frontend-design-system`
- `google-stitch-frontend-brief-enhancer`
- `google-stitch-shadcn-ui`

The adaptations remove runtime dependencies on Google Stitch services and
rename, restructure, and revise the source material for portable agent use.

Copyright 2026 Google LLC

Licensed under the Apache License, Version 2.0 (the "License"); you may not use
these adapted materials except in compliance with the License. You may obtain a
copy of the License at:

<https://www.apache.org/licenses/LICENSE-2.0>

Unless required by applicable law or agreed to in writing, software distributed
under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR
CONDITIONS OF ANY KIND, either express or implied. See the License for the
specific language governing permissions and limitations under the License.

## pstack

Selectively adapted from Lauren Tan's [pstack](https://github.com/cursor/plugins/blob/41e400932eca14f289e7db717a70455256b6d388/pstack/README.md) at `41e400932eca14f289e7db717a70455256b6d388`.

- [benchmark-checklist](https://github.com/cursor/plugins/blob/41e400932eca14f289e7db717a70455256b6d388/pstack/skills/benchmark-checklist/SKILL.md) supplies the measurement checks for the standalone local skill.
- [blast-radius](https://github.com/cursor/plugins/blob/41e400932eca14f289e7db717a70455256b6d388/pstack/skills/blast-radius/SKILL.md) supplies the decisive compatibility assumption and consumer check in step 6 of `before-git-push`.
- [sharpen](https://github.com/cursor/plugins/blob/41e400932eca14f289e7db717a70455256b6d388/pstack/skills/sharpen/SKILL.md) supplies the primary-source and independent-observation prompts for technical investigations in `prompt-polish`.
- [create-verification-skill](https://github.com/cursor/plugins/blob/41e400932eca14f289e7db717a70455256b6d388/pstack/skills/create-verification-skill/SKILL.md) supplies the reusable feature-to-verification mapping adapted for versioned documentation/API checks in `project-bug-hunting`.

MIT License

Copyright (c) 2026 Lauren Tan

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

## Matt Pocock skills

The following skills and selective supplements are adapted from
[`mattpocock/skills`](https://github.com/mattpocock/skills) at commit
`d65391149dbb5fe76478e76fa8d5122b2aa5a70e`:

- `mattpocock-domain-modeling` (`skills/engineering/domain-modeling`)
- `mattpocock-codebase-design` (`skills/engineering/codebase-design`)
- `mattpocock-grilling` (`skills/productivity/grilling`)
- `mattpocock-prototype` (`skills/engineering/prototype`)
- `mattpocock-research` (`skills/engineering/research`)
- `mattpocock-code-review` (`skills/engineering/code-review`) — adapted to detect repository issue trackers without requiring `/setup-matt-pocock-skills`
- `mattpocock-wizard` (`skills/engineering/wizard`)
- `mattpocock-writing-for-agents` (`skills/productivity/writing-for-agents`)

Selective cherry-picked supplements from the same commit:

- `skills/find-a-bug/references/feedback-loops.md` and `skills/find-a-bug/scripts/hitl-loop.template.sh` (adapted from `skills/engineering/diagnosing-bugs`)
- `skills/superpowers-test-driven-development/seam-and-slicing-guide.md` (adapted from `skills/engineering/tdd`)

The adaptations prefix skill names with `mattpocock-`, normalize
`agents/openai.yaml` `display_name` fields to lowercase kebab-case, and make
each skill self-contained inside `polish`. See [`upstream-sources.json`](upstream-sources.json)
for machine-readable provenance used for future upstream syncs.

MIT License

Copyright (c) 2026 Matt Pocock

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

## UI/UX Pro Max quantitative checks supplement

`skills/google-stitch-frontend-taste-design/references/quantitative-checks.md`
selectively adapts the prioritized review categories and quantitative
accessibility, touch, performance, responsive, form, navigation, and chart
baselines from [`nextlevelbuilder/ui-ux-pro-max-skill`](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill)
at commit `8db36338810d0942567b97ce439affd1619fcf31`, specifically
[`src/ui-ux-pro-max/templates/base/quick-reference.md`](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill/blob/8db36338810d0942567b97ce439affd1619fcf31/src/ui-ux-pro-max/templates/base/quick-reference.md).
The upstream CSV database and Python search engine are not imported.

MIT License

Copyright (c) 2024 Next Level Builder

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

## Session format references in `takeover-agent-sessions`

`skills/takeover-agent-sessions/references/storage-and-pitfalls.md` and the
format parsers in `skills/takeover-agent-sessions/scripts/takeover_session.py`
cross-verify multi-OS storage paths, read-only exploration patterns, and
observed session format schemas against:

- [`jlreyes/agent-history-skills`](https://github.com/jlreyes/agent-history-skills) at commit `493c49665ade4762aed523451020101b662742e6` (`skills`)
- [`vshulcz/deja-vu`](https://github.com/vshulcz/deja-vu) at commit `c97753d2ae7d3b62a45730fa2a0ce082839e14e8` (`docs/registry`)

MIT License

Copyright (c) 2026 James Reyes
Copyright (c) 2026 Vladislav Shulcz

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

## AI Agents in Depth (`bojieli/ai-agent-book`)

The eight AI Agent & Harness engineering skills (`auditing-agent-skills`,
`architecting-agent-context`, `designing-agent-tools-mcp`,
`hardening-agent-harness`, `orchestrating-multi-agent-workflows`,
`architecting-agent-memory-rag`, `engineering-async-realtime-agents`, and
`evaluating-evolving-agents`) distill architectural patterns, v3.0 experimental
evidence, and reworked skill guidance from
[`bojieli/ai-agent-book`](https://github.com/bojieli/ai-agent-book) (forked at
[`joe-nv/ai-agent-book`](https://github.com/joe-nv/ai-agent-book)) at commit
`40f4ce5778e6cc93e3606c3079bf8cf13a0c4d04` (`book/` and `skills/`). All Python
helper scripts and unit tests in these skills are original implementations for
`polish`.

Copyright 2025 Bojie Li

Licensed under the Apache License, Version 2.0 (the "License"); you may obtain
a copy of the License at `http://www.apache.org/licenses/LICENSE-2.0`.
Unless required by applicable law or agreed to in writing, software distributed
under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR
CONDITIONS OF ANY KIND, either express or implied.
