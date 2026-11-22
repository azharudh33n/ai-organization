"""Unit tests for the vetting gate's decision rule (no network)."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "skills" / "ai-organization" / "scripts"))
import vet_skill as vet  # noqa: E402

PASS_LOW = {"provider": "Snyk", "status": "pass", "riskLevel": "LOW"}
PASS_NO_RISK_FIELD = {"provider": "Socket", "status": "pass"}
WARN_MEDIUM = {"provider": "Runlayer", "status": "warn", "riskLevel": "MEDIUM"}
FAIL_HIGH = {"provider": "Snyk", "status": "fail", "riskLevel": "HIGH"}


class DecideTests(unittest.TestCase):
    def test_approves_clean_audits_from_a_verified_publisher(self) -> None:
        verdict, _ = vet.decide([PASS_LOW, PASS_NO_RISK_FIELD], publisher_verified=True)
        self.assertEqual(verdict, "approved")

    def test_asks_when_publisher_is_unverified(self) -> None:
        verdict, reasons = vet.decide([PASS_LOW], publisher_verified=False)
        self.assertEqual(verdict, "ask")
        self.assertTrue(any("verified" in r for r in reasons))

    def test_asks_when_an_audit_warns(self) -> None:
        verdict, reasons = vet.decide([PASS_LOW, WARN_MEDIUM], publisher_verified=True)
        self.assertEqual(verdict, "ask")
        self.assertTrue(any("Runlayer" in r for r in reasons))

    def test_rejects_when_an_audit_fails(self) -> None:
        verdict, reasons = vet.decide([PASS_LOW, FAIL_HIGH], publisher_verified=True)
        self.assertEqual(verdict, "rejected")
        self.assertTrue(any("Snyk" in r for r in reasons))

    def test_rejects_high_risk_even_if_status_says_pass(self) -> None:
        verdict, _ = vet.decide([{"provider": "X", "status": "pass", "riskLevel": "CRITICAL"}], publisher_verified=True)
        self.assertEqual(verdict, "rejected")

    def test_rejects_when_there_are_no_audits(self) -> None:
        verdict, _ = vet.decide([], publisher_verified=True)
        self.assertEqual(verdict, "rejected")

    def test_asks_when_an_audit_has_no_status(self) -> None:
        verdict, _ = vet.decide([{"provider": "X"}], publisher_verified=True)
        self.assertEqual(verdict, "ask")


class ArgumentTests(unittest.TestCase):
    def test_rejects_names_that_could_alter_the_url(self) -> None:
        self.assertEqual(vet.main(["vet_skill.py", "owner/repo", "../../etc"]), 1)

    def test_rejects_missing_arguments(self) -> None:
        self.assertEqual(vet.main(["vet_skill.py", "owner-only"]), 1)


if __name__ == "__main__":
    unittest.main()
