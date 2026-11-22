# CI/CD and release playbook

Contents: pipeline design · required checks · supply-chain hardening · deployment · guardrails for agent-written code · metrics · sources

The DevOps hire sets up the pipeline **before** feature work starts, so every agent's diff is gated from its first commit. Examples use GitHub Actions; the same ideas apply to GitLab CI, Buildkite and others.

## Pipeline design

Trunk-based: short-lived branches (hours, not days) merge into `main` behind required checks, and `main` is always deployable. A red build gets fixed or reverted right away, not left for later.

```text
PR opened → lint · type-check · unit tests · build · security scans   (required, in parallel, aim for under 10 min)
         → preview environment per PR + E2E smoke test                 (required for UI work)
merge queue → same checks on the merged result (trigger on `merge_group`)
main → build once → attest provenance + SBOM → deploy staging → smoke test
     → production: canary or progressive rollout, gated on health metrics, automatic rollback
```

## Required checks (branch protection or rulesets)

- Lint, type-check, unit and integration tests, and the build. Each is a named required check.
- A dependency review on every PR, which fails on new high or critical vulnerabilities or disallowed licenses.
- Secret scanning with push protection turned on for the repo.
- Workflow linting: `zizmor` (security audits) plus `actionlint` (syntax).
- At least one human or independent-agent approval, and CODEOWNERS on `.github/workflows/` and deploy config.
- If you use a merge queue, your workflows must also trigger on `merge_group`. Otherwise the required checks never report and the queue stalls.

## Supply-chain hardening

- **Pin every third-party action.** Prefer GitHub's workflow lockfile (`.github/workflows/actions.lock`, which also pins transitive actions) where it's available. Otherwise pin each `uses:` to a full commit SHA, with the version in a comment. Moved tags are how the tj-actions/changed-files compromise leaked secrets.
- **Least privilege.** Set `permissions: contents: read` at the top of every workflow and grant more per job, only where needed. Set `persist-credentials: false` on checkout.
- **No long-lived cloud secrets.** Deploy with OIDC federation to the cloud provider or registry. Store anything that has to stay a secret in environment-scoped secrets, with required reviewers for production.
- **Untrusted input.** Never put `${{ github.event.* }}` straight into a `run:` script; pass it through `env:`. Avoid `pull_request_target`, and never check out fork code with write tokens.
- **Provenance.** Build once, attest the artifact and its SBOM (`actions/attest-build-provenance`, `actions/attest-sbom`), and verify the attestation before deploying (`gh attestation verify`). Building in a shared reusable workflow raises the SLSA build level.
- **Dependency updates.** Dependabot or Renovate, with a cooldown of a few days on version updates so freshly published, possibly compromised releases don't land straight away. Security updates skip the cooldown.
- **Runners.** Use GitHub-hosted or ephemeral runners. Never put a self-hosted runner on a public repo.

## Deployment

- **Preview environment per PR** (Vercel, Netlify, Coolify preview deployments, or Kubernetes namespaces), torn down when the PR closes. The QA agent tests against it.
- **Staging** mirrors production config, with seeded or anonymized data and never real personal data unless the law allows it.
- **Production** rolls out progressively: a canary or percentage rollout gated on error rate and latency, with automatic abort and rollback (for example Argo Rollouts analysis, or your platform's health checks). Feature flags separate deploying from releasing.
- **Database migrations** are backward-compatible (expand, then contract), so the previous release can roll back without data loss.
- **Rollback is rehearsed.** The plan names the exact command or button, and the QA report shows it has been run at least once in staging.

## Guardrails for agent-written code

- Agents work on branches and open PRs. They never push to `main`, and they can't approve or merge their own PRs.
- When coding agents run in CI (for example `anthropics/claude-code-action`), restrict them: an allow-list of tools, `--max-turns`, job timeouts, concurrency limits, OIDC or a narrowly scoped GitHub App instead of broad tokens, and no triggers from untrusted bots.
- A human with write access approves workflows on agent-opened PRs.
- AI code review can comment, but it doesn't replace the required checks or the independent reviewer.

## Metrics (DORA)

Track the five DORA metrics. Throughput is change lead time, deployment frequency and failed-deployment recovery time. Instability is change fail rate and deployment rework rate. DORA's research on AI-assisted development finds that AI tends to raise throughput while hurting stability unless strong platform practices are in place, which is why the gates above matter more, not less, when agents write the code.

## DoD items this playbook usually adds

- CI is green on the shipped commit, and every check above is required on `main`.
- `zizmor` reports no high findings, every action is pinned, and workflow permissions are least-privilege.
- A preview deploy passed the E2E smoke test, and staging passed the smoke test.
- The rollback path was exercised in staging and documented.

## Sources

GitHub secure-use guide (docs.github.com/en/actions/reference/security/secure-use) · workflow lockfiles GA, 2026-10-28 (github.blog changelog) · CISA alert on CVE-2025-30066, 2025-03-18 · artifact attestations (docs.github.com/en/actions/concepts/security/artifact-attestations) · SLSA v1.2 · Dependabot default cooldown, 2026-07-14 · merge queue docs · dora.dev trunk-based development and DORA metrics guides · DORA 2025 State of AI-assisted Software Development · Argo Rollouts analysis · Claude Code GitHub Actions docs · zizmor audits (docs.zizmor.sh).
