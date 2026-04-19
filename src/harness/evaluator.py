from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from harness.cases import HarnessCase


@dataclass(slots=True)
class Evaluation:
    passed: bool
    failures: list[str]


def evaluate_case(case: HarnessCase, output_text: str, called_tools: list[str]) -> Evaluation:
    expected = case.expected
    failures: list[str] = []
    folded_output = output_text.lower()

    for needle in expected.get("contains", []):
        if needle.lower() not in folded_output:
            failures.append(f"output missing expected text {needle!r}")

    for needle in expected.get("not_contains", []):
        if needle.lower() in folded_output:
            failures.append(f"output contained forbidden text {needle!r}")

    for tool_name in expected.get("must_call", []):
        if tool_name not in called_tools:
            failures.append(f"tool {tool_name!r} was not called")

    for tool_name in expected.get("must_not_call", []):
        if tool_name in called_tools:
            failures.append(f"tool {tool_name!r} should not have been called")

    if "json" in expected:
        parsed = _parse_json_output(output_text)
        if parsed is None:
            failures.append("output was not parseable JSON")
        else:
            failures.extend(_compare_json_subset(parsed, expected["json"]))

    return Evaluation(passed=not failures, failures=failures)


def _parse_json_output(output_text: str) -> dict[str, Any] | None:
    candidate = output_text.strip()
    if candidate.startswith("```"):
        lines = candidate.splitlines()
        if len(lines) >= 3:
            candidate = "\n".join(lines[1:-1]).strip()
            if candidate.startswith("json"):
                candidate = candidate[4:].strip()
    try:
        value = json.loads(candidate)
    except json.JSONDecodeError:
        return None
    return value if isinstance(value, dict) else None


def _compare_json_subset(actual: dict[str, Any], expected: dict[str, Any], prefix: str = "") -> list[str]:
    failures: list[str] = []
    for key, expected_value in expected.items():
        path = f"{prefix}.{key}" if prefix else key
        if key not in actual:
            failures.append(f"json missing key {path!r}")
            continue
        actual_value = actual[key]
        if isinstance(expected_value, dict) and isinstance(actual_value, dict):
            failures.extend(_compare_json_subset(actual_value, expected_value, path))
        elif actual_value != expected_value:
            failures.append(f"json key {path!r}: expected {expected_value!r}, got {actual_value!r}")
    return failures

