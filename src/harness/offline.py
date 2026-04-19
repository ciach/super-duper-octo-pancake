from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class ScriptedFunctionCall:
    name: str
    arguments: str
    call_id: str
    type: str = "function_call"


@dataclass(slots=True)
class ScriptedResponse:
    id: str
    output: list[Any]
    output_text: str = ""
    usage: dict[str, int] | None = None


class ScriptedResponses:
    def __init__(self, script: dict[str, Any]):
        self._script = script
        self._index = 0
        self.calls: list[dict[str, Any]] = []

    def create(self, **kwargs: Any) -> ScriptedResponse:
        self.calls.append(kwargs)
        rounds = self._script.get("rounds", [])
        if self._index < len(rounds):
            calls = [
                ScriptedFunctionCall(
                    name=item["name"],
                    arguments=item.get("arguments", "{}"),
                    call_id=item.get("call_id", f"call_{self._index}_{offset}"),
                )
                for offset, item in enumerate(rounds[self._index])
            ]
            response = ScriptedResponse(
                id=f"resp_{self._index}",
                output=calls,
                usage={"input_tokens": 0, "output_tokens": 0},
            )
        else:
            response = ScriptedResponse(
                id=f"resp_{self._index}",
                output=[],
                output_text=self._script.get("final_output", ""),
                usage={"input_tokens": 0, "output_tokens": 0},
            )
        self._index += 1
        return response


class ScriptedResponsesClient:
    def __init__(self, script: dict[str, Any]):
        self.responses = ScriptedResponses(script)

