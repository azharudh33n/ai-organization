#!/usr/bin/env python3
"""Vetting gate for a third-party skill listed on skills.sh.

Run it (don't read it):  python3 scripts/vet_skill.py <owner>/<repo> <skill-name>

It decides from outside facts, so the decision does not rest on a model's reading
of the skill's own text:
  1. the independent security audits skills.sh publishes for the skill
  2. whether those audits still describe the skill: an audit counts only if the
     skill's files have not changed between the commit that was current when the
     audit ran and the commit being vetted (GitHub's push log and diff)
  3. whether the publisher is a GitHub organization with a verified domain

Verdict (also the exit code):
  approved (0)  at least two current audits, all passing at low risk or below,
                and a verified publisher
  ask      (2)  an audit warns, only one audit is current, an earlier version
                failed an audit, or the publisher is unverified: a person must
                approve before the skill is installed
  rejected (1)  an audit fails or reports high risk, no audit covers the current
                version, or a lookup failed (the gate fails closed)

It prints the commit it vetted. Install that exact commit, not whatever is newest.
Set GITHUB_TOKEN to raise GitHub's rate limit when vetting several skills.

Standard library only.
"""
from __future__ import annotations

import json
import os
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime
from typing import Callable

AUDIT_URL = "https://skills.sh/api/v1/skills/audit/{source}/{skill}"
GITHUB = "https://api.github.com"
TIMEOUT_SECONDS = 15
NAME_RE = re.compile(r"^[A-Za-z0-9._-]+$")
LOW_RISK = {"NONE", "SAFE", "LOW"}
BLOCKING_RISK = {"HIGH", "CRITICAL"}
MIN_CURRENT_AUDITS = 2  # one scanner alone is not "independent audits"
PUSH_LOG_PAGES = 3  # 300 pushes back; older audits are treated as out of date
COMPARE_FILE_LIMIT = 300  # GitHub lists at most this many files per comparison

Fetch = Callable[[str], object]


def is_blocking(audit: dict) -> bool:
    return str(audit.get("status", "")).lower() == "fail" or str(audit.get("riskLevel") or "").upper() in BLOCKING_RISK


def decide(audits: list[dict], publisher_verified: bool) -> tuple[str, list[str]]:
    """Turn the audits that cover the vetted commit, and the publisher check, into a verdict."""
    if not audits:
        return "rejected", ["no security audit covers the current version of this skill"]

    reasons: list[str] = []
    for audit in audits:
        provider = audit.get("provider", "unknown")
        status = str(audit.get("status", "")).lower()
        risk = str(audit.get("riskLevel") or "").upper()
        if is_blocking(audit):
            return "rejected", [f"{provider}: {status or 'no status'} {risk}".strip()]
        if status != "pass" or (risk and risk not in LOW_RISK):
            reasons.append(f"{provider}: {status or 'no status'} {risk}".strip())

    if len(audits) < MIN_CURRENT_AUDITS:
        reasons.append(f"only {len(audits)} audit covers the current version (need {MIN_CURRENT_AUDITS})")
    if not publisher_verified:
        reasons.append("publisher is not a verified GitHub organization")
    if reasons:
        return "ask", reasons
    return "approved", [f"{len(audits)} current audits pass at low risk or below; publisher verified"]


def parse_time(value: object) -> datetime | None:
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None


def find_skill_dir(paths: list[str], skill: str) -> str | None:
    """The skill's folder, when exactly one folder named after the skill holds a SKILL.md."""
    suffix = f"{skill}/SKILL.md"
    matches = [p[: -len("/SKILL.md")] for p in paths if p == suffix or p.endswith("/" + suffix)]
    return matches[0] if len(matches) == 1 else None


def head_at(pushes: list[dict], when: datetime) -> str | None:
    """Branch tip after the latest push at or before `when`. `pushes` is newest first."""
    for push in pushes:
        pushed = parse_time(push.get("timestamp"))
        if pushed and pushed <= when:
            return push.get("after")
    return None


def touches_skill(changed_files: list[str], skill_dir: str | None) -> bool:
    """True if a change affects the skill. Unknown folder: any change in the repo counts."""
    if skill_dir is None:
        return bool(changed_files)
    return any(path.startswith(skill_dir + "/") for path in changed_files)


