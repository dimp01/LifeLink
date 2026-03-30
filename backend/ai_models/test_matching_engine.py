#!/usr/bin/env python3
"""Unit tests for pure-Python matching engine.

These tests avoid database usage by relying on mocked donor/recipient objects.
Run from backend directory:
    python -m unittest -v test_matching_engine.py
"""

import unittest
from dataclasses import dataclass

from matching_engine import compute_match_score, rank_recipients


@dataclass
class MockDonor:
    id: str
    blood_group: str | None = None
    organs_selected: list[str] | None = None
    location: str | None = None


@dataclass
class MockRecipient:
    id: str
    urgency: str | None = None
    blood_group: str | None = None
    organ_needed: list[str] | None = None


class TestMatchingEngine(unittest.TestCase):
    def setUp(self):
        self.donor = MockDonor(
            id="donor-1",
            blood_group="O+",
            organs_selected=["Kidney", "Liver"],
            location="Bangalore",
        )

    def test_rank_recipients_orders_by_score_desc(self):
        recipients = [
            MockRecipient(id="r-low", urgency="standard", blood_group="AB-", organ_needed=["Heart"]),
            MockRecipient(id="r-mid", urgency="high", blood_group="O+", organ_needed=["Liver"]),
            MockRecipient(id="r-top", urgency="urgent", blood_group="O+", organ_needed=["Kidney", "Liver"]),
        ]

        ranked = rank_recipients(self.donor, recipients)

        self.assertEqual(len(ranked), 3)
        self.assertEqual(ranked[0]["recipient_id"], "r-top")
        self.assertGreaterEqual(ranked[0]["score"], ranked[1]["score"])
        self.assertGreaterEqual(ranked[1]["score"], ranked[2]["score"])

    def test_no_recipients_returns_empty_list(self):
        ranked = rank_recipients(self.donor, [])
        self.assertEqual(ranked, [])

    def test_missing_data_is_gracefully_handled(self):
        donor_missing = MockDonor(id="d-missing", blood_group=None, organs_selected=None)
        recipient_missing = MockRecipient(id="r-missing", urgency=None, blood_group=None, organ_needed=None)

        result = compute_match_score(donor_missing, recipient_missing)

        self.assertEqual(result["recipient_id"], "r-missing")
        self.assertIn("score", result)
        self.assertGreaterEqual(result["score"], 0.0)
        self.assertLessEqual(result["score"], 1.0)
        self.assertIn("explanation", result)
        self.assertIn("components", result["explanation"])

    def test_higher_urgency_increases_score_when_compatibility_same(self):
        recipient_standard = MockRecipient(
            id="r-standard",
            urgency="standard",
            blood_group="O+",
            organ_needed=["Kidney"],
        )
        recipient_urgent = MockRecipient(
            id="r-urgent",
            urgency="urgent",
            blood_group="O+",
            organ_needed=["Kidney"],
        )

        score_standard = compute_match_score(self.donor, recipient_standard)["score"]
        score_urgent = compute_match_score(self.donor, recipient_urgent)["score"]

        self.assertGreater(score_urgent, score_standard)

    def test_better_organ_compatibility_increases_score_when_urgency_same(self):
        recipient_partial = MockRecipient(
            id="r-partial",
            urgency="high",
            blood_group="O+",
            organ_needed=["Kidney", "Heart"],
        )
        recipient_full = MockRecipient(
            id="r-full",
            urgency="high",
            blood_group="O+",
            organ_needed=["Kidney", "Liver"],
        )

        score_partial = compute_match_score(self.donor, recipient_partial)["score"]
        score_full = compute_match_score(self.donor, recipient_full)["score"]

        self.assertGreater(score_full, score_partial)

    def test_score_is_deterministic_for_same_inputs(self):
        recipient = MockRecipient(
            id="r-det",
            urgency="high",
            blood_group="O+",
            organ_needed=["Liver"],
        )

        first = compute_match_score(self.donor, recipient)
        second = compute_match_score(self.donor, recipient)

        self.assertEqual(first["score"], second["score"])
        self.assertEqual(first["explanation"]["components"], second["explanation"]["components"])

    def test_survival_component_is_optional_and_non_breaking(self):
        recipient = MockRecipient(
            id="r-survival",
            urgency="high",
            blood_group="O+",
            organ_needed=["Kidney"],
        )

        without_survival = compute_match_score(self.donor, recipient, include_survival=False)
        with_survival = compute_match_score(
            self.donor,
            recipient,
            include_survival=True,
            use_mock_if_unavailable=True,
        )

        self.assertIn("survival_score", with_survival["explanation"]["components"])
        self.assertIn("survival_source", with_survival["explanation"]["components"])
        self.assertGreaterEqual(with_survival["score"], 0.0)
        self.assertLessEqual(with_survival["score"], 1.0)
        self.assertGreaterEqual(without_survival["score"], 0.0)
        self.assertLessEqual(without_survival["score"], 1.0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
