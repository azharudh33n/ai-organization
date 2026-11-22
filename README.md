# ai-organization

[![ci](https://github.com/azharudh33n/ai-organization/actions/workflows/ci.yml/badge.svg)](https://github.com/azharudh33n/ai-organization/actions/workflows/ci.yml)

A Claude Code skill that makes Claude run your project the way a top company would. Claude acts as CEO: it sizes the job, hires only the specialist subagents it needs, gives each one vetted skills and a tight brief, applies Andrej Karpathy's methods, gates software on a modern CI/CD pipeline, and ships only after independent QA proves the work.

It is built to spend tokens like money. A README fix doesn't get a nine-person org chart.

## Install

As a plugin (recommended):

```text
/plugin marketplace add azharudh33n/ai-organization
/plugin install ai-organization@ai-organization
```

Or copy the skill folder by hand:

```bash
git clone https://github.com/azharudh33n/ai-organization
cp -r ai-organization/skills/ai-organization ~/.claude/skills/
```

For the Claude app, zip `skills/ai-organization/` and upload it as a custom skill.

## How it works

1. **Size the job.** Solo (just do it and verify), Squad (2–4 hires, one brief file) or Company (full org, every gate).
2. **Brief and Definition of Done.** 5–10 criteria, each one a test, metric or inspection.
3. **Org chart.** The smallest team that covers every DoD item.
4. **Talent sourcing.** Installed skills first, then official vendor skills, then proven libraries (`obra/superpowers`, Karpathy's guidelines). Each is scored, security-reviewed and pinned to a commit.
5. **Hiring.** One job brief per subagent, with success criteria, boundaries and a handoff of 200 words or less.
6. **Plan and execute.** Parallel lanes, the CI/CD pipeline before features, and the Karpathy Loop for any metric goal.
7. **Independent QA.** A fresh agent that never saw the build checks every DoD item and records evidence.
8. **Review board, delivery and retro.**

Every hire follows the **Karpathy operating system**: think before acting, simplicity first, surgical changes, goal-driven execution.

The core `SKILL.md` stays small. Department playbooks live in [`skills/ai-organization/references/`](skills/ai-organization/references/) and load only when that department gets staffed:

| File | Loaded when |
|---|---|
| `templates.md` | Writing the brief, org chart, job briefs, plan or ADRs |
| `talent-sourcing.md` | Choosing and vetting skills for a role |
| `playbook-engineering.md` | Engineers are hired |
| `cicd.md` | Any software deliverable: pipeline, supply chain, deployment, DORA |
| `playbook-research.md` | Research or benchmarking |
| `playbook-creative.md` | Video, design or UI work |
| `karpathy-loop.md` | A DoD item is a number, or Data/ML hires |
| `qa-and-review.md` | QA, review board and retro |

## Kickoff prompt

```text
Use the ai-organization skill. Run this project the way a top company would.

PROJECT: <what you want built or made>
DELIVERABLES: <e.g. working web app + 60s promo video + launch doc>
AUDIENCE: <who it's for>
CONSTRAINTS: <stack, brand, deadline, budget, compliance>
QUALITY BAR: world-class. Nothing ships without independent QA evidence.

Ask me only if a wrong guess would be expensive. Otherwise decide, note
your assumption, and keep going. Update me at each phase.
```

## Evals

The [`evals/`](evals/) folder holds test cases in the layout `claude plugin eval` reads. Each case is a planning dry run, so the suite stays cheap enough to run often:

| Case | What it checks |
|---|---|
| `webapp-ci-cd-plan` | A checkable DoD, a lean team, CI gates, supply-chain controls, preview/staging with rollback, independent QA, and privacy |
| `tiny-task-right-sizing` | The skill scales down for a 2-line README fix instead of running the whole ceremony |
| `research-report-plan` | Research-led staffing, primary and triangulated sources, a fixed benchmark harness, and no invented numbers |

Run them yourself. These are real, billed model runs:

```bash
claude plugin eval . --allow-tools Write,Edit
```

Results from evolving v0 into v1 are in [`docs/evolution/benchmark.md`](docs/evolution/benchmark.md).

## Repo checks

Every push and PR runs [`ci.yml`](.github/workflows/ci.yml):

- the skill validator (`scripts/validate_skill.py`: frontmatter rules, a token budget for `SKILL.md`, no orphaned or missing references)
- `claude plugin validate --strict`
- markdownlint
- lychee link checking
- zizmor and actionlint on the workflows

Every action is pinned to a commit SHA, tokens are read-only, and Dependabot proposes updates after a 7-day cooldown. The eval suite runs on demand from [`eval.yml`](.github/workflows/eval.yml) with a cost ceiling.

## Credits

Built on ideas from Andrej Karpathy (coding guidelines, autoresearch, the training recipe), [`obra/superpowers`](https://github.com/obra/superpowers), [`anthropics/skills`](https://github.com/anthropics/skills). v1 evolves the author's original single-file ai-organization skill (v0).

## License

[MIT](LICENSE)
