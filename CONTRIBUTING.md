# Contributing

Thanks for helping improve ai-organization.

## Ground rules

- Keep `SKILL.md` lean. The validator enforces a token budget of about 2,175 tokens. New detail belongs in `skills/ai-organization/references/`, linked from `SKILL.md` with a note on when to read it.
- Explain *why* in instructions rather than adding all-caps MUSTs.
- One logical change per PR. Use [Conventional Commits](https://www.conventionalcommits.org/) subjects (`feat:`, `fix:`, `docs:`, `ci:`).

## Before you open a PR

```bash
python3 scripts/validate_skill.py
python3 -m unittest discover -s tests
npx --yes markdownlint-cli2@0.19.0 "**/*.md" "!evals/**"
claude plugin validate . --strict
```

If you change skill behaviour, run the eval suite and paste the before and after numbers into the PR. These are real, billed runs:

```bash
claude plugin eval . --allow-tools Write,Edit
```

## Adding an eval case

Add a folder under `evals/<case-name>/` with `prompt.md`, `case.yaml` and one grader file per assertion in `graders/`. Copy an existing case. Assertions must be objectively checkable from the output.

## Releasing (maintainers)

1. Bump `version` in `.claude-plugin/plugin.json` and add a `## X.Y.Z` section to `CHANGELOG.md`. CI checks that the two match.
2. Tag and push: `git tag vX.Y.Z && git push origin vX.Y.Z`. The release workflow builds the skill zip, attests its provenance and publishes the release.
