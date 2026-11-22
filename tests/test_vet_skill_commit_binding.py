"""The gate must judge the commit that gets installed, not an older scanned version (no network)."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "skills" / "ai-organization" / "scripts"))
import vet_skill as vet  # noqa: E402

OLD, HEAD = "a" * 40, "b" * 40
SKILL_DIR = "skills/demo"


def fake_fetch(changed_files: list[str], audits: list[dict] | None = None, verified: bool = True, compare_status: str = "ahead"):
    """A fetch() that serves a repo whose HEAD moved from OLD to HEAD on 1 June, after audits run on 1 May."""
    if audits is None:
        audits = [
            {"provider": "Snyk", "status": "pass", "riskLevel": "LOW", "auditedAt": "2026-05-01T00:00:00Z"},
            {"provider": "Socket", "status": "pass", "auditedAt": "2026-05-01T00:00:00.000Z"},
        ]

    def fetch(url: str) -> object:
        if "skills.sh" in url:
            return {"audits": audits}
        if url.endswith("/repos/acme/skills"):
            return {"default_branch": "main"}
        if url.endswith("/commits/main"):
            return {"sha": HEAD}
        if "/git/trees/" in url:
            return {"tree": [{"path": f"{SKILL_DIR}/SKILL.md"}, {"path": "skills/other/SKILL.md"}]}
        if "/activity" in url:
            return [
                {"timestamp": "2026-06-01T00:00:00Z", "after": HEAD},
                {"timestamp": "2026-04-01T00:00:00Z", "after": OLD},
            ]
        if "/compare/" in url:
            return {"status": compare_status, "files": [{"filename": name} for name in changed_files]}
        if url.endswith("/orgs/acme"):
            return {"is_verified": verified}
        raise AssertionError(f"unexpected url {url}")

    return fetch


class CommitBindingTests(unittest.TestCase):
    def test_rejects_when_the_skill_changed_after_every_audit(self) -> None:
        verdict, reasons, _ = vet.vet("acme", "skills", "demo", fake_fetch([f"{SKILL_DIR}/SKILL.md"]))
        self.assertEqual(verdict, "rejected")
        self.assertTrue(any("changed after" in r for r in reasons))

    def test_approves_when_only_other_folders_changed_since_the_audits(self) -> None:
        verdict, _, commit = vet.vet("acme", "skills", "demo", fake_fetch(["skills/other/SKILL.md", "README.md"]))
        self.assertEqual(verdict, "approved")
        self.assertEqual(commit, HEAD)

    def test_a_sibling_folder_with_the_same_prefix_does_not_count_as_the_skill(self) -> None:
        verdict, _, _ = vet.vet("acme", "skills", "demo", fake_fetch(["skills/demo-extra/SKILL.md"]))
        self.assertEqual(verdict, "approved")

    def test_rejects_when_history_was_rewritten_since_the_audits(self) -> None:
        verdict, _, _ = vet.vet("acme", "skills", "demo", fake_fetch([], compare_status="diverged"))
        self.assertEqual(verdict, "rejected")

    def test_any_repo_change_counts_when_the_skill_folder_cannot_be_found(self) -> None:
        verdict, _, _ = vet.vet("acme", "skills", "renamed-skill", fake_fetch(["README.md"]))
        self.assertEqual(verdict, "rejected")

    def test_asks_when_only_one_audit_covers_the_current_version(self) -> None:
        audits = [
            {"provider": "Snyk", "status": "pass", "riskLevel": "LOW", "auditedAt": "2026-07-01T00:00:00Z"},
            {"provider": "Socket", "status": "pass", "auditedAt": "2026-05-01T00:00:00Z"},
        ]
        verdict, reasons, _ = vet.vet("acme", "skills", "demo", fake_fetch([f"{SKILL_DIR}/SKILL.md"], audits=audits))
        self.assertEqual(verdict, "ask")
        self.assertTrue(any("only 1 audit" in r for r in reasons))

    def test_asks_when_an_earlier_version_failed_even_though_current_audits_pass(self) -> None:
        audits = [
            {"provider": "Snyk", "status": "pass", "riskLevel": "LOW", "auditedAt": "2026-07-01T00:00:00Z"},
            {"provider": "Socket", "status": "pass", "auditedAt": "2026-07-01T00:00:00Z"},
            {"provider": "Runlayer", "status": "fail", "riskLevel": "HIGH", "auditedAt": "2026-05-01T00:00:00Z"},
        ]
        verdict, reasons, _ = vet.vet("acme", "skills", "demo", fake_fetch([f"{SKILL_DIR}/SKILL.md"], audits=audits))
        self.assertEqual(verdict, "ask")
        self.assertTrue(any("earlier version failed Runlayer" in r for r in reasons))

    def test_an_audit_older_than_the_push_log_is_not_counted(self) -> None:
        audits = [{"provider": "Snyk", "status": "pass", "riskLevel": "LOW", "auditedAt": "2020-01-01T00:00:00Z"}]
        verdict, _, _ = vet.vet("acme", "skills", "demo", fake_fetch([], audits=audits))
        self.assertEqual(verdict, "rejected")

    def test_rejects_a_skill_with_no_audits_without_calling_github(self) -> None:
        def fetch(url: str) -> object:
            if "skills.sh" in url:
                return None
            raise AssertionError("GitHub should not be queried")

        verdict, _, commit = vet.vet("acme", "skills", "demo", fetch)
        self.assertEqual(verdict, "rejected")
        self.assertIsNone(commit)


if __name__ == "__main__":
    unittest.main()
