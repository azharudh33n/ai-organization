"""A SKILL.md counts as "not this skill" only when its declared name is beyond doubt (no network)."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "skills" / "ai-organization" / "scripts"))
import vet_skill as vet  # noqa: E402


def doc(*lines: str) -> str:
    return "---\n" + "\n".join(lines) + "\n---\nbody\n"


class UnambiguousNames(unittest.TestCase):
    def test_reads_a_name_with_windows_line_endings(self) -> None:
        self.assertEqual(vet.frontmatter_name("---\r\nname: demo\r\ndescription: x\r\n---\r\n"), "demo")

    def test_reads_a_name_with_extra_spaces_around_the_value(self) -> None:
        self.assertEqual(vet.frontmatter_name(doc("name:   demo  ")), "demo")

    def test_reads_a_single_quoted_name(self) -> None:
        self.assertEqual(vet.frontmatter_name(doc("name: 'demo'")), "demo")


class NamesAYamlParserCouldReadDifferently(unittest.TestCase):
    def assert_unreadable(self, *lines: str) -> None:
        self.assertIsNone(vet.frontmatter_name(doc(*lines)))

    def test_refuses_a_trailing_comment(self) -> None:
        self.assert_unreadable("name: demo # the real name")

    def test_refuses_an_anchor(self) -> None:
        self.assert_unreadable("name: &n demo")

    def test_refuses_a_tag(self) -> None:
        self.assert_unreadable("name: !!str demo")

    def test_refuses_an_escape_in_double_quotes(self) -> None:
        self.assert_unreadable('name: "de\\x6do"')

    def test_refuses_a_folded_value(self) -> None:
        self.assert_unreadable("name: >", "  demo")

    def test_refuses_a_quoted_key_next_to_a_plain_one(self) -> None:
        self.assert_unreadable("name: other", '"name": demo')

    def test_refuses_indented_keys(self) -> None:
        self.assert_unreadable("  name: demo", "  description: x")

    def test_refuses_a_second_name_nested_under_another_key(self) -> None:
        self.assert_unreadable("name: other", "metadata:", "  name: demo")

    def test_refuses_a_merge_key(self) -> None:
        self.assert_unreadable("name: other", "<<: *base")

    def test_refuses_a_flow_mapping(self) -> None:
        self.assert_unreadable("{name: demo, description: x}")

    def test_refuses_a_space_before_the_colon(self) -> None:
        self.assert_unreadable("name : demo")

    def test_refuses_a_byte_order_mark(self) -> None:
        self.assertIsNone(vet.frontmatter_name("﻿" + doc("name: demo")))

    def test_refuses_a_closing_line_that_is_not_exactly_three_dashes(self) -> None:
        self.assertIsNone(vet.frontmatter_name("---\nname: other\n----\nname: demo\n"))


class DoubtCountsAgainstApproval(unittest.TestCase):
    def test_a_file_with_a_doubtful_name_makes_the_skill_folder_uncertain(self) -> None:
        files = {"skills/demo/SKILL.md": doc("name: demo"), "skills/evil/SKILL.md": doc("name: demo # hidden")}
        self.assertIsNone(vet.resolve_skill_dir(files, "demo"))

    def test_a_clean_different_name_does_not(self) -> None:
        files = {"skills/demo/SKILL.md": doc("name: demo"), "skills/other/SKILL.md": doc("name: other")}
        self.assertEqual(vet.resolve_skill_dir(files, "demo"), "skills/demo")

    def test_a_lowercase_skill_file_is_still_a_skill_file(self) -> None:
        self.assertTrue(vet.is_skill_file("skills/evil/skill.md"))
        self.assertTrue(vet.is_skill_file("SKILL.md"))
        self.assertFalse(vet.is_skill_file("skills/demo/NOT-SKILL.md"))


if __name__ == "__main__":
    unittest.main()
