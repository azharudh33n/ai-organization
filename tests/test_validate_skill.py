"""Unit tests for scripts/validate_skill.py (standard library only)."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import validate_skill as vs  # noqa: E402

GOOD_DESC = "Does a thing. Use when the user asks for the thing."


def write_skill(root: Path, name: str = "demo", desc: str = GOOD_DESC, body: str = "Body.\n", refs: dict | None = None) -> Path:
    skill = root / "skills" / name
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text(f"---\nname: {name}\ndescription: {desc}\n---\n\n{body}", encoding="utf-8")
    for rel, text in (refs or {}).items():
        path = skill / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    return skill


def write_release(root: Path, version: str = "1.2.3", changelog_version: str | None = None, listed: str = "demo") -> None:
    meta = root / ".claude-plugin"
    meta.mkdir(parents=True, exist_ok=True)
    (meta / "plugin.json").write_text(json.dumps({"name": "demo", "version": version}), encoding="utf-8")
    (meta / "marketplace.json").write_text(json.dumps({"name": "m", "owner": {"name": "o"}, "plugins": [{"name": listed, "source": "./"}]}), encoding="utf-8")
    (root / "CHANGELOG.md").write_text(f"# Changelog\n\n## {changelog_version or version} (2026-01-01)\n", encoding="utf-8")


class CheckSkillTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_valid_skill_passes(self) -> None:
        skill = write_skill(self.root, body="See `references/a.md`.\n", refs={"references/a.md": "# A\n"})
        self.assertEqual(vs.check_skill(skill, 2000), [])

    def test_name_must_match_folder(self) -> None:
        skill = write_skill(self.root, name="demo")
        (skill / "SKILL.md").write_text(f"---\nname: other\ndescription: {GOOD_DESC}\n---\n", encoding="utf-8")
        self.assertTrue(any("must match folder" in e for e in vs.check_skill(skill, 2000)))

    def test_name_must_be_kebab_case(self) -> None:
        skill = write_skill(self.root, name="Bad_Name")
        self.assertTrue(any("kebab-case" in e for e in vs.check_skill(skill, 2000)))

    def test_description_length_limit(self) -> None:
        skill = write_skill(self.root, desc="x" * 1025)
        self.assertTrue(any("max 1024" in e for e in vs.check_skill(skill, 2000)))

    def test_description_rejects_xml_tags(self) -> None:
        skill = write_skill(self.root, desc="Use <b>this</b> skill")
        self.assertTrue(any("XML/HTML" in e for e in vs.check_skill(skill, 2000)))

    def test_token_budget_enforced(self) -> None:
        skill = write_skill(self.root, body="word " * 2000)
        self.assertTrue(any("budget" in e for e in vs.check_skill(skill, 500)))

    def test_missing_reference_flagged(self) -> None:
        skill = write_skill(self.root, body="See `references/missing.md`.\n")
        self.assertTrue(any("missing file" in e for e in vs.check_skill(skill, 2000)))

    def test_orphan_reference_flagged(self) -> None:
        skill = write_skill(self.root, refs={"references/orphan.md": "# O\n"})
        self.assertTrue(any("orphan" in e for e in vs.check_skill(skill, 2000)))

    def test_nested_reference_flagged(self) -> None:
        skill = write_skill(self.root, body="See `references/deep/x.md`.\n", refs={"references/deep/x.md": "# X\n"})
        self.assertTrue(any("one level deep" in e for e in vs.check_skill(skill, 2000)))

    def test_missing_frontmatter(self) -> None:
        skill = self.root / "skills" / "demo"
        skill.mkdir(parents=True)
        (skill / "SKILL.md").write_text("# no frontmatter\n", encoding="utf-8")
        self.assertTrue(any("frontmatter" in e for e in vs.check_skill(skill, 2000)))


class ReleaseMetadataTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_consistent_metadata_passes(self) -> None:
        write_release(self.root)
        self.assertEqual(vs.check_release_metadata(self.root), [])

    def test_changelog_must_have_version(self) -> None:
        write_release(self.root, changelog_version="1.2.2")
        self.assertTrue(any("CHANGELOG" in e for e in vs.check_release_metadata(self.root)))

    def test_version_must_be_semver(self) -> None:
        write_release(self.root, version="v1")
        self.assertTrue(any("semver" in e for e in vs.check_release_metadata(self.root)))

    def test_marketplace_must_list_plugin(self) -> None:
        write_release(self.root, listed="something-else")
        self.assertTrue(any("does not list" in e for e in vs.check_release_metadata(self.root)))

    def test_citation_version_must_match(self) -> None:
        write_release(self.root)
        (self.root / "CITATION.cff").write_text("version: 9.9.9\n", encoding="utf-8")
        self.assertTrue(any("CITATION" in e for e in vs.check_release_metadata(self.root)))


class RepoTests(unittest.TestCase):
    def test_this_repo_is_valid(self) -> None:
        root = Path(__file__).resolve().parent.parent
        for skill_md in (root / "skills").glob("*/SKILL.md"):
            self.assertEqual(vs.check_skill(skill_md.parent, 2175), [], skill_md)
        self.assertEqual(vs.check_release_metadata(root), [])


if __name__ == "__main__":
    unittest.main()
