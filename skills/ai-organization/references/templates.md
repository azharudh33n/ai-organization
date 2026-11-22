# Templates

Copy only what your tier needs. On the Squad tier, put the brief, team and plan together in `org/brief.md`.

## Brief (`org/brief.md`)

```markdown
# <Project>
Tier: Solo | Squad | Company (and why)
Goal: <one sentence>
Deliverables: <exact outputs: repo, deployed URL, report, video file>
Audience: <who> → success for them means <...>
Constraints: <stack, budget, deadline, brand, legal or compliance>
Assumptions: <each guess you made instead of asking>

## Definition of Done (5–10 items, each a test, metric or inspection)
1. <criterion> (check: <command / metric threshold / inspection>)
```

A weak DoD item reads "the app works". A strong one reads "`pnpm test` passes and the booking E2E flow passes in Playwright on mobile Chrome".

## Org chart row

| Role | Mission | Owns DoD items | Reports to | Depends on |
|---|---|---|---|---|

## Hiring log row (`org/hiring-log.md`)

| Role | Skill or agent (repo, path, commit) | Score /30 | Runner-up | Why |
|---|---|---|---|---|

## Job brief (the subagent's prompt)

```text
ROLE: <title>, held to the bar of the best <title> in the industry
MISSION: <one sentence tied to the DoD items it owns>
CONTEXT: <3–6 lines; paths to upstream outputs, not their contents>
SKILLS TO LOAD FIRST: <names or paths from the hiring log>
METHOD: Karpathy rules: state assumptions first, simplest solution,
        surgical changes only, loop until the success criteria pass
INPUTS: <exact files/data>
OUTPUTS: <exact files, formats, locations>
SUCCESS CRITERIA: <tests/metrics/checks that prove it works>
QUALITY BAR: <role-specific bar from the playbook>
BOUNDARIES: <files and tools it may touch; what it must not touch>
HANDOFF (≤200 words): assumptions, what was done, evidence
        (command and result, or paths), open risks, confidence (high/med/low)
```

## Plan (`org/plan.md`)

```markdown
## Milestones (all), each with its outcome, gate and lane
## Current milestone, broken into tasks (break later ones down when they start)
| Task (2–15 min) | Owner | Output | Check | Depends on | Lane |
## Metric DoD items → Optimization lab
## Risks (top 5): risk → likelihood/impact → mitigation
```

## ADR (`org/adr/NNN-title.md`)

```markdown
# NNN Title
Status: accepted | Context: <why a decision was needed>
Decision: <what> | Consequences: <tradeoffs accepted>
```
