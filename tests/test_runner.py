from __future__ import annotations

import unittest

from harness.cases import load_cases
from harness.offline import ScriptedResponsesClient
from harness.runner import run_case


class RunnerTests(unittest.TestCase):
    def test_runs_scripted_case_through_tool_loop(self) -> None:
        case = load_cases("examples/cases/stripe_minions.jsonl")[0]
        client = ScriptedResponsesClient(case.offline)

        result = run_case(case, client=client, model="gpt-5.4", reasoning_effort="none")

        self.assertTrue(result.passed, result.failures)
        self.assertEqual(["lookup_charge", "issue_refund"], [call.name for call in result.tool_calls])
        self.assertEqual("resp_2", result.response_id)

    def test_uses_previous_response_id_after_first_response(self) -> None:
        case = load_cases("examples/cases/stripe_minions.jsonl")[0]
        client = ScriptedResponsesClient(case.offline)

        run_case(case, client=client, model="gpt-5.4", reasoning_effort="low")

        calls = client.responses.calls
        self.assertNotIn("previous_response_id", calls[0])
        self.assertEqual("resp_0", calls[1]["previous_response_id"])
        self.assertEqual("resp_1", calls[2]["previous_response_id"])
        self.assertEqual({"effort": "low"}, calls[0]["reasoning"])
        self.assertEqual("json_schema", calls[0]["text"]["format"]["type"])


if __name__ == "__main__":
    unittest.main()

