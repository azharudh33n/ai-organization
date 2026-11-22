# Changelog

## 1.2.0 (2026-11-22)

- **The skill is opt-in.** The description now says to use it only when the user names it or asks for a project to be run or staffed as a company, an organization or a team of AI agents, and not for ordinary build, fix, plan, research or review requests.
- **CI/CD playbook split into two levels.** A baseline for every project (required checks, pinned actions, read-only tokens, secret scanning, a tried rollback) and an advanced level for projects with personal data, real money at risk, many teams or published artifacts (merge queues, OIDC, attestations, staging, canary releases, DORA metrics). The brief says which level applies and why.
- **Vetting gate: stricter reading of a skill's declared name.** A third security review pointed out that the gate's reading of `SKILL.md` frontmatter was looser than a real YAML parser. It now accepts one unambiguous spelling of `name:` and treats anything else (comments, anchors, tags, escapes, indented or repeated keys, a byte-order mark) as "this file might be the skill", which blocks approval. `skill.md` in any letter case counts as a skill file.

Trigger check: a proxy test with 14 requests (6 that ask for the organization approach, 8 ordinary ones) gave 14 of 14 for the new description. The old description also scored 14 of 14 on the same proxy, so the test shows the new wording keeps every wanted trigger but does not show that the old one over-triggered. The real trigger harness could not run because the `claude` CLI on the test machine was not logged in.

## 1.1.2 (2026-11-22)

Three more fixes to the vetting gate from a second automated security review.

- **The gate now finds a skill's folder the way the installer does**, by the name declared in `SKILL.md`. Before, it went by folder name, so a repo could show the gate one folder and the installer another. If more than one folder could be the skill, or any `SKILL.md` has no readable name, the verdict is never better than `ask`.
- **Change detection uses git's content hash of the folder** at the audited commit and at the vetted commit, instead of a list of changed files. That covers renames and has no file-count limit.
- **Symlinks and submodules.** A skill folder that contains one depends on content outside it, so any change anywhere in the repo now counts as a change to the skill.
- The gate prints the vetted path as well as the commit, and the playbook has the agent check both against `skills-lock.json` after installing.

## 1.1.1 (2026-11-22)

Security fix for the vetting gate, found by an automated review of 1.1.0.

- **The gate now judges the commit that gets installed.** In 1.1.0 it read a skill's audits and then installed whatever commit was newest, so a skill changed after its audits could be installed on the strength of them. An audit now counts only if the skill's files are unchanged between the commit that was current when the audit ran and the commit being vetted, using GitHub's push log and diff. The gate prints that commit and the install pins it.
- `approved` now needs at least two current audits.
- A failing audit of an earlier version leads to `ask`, not `approved`, even when newer audits pass.
- README and site: removed the comparison table against the unpublished original version.

## 1.1.0 (2026-11-22)

Talent sourcing rebuilt for cloud and unattended sessions, where no skills are installed.

Added:

- **Vetting gate** (`scripts/vet_skill.py`). It decides from the independent security audits skills.sh publishes and from GitHub's verified-organization status, and fails closed. Verdicts are `approved`, `ask` and `rejected`.
- **Committed roster.** Approved skills are installed with the `skills` CLI, pinned to a commit with a content hash in `skills-lock.json`, and committed to the project so later sessions start with them.
- **Unattended policy.** With nobody to ask, only `approved` skills are installed. Anything else is logged as a proposal.
- Engineering playbook: check current library docs before using an API, instead of relying on model memory.

Changed:

- The hardcoded list of GitHub repos and awesome-lists is gone, along with the 30-point scoring rubric. skills.sh search and the gate replace them.
- The hiring log lives in the project (`org/hiring-log.md`). The shared log under `~/.claude/` did not survive cloud sessions.

Verified:

- The gate was run against live skills: it approved `vercel-labs/agent-skills` web-design-guidelines, asked on `anthropics/skills` webapp-testing (audit warnings) and rejected a popular Playwright skill with a failing Snyk audit.

## 1.0.0 (2026-11-22)

First public release, evolved from the author's original single-file skill (v0). Measured against v0 on the eval suite in `evals/`; numbers are in `docs/evolution/benchmark.md`.

### Added

- **Size the job first.** Solo, Squad and Company tiers, so small tasks skip the full ceremony.
- **Token budget rules.** Brief by reference, handoffs of 200 words or less, match the model to the role, read once and share a map, cap the loops.
- **CI/CD playbook** (`references/cicd.md`): trunk-based flow, required checks, merge queues, SHA pinning or workflow lockfiles, least-privilege tokens, OIDC, provenance and SBOM attestations, Dependabot cooldowns, preview environments, progressive delivery with automatic rollback, guardrails for agent-written code, and DORA's five metrics.
- Packaging as a Claude Code plugin and marketplace, an eval suite (`claude plugin eval` layout), a validator script with unit tests, and hardened CI.
- Release pipeline: tagged releases ship `ai-organization-skill.zip` with SHA256SUMS and a SLSA build provenance attestation.
- Project site on GitHub Pages with search and social metadata (Open Graph, JSON-LD, sitemap), plus SECURITY, CONTRIBUTING, CODE_OF_CONDUCT, CITATION.cff and issue/PR templates.

### Changed

- `SKILL.md` is now a lean core of about 2k tokens, down from about 4.4k. Playbooks moved to `references/` and load only for departments that get staffed.
- Description rewritten in the third person, with the "when to use" triggers.
- Talent sourcing: repos re-verified. `forrestchang/andrej-karpathy-skills` now redirects to `multica-ai/andrej-karpathy-skills`.
- The Karpathy Loop restores the editable scope from the best commit instead of running a hard reset.
- The kickoff prompt moved to the README, since it is for humans, not the model.
