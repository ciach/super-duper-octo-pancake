from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class HarnessCase:
    id: str
    input: str
    instructions: str | None = None
    tools: list[str] = field(default_factory=list)
    response_schema: str | dict[str, Any] | None = None
    expected: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    offline: dict[str, Any] = field(default_factory=dict)


def load_cases(path: str | Path) -> list[HarnessCase]:
    case_path = Path(path)
    seen: set[str] = set()
    cases: list[HarnessCase] = []

    with case_path.open("r", encoding="utf-8") as handle:
        for line_number, raw_line in enumerate(handle, start=1):
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue

            payload = json.loads(line)
            case = HarnessCase(
                id=_required_str(payload, "id", line_number),
                input=_required_str(payload, "input", line_number),
                instructions=payload.get("instructions"),
                tools=list(payload.get("tools", [])),
                response_schema=payload.get("response_schema"),
                expected=dict(payload.get("expected", {})),
                metadata=dict(payload.get("metadata", {})),
                offline=dict(payload.get("offline", {})),
            )
            if case.id in seen:
                raise ValueError(f"{case_path}:{line_number}: duplicate case id {case.id!r}")
            seen.add(case.id)
            cases.append(case)

    if not cases:
        raise ValueError(f"{case_path}: no cases found")
    return cases


def get_case(cases: list[HarnessCase], case_id: str) -> HarnessCase:
    for case in cases:
        if case.id == case_id:
            return case
    raise KeyError(f"unknown case id {case_id!r}")


def _required_str(payload: dict[str, Any], key: str, line_number: int) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"line {line_number}: {key!r} must be a non-empty string")
    return value

