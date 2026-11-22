# Benchmark: v0 → v1

How the skill was evolved, using its own method: a fixed eval, one change set at a time, and changes kept only when they beat the baseline.

## Setup

- **Cases:** the three in [`evals/`](../../evals/). Each is a planning dry run, stopping before execution, so runs are cheap and repeatable.
- **Configurations:** `old_skill` is the original single-file skill (v0). `new_skill` is this repo's version.
- **Runner:** one fresh subagent per run (Claude Opus 5.5), with no subagents of its own and no web access.
- **Grader:** a separate fresh agent that saw only the prompt, the assertions and the outputs, and cited evidence for every pass or fail.
- **Size on trigger:** `scripts/validate_skill.py` estimates tokens as characters ÷ 4.

## Results

### Loaded on every trigger

| | v0 | v1 |
|---|---|---|
| SKILL.md body | 260 lines, ~4,351 tokens | 89 lines, ~2,166 tokens (**−50%**) |
| Playbooks | inline, always loaded | ~5,100 tokens in `references/`, loaded only for staffed departments |

### Iteration 1 (15 assertions)

| Case | v0 | v1 | Tokens v0 → v1 | Time v0 → v1 |
|---|---|---|---|---|
| webapp-ci-cd-plan | 6/7 | 6/7 | 165k → 161k | 581s → 532s |
| tiny-task-right-sizing | 3/4 | **4/4** | 112k → 98k | 125s → **37s** |
| research-report-plan | 4/4 | 4/4 | 136k → 139k | 348s → 352s |

**What the grader found:** v1 right-sized the small task (no paperwork, against 9 files for v0) and had stronger CI/CD security. But its "smallest team" rule merged roles that should stay apart: the benchmark builder also tuned the engines it was judging. The assertions didn't catch this, so two separation-of-duties assertions were added.

### Iteration 2 (17 assertions)

**Changes to the skill:**

- separation of duties now beats team size
- utility agents count toward the team cap
- rolling-wave planning (detail only the current milestone)
- ADRs only for decisions that are expensive to reverse

| Case | v0 | v2 | Tokens v0 → v2 | Time v0 → v2 |
|---|---|---|---|---|
| webapp-ci-cd-plan | 6/8 | **8/8** | 165k → 149k | 581s → 452s |
| tiny-task-right-sizing | 3/4 | **4/4** | 112k → 99k | 125s → 39s |
| research-report-plan | 5/5 | 4/5 | 136k → 148k | 348s → 422s |
| **Total** | **14/17 (82%)** | **16/17 (94%)** | mean −4% | mean −14% |

v2's one miss: its research plan asked for "at least 2 sources" and dropped the word "independent" that the playbook requires. That looks like run-to-run variation, not a gap in the skill. With rolling-wave planning, the webapp plan details 30 tasks up front instead of 97. The research run moved up to the Company tier to keep builder and tuner separate (6 roles, against 9 for v0), which explains its higher cost.

## After iteration 2

An independent QA review of the repo (not of the eval runs) led to these fixes, which were not re-run through the eval suite:

- The Karpathy Loop no longer has the tuner write its own locked eval.
- The separation rule now targets acceptance and DoD suites, so builders still write their own TDD unit tests.
- The user approves anything irreversible or shared.
- One shared hiring log lives at `~/.claude/ai-organization/hiring-log.md`.
- On sensitive data, a dedicated security reviewer is hired.
- zizmor is pinned.
- The validator budget enforces at least a 50% cut from v0.

## Caveats

- There is one run per configuration per case, so treat the differences as directional. Run `claude plugin eval .` (3 runs per case by default) for tighter numbers.
- Grading was done by an LLM judge. Count-based assertions were checked by counting files and roles.
- The dry runs test planning and staffing, not execution quality.
- One v2 research run read a hiring log another eval run had left in the shared workspace. Future runs should get isolated directories.

## v1.1.0: skill sourcing check

Talent sourcing was rebuilt around skills.sh and a vetting gate. One fresh agent ran phases 0 to 3 on a Next.js, Supabase and Playwright project, told it was unattended in a cloud session with an empty roster. This was a single manual run, checked by inspecting the resulting repo, not a graded eval.

| Candidate | Installs | Gate verdict | Outcome |
|---|---|---|---|
| `supabase/agent-skills` supabase-postgres-best-practices | n/a | `approved` | Installed at a pinned commit, committed in its own commit |
| `microsoft/playwright-cli` playwright-cli | 224K | `ask` (Snyk warns, medium) | Logged as a proposal |
| `github/awesome-copilot` playwright-generate-test | 18.3K | `ask` (Runlayer warns, medium) | Logged as a proposal |
| `supabase/agent-skills` supabase | 372.3K | `ask` (Snyk and ZeroLeaks warn, medium) | Logged as a proposal |
| `currents-dev/playwright-best-practices-skill` | 110.2K | `rejected` (Runlayer fails, high) | Not installed |
| `vercel-labs/openreview` next-best-practices | 7.1K | `rejected` (Runlayer fails, high) | Not installed |

What this shows:

- The agent followed the unattended policy: only the `approved` skill was installed, and re-running the gate on it afterwards still returned `approved`.
- The gate is strict. Skills from Microsoft, GitHub and Supabase landed on `ask` because one scanner warned, so an unattended run hired one skill out of six candidates. In practice a person seeds the roster once, by approving the `ask` skills they want, and cloud sessions then start with them.
- Two roles went ahead on a job brief alone. Whether a hired skill improves the work over a brief has not been measured.

The table shows the gate as it was in v1.1.0. Since v1.1.1 an audit counts only if the skill is unchanged since it ran. Under that rule the installed Supabase skill is still `approved` (three current audits), the two skills with a current failing audit are still `rejected`, and `currents-dev/playwright-best-practices-skill` moves from `rejected` to `ask`: its failing scan predates a later change, and its three current scans pass.
