# CI/CD and release playbook

Contents: which level to use · baseline (every project) · advanced (when the stakes call for it) · guardrails for agent-written code · sources

The DevOps hire sets up the pipeline **before** feature work starts, so every agent's diff is gated from its first commit. Examples use GitHub Actions; the same ideas apply to GitLab CI, Buildkite and others.

## Which level to use

Start from the baseline. It is cheap, and it is enough for a landing page, a marketing site, a client brochure site, an internal tool or a prototype.

Add the advanced section, in whole or in part, when at least one of these is true, and say in the brief which one:

- the project handles personal, health or payment data, or falls under a compliance regime
- downtime or a bad release costs real money or safety
- several teams or many agents merge into the same repo every day
- the project publishes artifacts other people install (packages, images, binaries)

Process the project doesn't need is a cost, not a safety margin: a canary rollout for a five-page site only slows it down.

## Baseline (every project)

**Flow.** Trunk-based: short-lived branches (hours, not days) merge into `main` behind required checks, and `main` is always deployable. A red build gets fixed or reverted right away.

```text
PR opened → lint · type-check · tests · build      (required, in parallel, a few minutes)
          → preview deploy, if the host offers one  (Vercel, Netlify, Coolify and similar)
merge to main → build → deploy → smoke test (the site loads, the key flow works)
```

**Required checks** on `main`, set through branch protection or a ruleset: lint, type-check, tests and build, plus one approval from a person or an independent agent.

**Pipeline safety that costs nothing:**

- Pin every third-party action to a full commit SHA with the version in a comment, or use GitHub's workflow lockfile. Tags can be moved; that is how the tj-actions/changed-files compromise leaked secrets.
- Set `permissions: contents: read` at the top of each workflow and grant more per job only where needed. Set `persist-credentials: false` on checkout.
- Never put `${{ github.event.* }}` straight into a `run:` script; pass it through `env:`. Avoid `pull_request_target`.
- Turn on secret scanning with push protection.
- Turn on Dependabot or Renovate, with a cooldown of a few days on version updates. Security updates skip the cooldown.

**Rollback.** Write down the one command or button that puts the previous release back (redeploy the last good build), and try it once before launch.

**DoD items the baseline adds:** CI is green on the shipped commit; the four checks are required on `main`; actions are pinned and tokens are read-only; the rollback step has been tried once.

## Advanced (when the stakes call for it)

### Stricter gates

- Dependency review on every PR, failing on new high or critical vulnerabilities or disallowed licenses.
- Workflow linting: `zizmor` (security audits) and `actionlint` (syntax).
- CODEOWNERS on `.github/workflows/` and deploy config.
- A merge queue when many PRs land per day. Workflows must also trigger on `merge_group`, or the required checks never report and the queue stalls.

### Supply chain

- No long-lived cloud secrets: deploy with OIDC federation, and keep anything that must stay a secret in environment-scoped secrets with required reviewers for production.
- Build once, attest the artifact and its SBOM (`actions/attest-build-provenance`, `actions/attest-sbom`), and verify the attestation before deploying (`gh attestation verify`). Building in a shared reusable workflow raises the SLSA build level.
- GitHub-hosted or ephemeral runners only. Never put a self-hosted runner on a public repo.

### Deployment

- **Staging** that mirrors production config, with seeded or anonymized data. Real personal data only where the law allows it.
- **Progressive rollout** to production: a canary or percentage rollout gated on error rate and latency, with automatic abort and rollback (for example Argo Rollouts analysis, or the platform's health checks). Feature flags separate deploying from releasing. If the platform can't do this (a single server, for instance), say so in an ADR and use a health-gated deploy with a rehearsed rollback instead.
- **Database migrations** are backward-compatible (expand, then contract), so the previous release can roll back without data loss.
- **Rollback is rehearsed** in staging, and the QA report shows it.

**Metrics.** Track the five DORA metrics. Throughput: change lead time, deployment frequency, failed-deployment recovery time. Instability: change fail rate, deployment rework rate. DORA's research on AI-assisted development finds that AI tends to raise throughput while hurting stability unless strong platform practices are in place.

**DoD items the advanced level adds:** `zizmor` reports no high findings; a staging deploy passed the E2E smoke test; the rollback was exercised in staging and documented; release artifacts verify against their attestation.

## Guardrails for agent-written code (both levels)

- Agents work on branches and open PRs. They never push to `main`, and they can't approve or merge their own PRs.
- A person with write access approves workflow runs on agent-opened PRs.
- AI code review can comment, but it doesn't replace the required checks or the independent reviewer.
- When coding agents run inside CI (for example `anthropics/claude-code-action`), restrict them: an allow-list of tools, `--max-turns`, job timeouts, concurrency limits, OIDC or a narrowly scoped GitHub App instead of broad tokens, and no triggers from untrusted bots.

## Sources

GitHub secure-use guide (docs.github.com/en/actions/reference/security/secure-use) · workflow lockfiles (github.blog changelog) · CISA alert on CVE-2025-30066, 2025-03-18 · artifact attestations (docs.github.com/en/actions/concepts/security/artifact-attestations) · SLSA v1.2 · Dependabot default cooldown · merge queue docs · dora.dev trunk-based development and DORA metrics guides · DORA 2025 State of AI-assisted Software Development · Argo Rollouts analysis · Claude Code GitHub Actions docs · zizmor audits (docs.zizmor.sh).
