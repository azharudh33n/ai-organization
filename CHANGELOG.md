# Changelog

## 1.0.0 (2026-11-22)

First public release, evolved from the original single-file community skill (v0). Measured against v0 on the eval suite in `evals/`; numbers are in `docs/evolution/benchmark.md`.

### Added

- **Size the job first.** Solo, Squad and Company tiers, so small tasks skip the full ceremony.
- **Token budget rules.** Brief by reference, handoffs of 200 words or less, match the model to the role, read once and share a map, cap the loops.
- **CI/CD playbook** (`references/cicd.md`): trunk-based flow, required checks, merge queues, SHA pinning or workflow lockfiles, least-privilege tokens, OIDC, provenance and SBOM attestations, Dependabot cooldowns, preview environments, progressive delivery with automatic rollback, guardrails for agent-written code, and DORA's five metrics.
- Packaging as a Claude Code plugin and marketplace, an eval suite (`claude plugin eval` layout), a validator script and hardened CI.

### Changed

- `SKILL.md` is now a lean core of about 2k tokens, down from about 4.4k. Playbooks moved to `references/` and load only for departments that get staffed.
- Description rewritten in the third person, with the "when to use" triggers.
- Talent sourcing: repos re-verified. `forrestchang/andrej-karpathy-skills` now redirects to `multica-ai/andrej-karpathy-skills`.
- The Karpathy Loop restores the editable scope from the best commit instead of running a hard reset.
- The kickoff prompt moved to the README, since it is for humans, not the model.
