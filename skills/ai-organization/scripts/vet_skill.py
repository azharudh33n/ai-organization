#!/usr/bin/env python3
"""Vetting gate for a third-party skill listed on skills.sh.

Run it (don't read it):  python3 scripts/vet_skill.py <owner>/<repo> <skill-name>

It reads two public facts and decides, so the decision does not rest on a model's
reading of the skill's own text:
  1. the independent security audits skills.sh publishes for the skill
  2. whether the publisher is a GitHub organization with a verified domain

Verdict (also the exit code):
  approved (0)  every audit passes at low risk or below, and the publisher is verified
  ask      (2)  audits are clean but the publisher is unverified, or an audit warns:
                a person must approve before the skill is installed
  rejected (1)  an audit fails or reports high risk, there are no audits, or a lookup
                failed (the gate fails closed)

Standard library only.
"""
from __future__ import annotations

import json
import os
import re
import sys
import urllib.error
import urllib.request

AUDIT_URL = "https://skills.sh/api/v1/skills/audit/{source}/{skill}"
ORG_URL = "https://api.github.com/orgs/{owner}"
TIMEOUT_SECONDS = 15
NAME_RE = re.compile(r"^[A-Za-z0-9._-]+$")
LOW_RISK = {"NONE", "SAFE", "LOW"}
BLOCKING_RISK = {"HIGH", "CRITICAL"}


def decide(audits: list[dict], publisher_verified: bool) -> tuple[str, list[str]]:
    """Turn audit records and the publisher check into a verdict and its reasons."""
    if not audits:
        return "rejected", ["no security audits exist for this skill"]

    reasons: list[str] = []
    needs_person = False
    for audit in audits:
        provider = audit.get("provider", "unknown")
        status = str(audit.get("status", "")).lower()
        risk = str(audit.get("riskLevel") or "").upper()
        if status == "fail" or risk in BLOCKING_RISK:
            return "rejected", [f"{provider}: {status or 'no status'} {risk}".strip()]
        if status != "pass" or (risk and risk not in LOW_RISK):
            needs_person = True
            reasons.append(f"{provider}: {status or 'no status'} {risk}".strip())

    if not publisher_verified:
        needs_person = True
        reasons.append("publisher is not a verified GitHub organization")
    if needs_person:
        return "ask", reasons
    return "approved", [f"{len(audits)} audits pass at low risk or below; publisher verified"]


def fetch_json(url: str, token: str | None = None) -> dict | None:
    """GET a JSON document. Returns None on 404; raises OSError on any other failure."""
    request = urllib.request.Request(url, headers={"Accept": "application/json", "User-Agent": "vet-skill"})
    if token:
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

    github_token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    try:
        audit_doc = fetch_json(AUDIT_URL.format(source=f"{owner}/{repo}", skill=skill))
        org_doc = fetch_json(ORG_URL.format(owner=owner), github_token)
    except OSError as exc:
        print(f"rejected: lookup failed, so the gate fails closed ({exc})")
        return 1

    audits = (audit_doc or {}).get("audits", [])
    verified = bool(org_doc and org_doc.get("is_verified"))
    verdict, reasons = decide(audits, verified)
    print(f"{verdict}: {owner}/{repo} {skill}")
    for reason in reasons:
        print(f"  - {reason}")
    return {"approved": 0, "ask": 2, "rejected": 1}[verdict]


if __name__ == "__main__":
    sys.exit(main(sys.argv))
