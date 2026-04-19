from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from harness.cases import HarnessCase
from harness.evaluator import evaluate_case
from harness.schemas import response_text_format
from harness.tools import ToolDefinition, call_tool, select_tools

DEFAULT_INSTRUCTIONS = (
    "You are running a regression harness. Follow the case instructions exactly, "
    "use provided tools when needed, and keep the final answer concise."
)


@dataclass(slots=True)
class ToolCallRecord:
    name: str
    arguments: str
    call_id: str
    output: str


@dataclass(slots=True)
class RunResult:
    case_id: str
    passed: bool
    output_text: str
    failures: list[str]
    tool_calls: list[ToolCallRecord]
    response_id: str | None = None
    usage: dict[str, Any] | None = None


def run_cases(
    cases: list[HarnessCase],
    client: Any,
    model: str,
    reasoning_effort: str | None = "none",
    max_tool_rounds: int = 4,
) -> list[RunResult]:
    return [
        run_case(
            case,
            client=client,
            model=model,
            reasoning_effort=reasoning_effort,
            max_tool_rounds=max_tool_rounds,
        )
        for case in cases
    ]


def run_case(
    case: HarnessCase,
    client: Any,
    model: str,
    reasoning_effort: str | None = "none",
    max_tool_rounds: int = 4,
    registry: dict[str, ToolDefinition] | None = None,
) -> RunResult:
    tools = select_tools(case.tools, registry)
    called: list[ToolCallRecord] = []
    input_items: list[Any] = [{"role": "user", "content": case.input}]
    response = _create_response(
        client,
        case=case,
        model=model,
        tools=tools,
        input_items=input_items,
        reasoning_effort=reasoning_effort,
    )
    response_id = _response_id(response)
    replay_items = input_items + list(getattr(response, "output", []))

    for _ in range(max_tool_rounds):
        function_calls = _extract_function_calls(response)
        if not function_calls:
            break

        tool_outputs = []
        for item in function_calls:
            if item.name not in tools:
                raise KeyError(f"model called unknown tool {item.name!r}")
            output = call_tool(tools[item.name], item.arguments)
            called.append(
                ToolCallRecord(
                    name=item.name,
                    arguments=item.arguments,
                    call_id=item.call_id,
                    output=output,
                )
            )
            tool_outputs.append(
                {
                    "type": "function_call_output",
                    "call_id": item.call_id,
                    "output": output,
                }
            )

        response = _create_response(
            client,
            case=case,
            model=model,
            tools=tools,
            input_items=tool_outputs if response_id else replay_items + tool_outputs,
            reasoning_effort=reasoning_effort,
            previous_response_id=response_id,
        )
        response_id = _response_id(response)
        replay_items += tool_outputs + list(getattr(response, "output", []))
    else:
        raise RuntimeError(f"{case.id}: exceeded max tool rounds ({max_tool_rounds})")

    output_text = _output_text(response)
    evaluation = evaluate_case(case, output_text, [item.name for item in called])
    return RunResult(
        case_id=case.id,
        passed=evaluation.passed,
        output_text=output_text,
        failures=evaluation.failures,
        tool_calls=called,
        response_id=response_id,
        usage=_usage(response),
    )


def _create_response(
    client: Any,
    case: HarnessCase,
    model: str,
    tools: dict[str, ToolDefinition],
    input_items: list[Any],
    reasoning_effort: str | None,
    previous_response_id: str | None = None,
) -> Any:
    kwargs: dict[str, Any] = {
        "model": model,
        "instructions": case.instructions or DEFAULT_INSTRUCTIONS,
        "input": input_items,
    }
    if tools:
        kwargs["tools"] = [tool.as_openai_tool() for tool in tools.values()]
    if previous_response_id:
        kwargs["previous_response_id"] = previous_response_id
    if reasoning_effort:
        kwargs["reasoning"] = {"effort": reasoning_effort}

    text = response_text_format(case.response_schema)
    if text is not None:
        kwargs["text"] = text

    return client.responses.create(**kwargs)


def _extract_function_calls(response: Any) -> list[Any]:
    return [
        item
        for item in getattr(response, "output", [])
        if getattr(item, "type", None) == "function_call"
    ]


def _output_text(response: Any) -> str:
    value = getattr(response, "output_text", None)
    if isinstance(value, str):
        return value

    chunks: list[str] = []
    for item in getattr(response, "output", []):
        for content in getattr(item, "content", []) or []:
            text = getattr(content, "text", None)
            if isinstance(text, str):
                chunks.append(text)
    return "".join(chunks)


def _response_id(response: Any) -> str | None:
    value = getattr(response, "id", None)
    return value if isinstance(value, str) else None


def _usage(response: Any) -> dict[str, Any] | None:
    usage = getattr(response, "usage", None)
    if usage is None:
        return None
    if isinstance(usage, dict):
        return usage
    dump = getattr(usage, "model_dump", None)
    if callable(dump):
        return dump()
    return None

