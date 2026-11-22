# Karpathy Loop and ML recipe

## The loop (after `karpathy/autoresearch`)

Use it whenever a DoD item is a number: performance, bundle size, Lighthouse score, conversion copy, prompt quality, model accuracy or cost.

**Setup (before the first experiment):**

- `program.md`: the goal, the metric and its target, the editable scope, the budget, and ideas to try. The CEO drafts it and the user approves it. After that it is frozen, and agents read it but don't rewrite it.
- A **locked eval script** and **one metric** to beat. A different role writes and locks the eval (QA, or the benchmark or eval owner). The Optimization Engineer who tunes against it can run it but never edit it.
- **One editable scope** (a file or module). Everything else is read-only.
- A **fixed budget** per experiment and in total (time, runs or tokens).

**Loop:**

1. Record a baseline (run it at least 3 times if the metric is noisy).
2. Commit the current best, propose one change, run it and measure it.
3. Keep the change only if it beats the current best by more than the noise. Otherwise restore the editable scope to the last kept commit (`git restore --source=<best-commit> -- <scope>`).
4. Log every attempt in `org/experiments.tsv`: `id  commit  change  metric  kept(y/n)  note`.
5. Stop at the target or when the budget runs out. Report the best result, its commit, and what worked and what didn't.

**Guardrails:** never edit the eval to win. Watch for gains that only come from overfitting the eval set, and keep a held-out check when you can.

## Neural-net training recipe (Data/ML hires)

1. Become one with the data: look at real examples, distributions and label noise.
2. Build an end-to-end skeleton with dumb baselines and fixed seeds.
3. Overfit a small batch to prove the pipeline can learn.
4. Regularize, then tune (with the loop above), then squeeze out the last gains.

Never skip the baselines. Visualize inputs and predictions at every stage, and never trust a metric you haven't sanity-checked against real examples. For from-scratch understanding, see `karpathy/nanoGPT`, `nanochat` and `micrograd`.
