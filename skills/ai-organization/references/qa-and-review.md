# Independent QA and review board

## QA Lead

The QA Lead is a fresh agent. It gets only the brief, the DoD and the deliverables, never the build transcripts. Not knowing how the work was made is the point.

- Write a test plan that maps 1:1 to the DoD.
- **Software:** unit, integration and end-to-end tests (Playwright via `webapp-testing` or the Playwright MCP), edge cases, error paths, accessibility, a performance smoke test, and a security scan (dependencies and secrets). Confirm that CI is green on the exact commit being shipped.
- **Metrics:** re-run the locked eval scripts and confirm the Optimization lab's numbers.
- **Research:** spot-check citations, check claims against their sources, and flag overreach.
- **Video:** audit frames, check specs with ffprobe, check audio levels, and verify the captions.
- **Output** (`org/qa.md`): PASS or FAIL per DoD item, with evidence (command output, screenshots, frames).

**Bug loop:** each failure goes back to its owner with repro steps. After the fix, QA re-tests the affected items plus a regression smoke test. After 3 failed rounds on the same item, stop and escalate to the CEO with options.

## Principal Reviewer (review board)

1. **Process audit:** were assumptions stated, was the simplest solution chosen, were the diffs surgical, and is every criterion backed by evidence?
2. **Adversarial critique:** what would a demanding client or a top expert reject? List the blockers separately from the nice-to-haves.
3. The CEO grades each DoD item. Ship only when every item passes, or when the user has explicitly accepted a known gap.

## Retro (`org/retro.md`)

Which hires and skills did best, which underperformed, where tokens or time were wasted, and what to hire or do differently next time. List rostered skills that no role used, so they can be removed.
