from __future__ import annotations

import unittest

from harness.cases import HarnessCase
from harness.evaluator import evaluate_case


class EvaluatorTests(unittest.TestCase):
    def test_checks_json_subset_and_tool_calls(self) -> None:
        case = HarnessCase(
            id="case",
            input="input",
            expected={
                "must_call": ["lookup_charge"],
                "contains": ["refunded"],
                "json": {"status": "refunded"},
            },
        )

        result = evaluate_case(case, '{"status":"refunded","extra":true}', ["lookup_charge"])

        self.assertTrue(result.passed)
        self.assertEqual([], result.failures)

    def test_reports_missing_expectations(self) -> None:
        case = HarnessCase(
            id="case",
            input="input",
            expected={"must_call": ["issue_refund"], "json": {"status": "refunded"}},
        )

        result = evaluate_case(case, '{"status":"ticket_created"}', ["lookup_charge"])

        self.assertFalse(result.passed)
        self.assertEqual(2, len(result.failures))


if __name__ == "__main__":
    unittest.main()

