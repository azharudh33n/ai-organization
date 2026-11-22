"""The gate must judge the folder and commit that get installed, not an older or different one (no network).

Each test builds a fake repository in two states: OLD, the commit that was current when
the audits ran on 1 May, and HEAD, pushed on 1 June. A folder maps to a content hash,
the way git trees do: the hash changes exactly when something inside the folder changes.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "skills" / "ai-organization" / "scripts"))
import vet_skill as vet  # noqa: E402

OLD, HEAD = "a" * 40, "b" * 40
MAY_AUDITS = [
    {"provider": "Snyk", "status": "pass", "riskLevel": "LOW", "auditedAt": "2026-05-01T00:00:00Z"},
    {"provider": "Socket", "status": "pass", "auditedAt": "2026-05-01T00:00:00.000Z"},
]
DEMO = {"skills/demo": ("demo", "v1")}  # folder -> (declared name, content version)


def tree(folders: dict[str, tuple[str | None, str]], links_in: str | None = None, truncated: bool = False) -> dict:
    entries = []
    for folder, (_, version) in folders.items():
        entries.append({"path": folder, "type": "tree", "mode": "040000", "sha": f"{folder}@{version}"})
        entries.append({"path": f"{folder}/SKILL.md", "type": "blob", "mode": "100644", "sha": "blob"})
    if links_in:
        entries.append({"path": f"{links_in}/shared.sh", "type": "blob", "mode": "120000", "sha": "link"})
    root = "|".join(sorted(e["sha"] for e in entries if e["type"] == "tree"))
    return {"sha": root, "truncated": truncated, "tree": entries}


def run(skill: str = "demo", old: dict | None = None, head: dict | None = None, audits: list[dict] | None = None, verified: bool = True, old_tree: dict | None = None, links_in: str | None = None):
    old = DEMO if old is None else old
    head = DEMO if head is None else head
    audits = MAY_AUDITS if audits is None else audits

    def fetch(url: str) -> object:
        if "skills.sh" in url:
            return {"audits": audits}
        if url.endswith("/repos/acme/skills"):
            return {"default_branch": "main"}
        if url.endswith("/commits/main"):
            return {"sha": HEAD}
        if f"/git/trees/{HEAD}" in url:
            return tree(head, links_in)
        if f"/git/trees/{OLD}" in url:
            return old_tree if old_tree is not None else tree(old, links_in)
        if "/activity" in url:
            return [{"timestamp": "2026-06-01T00:00:00Z", "after": HEAD}, {"timestamp": "2026-04-01T00:00:00Z", "after": OLD}]
        if url.endswith("/orgs/acme"):
            return {"is_verified": verified}
        raise AssertionError(f"unexpected url {url}")

    def fetch_text(url: str) -> str | None:
        folder = url.split(f"/{HEAD}/", 1)[1][: -len("/SKILL.md")]
        name = head[folder][0]
        return "no frontmatter here" if name is None else f"---\nname: {name}\ndescription: x\n---\nbody\n"

    return vet.vet("acme", "skills", skill, fetch, fetch_text)


class AuditsMustCoverTheInstalledCommit(unittest.TestCase):
    def test_rejects_when_the_skill_changed_after_every_audit(self) -> None:
        verdict, reasons, _, _ = run(head={"skills/demo": ("demo", "v2")})
        self.assertEqual(verdict, "rejected")
        self.assertTrue(any("changed after" in r for r in reasons))

    def test_approves_when_only_other_folders_changed_since_the_audits(self) -> None:
        old = {**DEMO, "skills/other": ("other", "v1")}
        head = {**DEMO, "skills/other": ("other", "v2")}
        verdict, _, commit, path = run(old=old, head=head)
        self.assertEqual(verdict, "approved")
        self.assertEqual(commit, HEAD)
        self.assertEqual(path, "skills/demo/SKILL.md")

    def test_a_sibling_folder_with_the_same_prefix_does_not_count_as_the_skill(self) -> None:
        old = {**DEMO, "skills/demo-extra": ("demo-extra", "v1")}
        head = {**DEMO, "skills/demo-extra": ("demo-extra", "v2")}
        self.assertEqual(run(old=old, head=head)[0], "approved")

    def test_rejects_when_the_audited_commit_cannot_be_listed(self) -> None:
        verdict, _, _, _ = run(old_tree=tree(DEMO, truncated=True))
        self.assertEqual(verdict, "rejected")

    def test_asks_when_only_one_audit_covers_the_current_version(self) -> None:
        audits = [
            {"provider": "Snyk", "status": "pass", "riskLevel": "LOW", "auditedAt": "2026-07-01T00:00:00Z"},
            {"provider": "Socket", "status": "pass", "auditedAt": "2026-05-01T00:00:00Z"},
        ]
        verdict, reasons, _, _ = run(head={"skills/demo": ("demo", "v2")}, audits=audits)
        self.assertEqual(verdict, "ask")
        self.assertTrue(any("only 1 audit" in r for r in reasons))

    def test_asks_when_an_earlier_version_failed_even_though_current_audits_pass(self) -> None:
        audits = [
            {"provider": "Snyk", "status": "pass", "riskLevel": "LOW", "auditedAt": "2026-07-01T00:00:00Z"},
            {"provider": "Socket", "status": "pass", "auditedAt": "2026-07-01T00:00:00Z"},
            {"provider": "Runlayer", "status": "fail", "riskLevel": "HIGH", "auditedAt": "2026-05-01T00:00:00Z"},
        ]
        verdict, reasons, _, _ = run(head={"skills/demo": ("demo", "v2")}, audits=audits)
        self.assertEqual(verdict, "ask")
        self.assertTrue(any("earlier version failed Runlayer" in r for r in reasons))

    def test_an_audit_older_than_the_push_log_is_not_counted(self) -> None:
        audits = [{"provider": "Snyk", "status": "pass", "riskLevel": "LOW", "auditedAt": "2020-01-01T00:00:00Z"}]
        self.assertEqual(run(audits=audits)[0], "rejected")

    def test_rejects_a_skill_with_no_audits_without_calling_github(self) -> None:
        def fetch(url: str) -> object:
            if "skills.sh" in url:
                return None
            raise AssertionError("GitHub should not be queried")

        verdict, _, commit, _ = vet.vet("acme", "skills", "demo", fetch, lambda url: None)
        self.assertEqual(verdict, "rejected")
        self.assertIsNone(commit)


class TheVettedFolderMustBeTheOneInstalled(unittest.TestCase):
    """The installer picks a skill by the name declared in SKILL.md, not by its folder name."""

    def test_never_approves_when_another_folder_declares_the_same_skill_name(self) -> None:
        repo = {"skills/demo": ("something-else", "v1"), "skills/evil": ("demo", "v1")}
        verdict, reasons, _, path = run(old=repo, head=repo)
        self.assertEqual(verdict, "ask")
        self.assertIsNone(path)
        self.assertTrue(any("which folder" in r for r in reasons))

    def test_rejects_when_the_folder_that_declares_the_name_changed_after_the_audits(self) -> None:
        old = {"skills/demo": ("something-else", "v1"), "skills/evil": ("demo", "v1")}
        head = {"skills/demo": ("something-else", "v1"), "skills/evil": ("demo", "v2")}
        self.assertEqual(run(old=old, head=head)[0], "rejected")

    def test_approves_a_skill_whose_folder_is_named_differently_when_the_name_is_unique(self) -> None:
        repo = {"skills/react": ("demo", "v1"), "skills/other": ("other", "v1")}
        verdict, _, _, path = run(old=repo, head=repo)
        self.assertEqual(verdict, "approved")
        self.assertEqual(path, "skills/react/SKILL.md")

    def test_never_approves_when_a_skill_file_in_the_repo_has_no_readable_name(self) -> None:
        repo = {**DEMO, "skills/mystery": (None, "v1")}
        self.assertEqual(run(old=repo, head=repo)[0], "ask")

    def test_any_repo_change_counts_when_the_skill_folder_cannot_be_found(self) -> None:
        old = {**DEMO, "skills/other": ("other", "v1")}
        head = {**DEMO, "skills/other": ("other", "v2")}
        self.assertEqual(run(skill="not-in-this-repo", old=old, head=head)[0], "rejected")

    def test_rejects_when_a_skill_with_links_has_changes_outside_its_folder(self) -> None:
        old = {**DEMO, "shared": ("shared", "v1")}
        head = {**DEMO, "shared": ("shared", "v2")}
        self.assertEqual(run(old=old, head=head, links_in="skills/demo")[0], "rejected")

    def test_approves_a_skill_with_links_when_nothing_in_the_repo_changed(self) -> None:
        repo = {**DEMO, "shared": ("shared", "v1")}
        self.assertEqual(run(old=repo, head=repo, links_in="skills/demo")[0], "approved")


class FrontmatterNameTests(unittest.TestCase):
    def test_reads_a_plain_or_quoted_name(self) -> None:
        self.assertEqual(vet.frontmatter_name("---\nname: demo\n---\n"), "demo")
        self.assertEqual(vet.frontmatter_name('---\nname: "demo"\n---\n'), "demo")

    def test_refuses_a_name_declared_twice(self) -> None:
        self.assertIsNone(vet.frontmatter_name("---\nname: demo\nname: other\n---\n"))

    def test_refuses_text_without_frontmatter(self) -> None:
        self.assertIsNone(vet.frontmatter_name("# just a heading\nname: demo\n"))


if __name__ == "__main__":
    unittest.main()
