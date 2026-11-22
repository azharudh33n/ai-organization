#!/usr/bin/env python3
"""Vetting gate for a third-party skill listed on skills.sh.

Run it (don't read it):  python3 scripts/vet_skill.py <owner>/<repo> <skill-name>

It decides from outside facts, so the decision does not rest on a model's reading
of the skill's own text:
  1. the independent security audits skills.sh publishes for the skill
  2. whether those audits still describe the skill: an audit counts only if the
     skill's folder has the same git content hash at the commit that was current
     when the audit ran and at the commit being vetted
  3. whether the publisher is a GitHub organization with a verified domain

Verdict (also the exit code):
  approved (0)  at least two current audits, all passing at low risk or below,
                a verified publisher, and exactly one folder that can be this skill
  ask      (2)  an audit warns, only one audit is current, an earlier version
                failed an audit, the publisher is unverified, or the skill's
                folder is ambiguous: a person must approve before it is installed
  rejected (1)  an audit fails or reports high risk, no audit covers the current
                version, or a lookup failed (the gate fails closed)

It prints the commit and path it vetted. Install that exact commit.
Set GITHUB_TOKEN to raise GitHub's rate limit when vetting several skills.

Standard library only.
"""
from __future__ import annotations

import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from typing import Callable

AUDIT_URL = "https://skills.sh/api/v1/skills/audit/{source}/{skill}"
GITHUB = "https://api.github.com"
RAW = "https://raw.githubusercontent.com"
TIMEOUT_SECONDS = 15
NAME_RE = re.compile(r"^[A-Za-z0-9._-]+$")
LOW_RISK = {"NONE", "SAFE", "LOW"}
BLOCKING_RISK = {"HIGH", "CRITICAL"}
MIN_CURRENT_AUDITS = 2  # one scanner alone is not "independent audits"
PUSH_LOG_PAGES = 3  # 300 pushes back; older audits are treated as out of date
MAX_SKILL_FILES = 60  # more SKILL.md files than this: don't try to tell them apart
MAX_TEXT_BYTES = 65536
LINK_MODES = {"120000", "160000"}  # symlink, submodule: content that lives elsewhere
WHOLE_REPO = ""
FRONTMATTER_RE = re.compile(r"\A---[ \t]*\n(.*?)\n---[ \t]*(?:\n|\Z)", re.S)
NAME_KEY_RE = re.compile(r"""^\s*["']?name["']?\s*:""", re.I)
PLAIN_NAME_RE = re.compile(r"""^name:[ \t]+(["']?)([A-Za-z0-9][A-Za-z0-9._-]*)\1[ \t]*$""")

FetchJson = Callable[[str], object]
FetchText = Callable[[str], "str | None"]


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


def frontmatter_name(text: str | None) -> str | None:
    """The skill's declared name, only when no YAML parser could read it differently.

    This is not a YAML parser, and the installer uses a real one. So it accepts a single
    spelling: one top-level `name:` line whose value is a plain token of letters, digits,
    dot, dash and underscore, optionally in matching quotes. Comments, anchors, tags,
    escapes, multi-line values, merge keys, flow mappings, indented or repeated name keys
    and a byte-order mark all return None, which callers treat as "this file might be
    the skill".
    """
    if not text:
        return None
    match = FRONTMATTER_RE.match(text.replace("\r\n", "\n").replace("\r", "\n"))
    if not match:
        return None
    lines = match.group(1).split("\n")
    if any(line.lstrip().startswith(("<<", "{", "%")) for line in lines):
        return None
    name_lines = [line for line in lines if NAME_KEY_RE.match(line)]
    if len(name_lines) != 1:
        return None
    plain = PLAIN_NAME_RE.match(name_lines[0])
    return plain.group(2) if plain else None


def is_skill_file(path: str) -> bool:
    """SKILL.md in any letter case: some filesystems would open `skill.md` for it."""
    return path.rsplit("/", 1)[-1].lower() == "skill.md"


def resolve_skill_dir(skill_files: dict[str, str | None], skill: str) -> str | None:
    """The one folder that can be this skill, or None when that is not certain.

    The installer picks a skill by the name in its SKILL.md, not by its folder, so
    a folder name alone proves nothing. Every SKILL.md that could be taken for the
    skill is a candidate: its folder is named after the skill, its declared name
    matches, or its name cannot be read. The answer is certain only when there is
    one candidate and it declares exactly this name.
    """
    candidates: list[tuple[str, str | None]] = []
    for path, text in skill_files.items():
        folder = path[: -len("SKILL.md")].rstrip("/")
        name = frontmatter_name(text)
        if name is None or name.lower() == skill.lower() or folder.rsplit("/", 1)[-1].lower() == skill.lower():
            candidates.append((folder, name))
    if len(candidates) == 1 and candidates[0][1] == skill:
        return candidates[0][0]
    return None


def tree_index(tree_doc: object) -> dict[str, dict] | None:
    """Map each path in a recursive git tree to its entry. None if the listing is missing or cut short."""
    if not isinstance(tree_doc, dict) or tree_doc.get("truncated") or "sha" not in tree_doc:
        return None
    index = {entry["path"]: entry for entry in tree_doc.get("tree", [])}
    index[WHOLE_REPO] = {"type": "tree", "sha": tree_doc["sha"]}
    return index


def has_links(index: dict[str, dict], folder: str) -> bool:
    """True if the folder holds a symlink or submodule, whose content lives outside it."""
    prefix = folder + "/" if folder else ""
    return any(entry.get("mode") in LINK_MODES for path, entry in index.items() if path and path.startswith(prefix))


