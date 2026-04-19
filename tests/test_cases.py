from __future__ import annotations

import unittest

from harness.cases import load_cases


class CaseLoadingTests(unittest.TestCase):
    def test_loads_example_cases(self) -> None:
        cases = load_cases("examples/cases/stripe_minions.jsonl")

        self.assertEqual(["stripe_refund_minion", "stripe_ticket_minion"], [case.id for case in cases])
        self.assertEqual("support_decision", cases[0].response_schema)
        self.assertIn("lookup_charge", cases[0].tools)


if __name__ == "__main__":
    unittest.main()

