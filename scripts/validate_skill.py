#!/usr/bin/env python3
"""Validate every skill under skills/: frontmatter, size budget, and reference links.

Standard library only, so it runs anywhere with no install step.
Usage: python3 scripts/validate_skill.py [--max-tokens N]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")
LINK_RE = re.compile(r"`(references/[\w./-]+\.md)`")


def est_tokens(text: str) -> int:
    # About 4 characters per token for English prose. Good enough for a budget gate.
    return round(len(text) / 4)


def parse_frontmatter(text: str) -> tuple[dict | None, str]:
    if not text.startswith("---\n"):
        return None, text
    end = text.find("\n---\n", 4)
    if end == -1:
        return None, text
    fields = {}
    for line in text[4:end].splitlines():
        if ":" in line and not line.startswith(" "):
            key, _, value = line.partition(":")
            fields[key.strip()] = value.strip().strip('"')
    return fields, text[end + 5 :]


def check_skill(skill_dir: Path, max_tokens: int) -> list[str]:
    errors = []
    skill_md = skill_dir / "SKILL.md"
    text = skill_md.read_text(encoding="utf-8")
    fm, body = parse_frontmatter(text)
    if fm is None:
        return [f"{skill_md}: missing YAML frontmatter"]

    name = fm.get("name", "")
    desc = fm.get("description", "")
    if not NAME_RE.match(name) or len(name) > 64:
        errors.append(f"name '{name}' must be kebab-case and at most 64 chars")
    if name != skill_dir.name:
        errors.append(f"name '{name}' must match folder '{skill_dir.name}'")
    if not desc:
        errors.append("description is empty")
    elif len(desc) > 1024:
        errors.append(f"description is {len(desc)} chars (max 1024)")
    if re.search(r"<[^>]+>", desc):
        errors.append("description must not contain XML/HTML tags")

    lines = body.count("\n") + 1
    tokens = est_tokens(body)
    if lines > 500:
        errors.append(f"SKILL.md body is {lines} lines (max 500)")
    if tokens > max_tokens:
        errors.append(f"SKILL.md body is ~{tokens} tokens (budget {max_tokens})")

    linked = set(LINK_RE.findall(body))
    for rel in sorted(linked):
        if not (skill_dir / rel).is_file():
            errors.append(f"SKILL.md links to missing file {rel}")
    refs_dir = skill_dir / "references"
    if refs_dir.is_dir():
        for ref in sorted(refs_dir.rglob("*.md")):
            rel = ref.relative_to(skill_dir).as_posix()
            if rel not in linked:
                errors.append(f"{rel} is never referenced from SKILL.md (orphan)")
            if ref.parent != refs_dir:
                errors.append(f"{rel} is nested; keep references one level deep")

    ref_tokens = sum(est_tokens(p.read_text(encoding="utf-8")) for p in refs_dir.rglob("*.md")) if refs_dir.is_dir() else 0
    print(
        f"{name}: body {lines} lines, ~{tokens} tokens on trigger; "
        f"description {len(desc)} chars; references ~{ref_tokens} tokens (loaded on demand)"
    )
    return errors


def check_release_metadata(root: Path) -> list[str]:
    """plugin.json, marketplace.json, CHANGELOG.md and CITATION.cff must agree."""
    errors = []
    try:
        plugin = json.loads((root / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
        market = json.loads((root / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"cannot read plugin manifests: {exc}"]

    version = plugin.get("version", "")
    if not SEMVER_RE.match(version):
        errors.append(f"plugin.json version '{version}' is not semver X.Y.Z")
    names = [p.get("name") for p in market.get("plugins", [])]
    if plugin.get("name") not in names:
        errors.append(f"marketplace.json does not list plugin '{plugin.get('name')}'")

    changelog = root / "CHANGELOG.md"
    if not changelog.is_file() or not re.search(rf"^## {re.escape(version)}\b", changelog.read_text(encoding="utf-8"), re.M):
        errors.append(f"CHANGELOG.md has no '## {version}' section")
    citation = root / "CITATION.cff"
    if citation.is_file() and not re.search(rf"^version: {re.escape(version)}$", citation.read_text(encoding="utf-8"), re.M):
        errors.append(f"CITATION.cff version does not match {version}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    # v0 of ai-organization loaded ~4351 tokens on trigger; the budget holds v1+ to at most half of that.
    parser.add_argument("--max-tokens", type=int, default=2175)
    args = parser.parse_args()

    skill_dirs = sorted(p.parent for p in (ROOT / "skills").glob("*/SKILL.md"))
    if not skill_dirs:
        print("no skills found under skills/", file=sys.stderr)
        return 1
    failed = False
    for skill_dir in skill_dirs:
        for err in check_skill(skill_dir, args.max_tokens):
            print(f"ERROR {skill_dir.name}: {err}", file=sys.stderr)
            failed = True
    for err in check_release_metadata(ROOT):
        print(f"ERROR release metadata: {err}", file=sys.stderr)
        failed = True
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
