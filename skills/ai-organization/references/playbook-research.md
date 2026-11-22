# Research playbook

How top investigative researchers work:

1. **Frame the question.** Split it into 3–7 sub-questions. For each one, say which answer would change the decision. Drop the sub-questions that wouldn't change it.
2. **Go to primary sources first:** official docs, papers, filings, specs, source code, changelogs and maintainer statements. Use secondary sources only to find primary ones.
3. **Triangulate.** Confirm each key claim with at least 2 independent sources. Record the publication date of each, and prefer the most recent for anything that changes over time (prices, versions, benchmarks).
4. **Try to prove yourself wrong.** Look for disconfirming evidence and alternative explanations, and record what you looked for.
5. **Output:** findings, each with a citation (URL and date) and a confidence level (high/med/low), plus contradictions, gaps and what would change the conclusion.
6. **Fact-check independently.** A separate fact-checker re-verifies the top 10 claims before anyone builds on them.

**Benchmarks inside research:** treat a benchmark as an experiment, not an anecdote. Fix the dataset, hardware and harness before tuning. Name one primary metric (for example recall@10 at a p95 latency budget) and run a baseline configuration. Report variance across at least 3 runs. Use the Karpathy Loop (`karpathy-loop.md`) for any tuning. Never present numbers you haven't measured. In a plan or dry run, write "to be measured".

**Quality bar:** every claim traceable to a dated source; recommendations tied to the stated constraints; uncertainty stated plainly.
