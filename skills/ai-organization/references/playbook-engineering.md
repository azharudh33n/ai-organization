# Engineering playbook

The flow follows `obra/superpowers` with Karpathy's rules on top. If superpowers isn't installed, follow the same steps by hand.

1. **Spec** (`brainstorming`): write the requirements, assumptions and tradeoffs before any code.
2. **Plan** (`writing-plans`): break the work into small tasks, each with exact files and a test command.
3. **Isolate** (`using-git-worktrees`): one worktree or branch per parallel lane, so agents never edit the same files.
4. **TDD** (`test-driven-development`): red → green → refactor. The builder's unit tests drive the design. The acceptance tests for DoD items belong to QA, not to the builder.
5. **Implement** (`subagent-driven-development` / `executing-plans`): write the simplest code that passes, touching only the files in scope.
6. **Debug** (`systematic-debugging`): find the root cause before you change anything. A reproduction comes first.
7. **Review** (`requesting-code-review`): a senior reviewer who didn't write the code checks correctness, security, readability and performance.
8. **Diff audit**: the reviewer rejects any change outside the task's scope, any abstraction nobody asked for, and any line that doesn't trace back to a success criterion.
9. **Verify** (`verification-before-completion`): run the full test suite, lint, type-check and build, and paste the output as evidence.

**Quality bar:** all tests green; no lint or type errors; the smallest diff that does the job; no secrets in code or logs; inputs validated where they enter the system; errors handled, not swallowed; a README that says how to run it.

**Sensitive data:** when the project handles personal, health or payment data, hire a dedicated security and privacy reviewer rather than folding that work into a general code reviewer.

**Security basics for every web deliverable:** validate input on the server, encode output for its context, check authorization on the server for every request, keep secrets out of client bundles, and rate-limit any form that sends email or writes data.

**Context saving:** one agent maps the codebase (entry points, key modules, test commands) into `org/codebase-map.md`. Every other engineer reads that map instead of exploring again.