def content_hash(index: dict[str, dict] | None, folder: str) -> str | None:
    """Git's hash of a folder's whole content: equal hashes mean identical files."""
    entry = (index or {}).get(folder)
    return entry.get("sha") if entry and entry.get("type") == "tree" else None


def head_at(pushes: list[dict], when: datetime) -> str | None:
    """Branch tip after the latest push at or before `when`. `pushes` is newest first."""
    for push in pushes:
        pushed = parse_time(push.get("timestamp"))
        if pushed and pushed <= when:
            return push.get("after")
    return None


def current_audits(audits: list[dict], pushes: list[dict], head: str, same_as_head: Callable[[str], bool]) -> tuple[list[dict], list[dict]]:
    """Split audits into those whose scanned version of the skill is the same as at `head`, and the rest."""
    kept: list[dict] = []
    outdated: list[dict] = []
    unchanged_since: dict[str, bool] = {}
    for audit in audits:
        audited = parse_time(audit.get("auditedAt"))
        base = head_at(pushes, audited) if audited else None
        if base is None:
            outdated.append(audit)
            continue
        if base not in unchanged_since:
            unchanged_since[base] = same_as_head(base)
        (kept if unchanged_since[base] else outdated).append(audit)
    return kept, outdated


def vet(owner: str, repo: str, skill: str, fetch: FetchJson, fetch_text: FetchText) -> tuple[str, list[str], str | None, str | None]:
    """Run the whole gate. Returns verdict, reasons, vetted commit and vetted SKILL.md path.

    `fetch(url)` returns parsed JSON and `fetch_text(url)` returns text; both return None for a 404.
    """
    audit_doc = fetch(AUDIT_URL.format(source=f"{owner}/{repo}", skill=skill))
    audits = audit_doc.get("audits", []) if isinstance(audit_doc, dict) else []
    if not audits:
        return "rejected", ["no security audits exist for this skill"], None, None

    repo_doc = fetch(f"{GITHUB}/repos/{owner}/{repo}")
    if not isinstance(repo_doc, dict):
        return "rejected", ["source repository not found on GitHub"], None, None
    branch = repo_doc["default_branch"]
    head = fetch(f"{GITHUB}/repos/{owner}/{repo}/commits/{branch}")["sha"]

    def tree_at(commit: str) -> dict[str, dict] | None:
        return tree_index(fetch(f"{GITHUB}/repos/{owner}/{repo}/git/trees/{commit}?recursive=1"))

    head_index = tree_at(head)
    if head_index is None:
        return "rejected", ["could not list the repository's files, so nothing can be verified"], None, None

    skill_paths = [path for path in head_index if is_skill_file(path)]
    folder = None
    if 0 < len(skill_paths) <= MAX_SKILL_FILES:
        texts = {path: fetch_text(f"{RAW}/{owner}/{repo}/{head}/{urllib.parse.quote(path)}") for path in skill_paths}
        folder = resolve_skill_dir(texts, skill)

    # Watch the skill's folder when it is certain and self-contained; otherwise watch the whole repository.
    scope = folder if folder is not None and not has_links(head_index, folder) else WHOLE_REPO
    head_hash = content_hash(head_index, scope)

    def same_as_head(base: str) -> bool:
        if base == head:
            return True
        base_hash = content_hash(tree_at(base), scope)
        return base_hash is not None and base_hash == head_hash

    pushes: list[dict] = []
    for page in range(1, PUSH_LOG_PAGES + 1):
        batch = fetch(f"{GITHUB}/repos/{owner}/{repo}/activity?ref=refs/heads/{branch}&per_page=100&page={page}") or []
        pushes.extend(batch)
        if len(batch) < 100:
            break

    kept, outdated = current_audits(audits, pushes, head, same_as_head)
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
    if folder is None and verdict == "approved":
        # The audits may describe a different folder than the one the installer would pick.
        verdict = "ask"
        reasons.insert(0, "cannot tell for certain which folder in the repository is this skill")

    path = f"{folder}/SKILL.md".lstrip("/") if folder is not None else None
    return verdict, reasons, head, path


def _open(url: str, limit: int | None = None) -> bytes | None:
    """GET a URL, reading at most `limit` bytes. Returns None on 404; raises OSError on any other failure."""
    request = urllib.request.Request(url, headers={"User-Agent": "vet-skill"})
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token and url.startswith(GITHUB + "/"):
        request.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            return response.read(limit)
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return None
        raise OSError(f"{url} returned HTTP {exc.code}") from exc


def fetch_json(url: str) -> object:
    body = _open(url)
    if body is None:
        return None
    try:
        return json.loads(body)
    except json.JSONDecodeError as exc:
        raise OSError(f"{url} did not return JSON") from exc


def fetch_text(url: str) -> str | None:
    body = _open(url, MAX_TEXT_BYTES)
    return None if body is None else body.decode("utf-8", errors="replace")


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
        verdict, reasons, commit, path = vet(owner, repo, skill, fetch_json, fetch_text)
    except (OSError, KeyError, TypeError) as exc:
        print(f"rejected: lookup failed, so the gate fails closed ({exc!r})")
        return 1

    print(f"{verdict}: {owner}/{repo} {skill}")
    for reason in reasons:
        print(f"  - {reason}")
    if commit and verdict != "rejected":
        print(f"  vetted commit: {owner}/{repo}@{commit}")
        if path:
            print(f"  vetted path: {path}")
    return {"approved": 0, "ask": 2, "rejected": 1}[verdict]


if __name__ == "__main__":
    sys.exit(main(sys.argv))