def current_audits(audits: list[dict], pushes: list[dict], head: str, skill_dir: str | None, changed_between: Callable[[str, str], list[str] | None]) -> tuple[list[dict], list[dict]]:
    """Split audits into those whose scanned version of the skill is the same as at `head`, and the rest."""
    kept: list[dict] = []
    outdated: list[dict] = []
    unchanged_since: dict[str, bool] = {head: True}
    for audit in audits:
        audited = parse_time(audit.get("auditedAt"))
        base = head_at(pushes, audited) if audited else None
        if base is None:
            outdated.append(audit)
            continue
        if base not in unchanged_since:
            changed = changed_between(base, head)
            unchanged_since[base] = changed is not None and not touches_skill(changed, skill_dir)
        (kept if unchanged_since[base] else outdated).append(audit)
    return kept, outdated


def vet(owner: str, repo: str, skill: str, fetch: Fetch) -> tuple[str, list[str], str | None]:
    """Run the whole gate. `fetch(url)` returns parsed JSON, or None for a 404."""
    audit_doc = fetch(AUDIT_URL.format(source=f"{owner}/{repo}", skill=skill))
    audits = audit_doc.get("audits", []) if isinstance(audit_doc, dict) else []
    if not audits:
        return "rejected", ["no security audits exist for this skill"], None

    repo_doc = fetch(f"{GITHUB}/repos/{owner}/{repo}")
    if not isinstance(repo_doc, dict):
        return "rejected", ["source repository not found on GitHub"], None
    branch = repo_doc["default_branch"]
    head = fetch(f"{GITHUB}/repos/{owner}/{repo}/commits/{branch}")["sha"]
    tree = fetch(f"{GITHUB}/repos/{owner}/{repo}/git/trees/{head}?recursive=1") or {}
    skill_dir = find_skill_dir([entry["path"] for entry in tree.get("tree", [])], skill)

    pushes: list[dict] = []
    for page in range(1, PUSH_LOG_PAGES + 1):
        batch = fetch(f"{GITHUB}/repos/{owner}/{repo}/activity?ref=refs/heads/{branch}&per_page=100&page={page}") or []
        pushes.extend(batch)
        if len(batch) < 100:
            break

    def changed_between(base: str, tip: str) -> list[str] | None:
        diff = fetch(f"{GITHUB}/repos/{owner}/{repo}/compare/{base}...{tip}")
        if not isinstance(diff, dict) or diff.get("status") not in ("ahead", "identical"):
            return None  # rewritten history or missing commit: cannot prove it is unchanged
        files = [f["filename"] for f in diff.get("files", [])]
        return None if len(files) >= COMPARE_FILE_LIMIT else files

    kept, outdated = current_audits(audits, pushes, head, skill_dir, changed_between)
    org_doc = fetch(f"{GITHUB}/orgs/{owner}")
    verified = isinstance(org_doc, dict) and bool(org_doc.get("is_verified"))
    verdict, reasons = decide(kept, verified)
    if outdated:
        reasons.append(f"{len(outdated)} older audit(s) not counted: the skill changed after they ran")
    failed_before = [a.get("provider", "unknown") for a in outdated if is_blocking(a)]
    if failed_before and verdict == "approved":
        # Newer audits pass, but nothing shows the earlier failure was fixed: a person decides.
        verdict = "ask"
        reasons.insert(0, f"an earlier version failed {', '.join(failed_before)}")
    return verdict, reasons, head


def fetch_json(url: str) -> object:
    """GET a JSON document. Returns None on 404; raises OSError on any other failure."""
    request = urllib.request.Request(url, headers={"Accept": "application/json", "User-Agent": "vet-skill"})
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token and url.startswith(GITHUB + "/"):
        request.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            return json.load(response)
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return None
        raise OSError(f"{url} returned HTTP {exc.code}") from exc
    except json.JSONDecodeError as exc:
        raise OSError(f"{url} did not return JSON") from exc


def main(argv: list[str]) -> int:
    if len(argv) != 3 or argv[1].count("/") != 1:
        print("usage: vet_skill.py <owner>/<repo> <skill-name>", file=sys.stderr)
        return 1
    owner, repo = argv[1].split("/")
    skill = argv[2]
    if not all(NAME_RE.match(part) for part in (owner, repo, skill)):
        print("rejected: names may contain only letters, digits, dot, dash and underscore", file=sys.stderr)
        return 1

    try:
        verdict, reasons, commit = vet(owner, repo, skill, fetch_json)
    except (OSError, KeyError, TypeError) as exc:
        print(f"rejected: lookup failed, so the gate fails closed ({exc!r})")
        return 1

    print(f"{verdict}: {owner}/{repo} {skill}")
    for reason in reasons:
        print(f"  - {reason}")
    if commit and verdict != "rejected":
        print(f"  vetted commit: {owner}/{repo}@{commit}")
    return {"approved": 0, "ask": 2, "rejected": 1}[verdict]


if __name__ == "__main__":
    sys.exit(main(sys.argv))
