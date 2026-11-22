# Brief: evolve the ai-organization skill (v0 → v1)

This brief is the skill run on itself: Phase 0 of ai-organization, with the skill as the project.

**Goal:** make the skill produce better-run projects for fewer tokens, and make it publishable as a Claude Code plugin.

**Deliverables:** improved skill (plugin layout), eval suite, CI workflows, README, public GitHub repo.

**Audience:** Claude Code users who want Claude to orchestrate subagents on multi-role projects.

**Constraints:** follow Anthropic's skill authoring guidance. Keep the original's intent (CEO → hire → source skills → Karpathy methods → independent QA → ship). No dependencies the skill can't explain.

## Definition of Done

1. `SKILL.md` body is ≤ 500 lines and loads at least 50% fewer tokens than v0 when the skill triggers (measured with `scripts/validate_skill.py`).
2. Frontmatter passes validation: `name` matches folder, kebab-case, ≤ 64 chars; `description` ≤ 1024 chars and says when to use the skill.
3. Detailed playbooks live in `references/`, one level deep, each linked from `SKILL.md` with a note on when to read it.
4. On the eval suite, v1's assertion pass rate is higher than v0's, with no case scoring lower.
5. v1 uses no more tokens than v0 on average across eval runs.
6. A CI/CD playbook reflects current practice (supply-chain hardening, required checks, preview envs, progressive delivery, DORA), with sources.
7. The repo's own CI passes: validation, markdown lint, link check and workflow lint, with actions pinned to commit SHAs and least-privilege permissions.
8. A reviewer who didn't write v1 checks it against this list before publishing.

## Assumptions

- "Save tokens" means fewer tokens loaded per trigger and fewer tokens spent per run (no needless ceremony on small jobs).
- Evals are dry runs (planning only) so they are cheap and repeatable. Full project execution is too costly to benchmark here.
- MIT license.
