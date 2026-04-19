from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any

from harness.cases import get_case, load_cases
from harness.offline import ScriptedResponsesClient
from harness.runner import RunResult, run_case
from harness.tools import build_tool_registry

DEFAULT_CASES = Path("examples/cases/stripe_minions.jsonl")
DEFAULT_MODEL = "gpt-5.4"


def main(argv: list[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)

    if args.command == "list-tools":
        return _list_tools()
    if args.command == "show-case":
        return _show_case(args)
    if args.command == "run":
        return _run(args)

    parser.print_help()
    return 2


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="openai-harness")
    subparsers = parser.add_subparsers(dest="command")

    run = subparsers.add_parser("run", help="Run harness cases")
    run.add_argument("--cases", default=str(DEFAULT_CASES), help="Path to JSONL cases")
    run.add_argument("--case-id", action="append", help="Run only a specific case ID")
    run.add_argument("--offline", action="store_true", help="Use scripted offline case responses")
    run.add_argument("--json", action="store_true", help="Print machine-readable JSON")
    run.add_argument("--max-tool-rounds", type=int, default=4)
    run.add_argument("--model", default=os.getenv("OPENAI_MODEL", DEFAULT_MODEL))
    run.add_argument(
        "--reasoning-effort",
        default=os.getenv("OPENAI_REASONING_EFFORT", "none"),
        choices=["none", "low", "medium", "high", "xhigh"],
    )

    show = subparsers.add_parser("show-case", help="Print one loaded case")
    show.add_argument("case_id")
    show.add_argument("--cases", default=str(DEFAULT_CASES))

    subparsers.add_parser("list-tools", help="List registered tool names")
    return parser


def _run(args: argparse.Namespace) -> int:
    cases = load_cases(args.cases)
    selected = set(args.case_id or [])
    if selected:
        cases = [case for case in cases if case.id in selected]
        missing = selected.difference(case.id for case in cases)
        if missing:
            raise SystemExit(f"unknown case id(s): {', '.join(sorted(missing))}")

    results: list[RunResult] = []
    for case in cases:
        client = _client_for_case(case, args.offline)
        result = run_case(
            case,
            client=client,
            model=args.model,
            reasoning_effort=args.reasoning_effort,
            max_tool_rounds=args.max_tool_rounds,
        )
        results.append(result)

    if args.json:
        print(json.dumps([_result_json(result) for result in results], indent=2))
    else:
        _print_results(results)

    return 0 if all(result.passed for result in results) else 1


def _client_for_case(case: Any, offline: bool) -> Any:
    if offline:
        if not case.offline:
            raise SystemExit(f"{case.id}: no offline script defined")
        return ScriptedResponsesClient(case.offline)

    if not os.getenv("OPENAI_API_KEY"):
        raise SystemExit("OPENAI_API_KEY is required for live runs; use --offline for CI-safe checks")

    from openai import OpenAI

    return OpenAI()


def _print_results(results: list[RunResult]) -> None:
    for result in results:
        status = "PASS" if result.passed else "FAIL"
        tools = ", ".join(call.name for call in result.tool_calls) or "none"
        print(f"{status} {result.case_id}")
        print(f"  tools: {tools}")
        if result.output_text:
            print(f"  output: {result.output_text}")
        for failure in result.failures:
            print(f"  failure: {failure}")


def _result_json(result: RunResult) -> dict[str, Any]:
    payload = asdict(result)
    payload["tool_calls"] = [asdict(call) for call in result.tool_calls]
    return payload


def _show_case(args: argparse.Namespace) -> int:
    case = get_case(load_cases(args.cases), args.case_id)
    print(json.dumps(asdict(case), indent=2))
    return 0


def _list_tools() -> int:
    for name in sorted(build_tool_registry()):
        print(name)
    return 0


if __name__ == "__main__":
    sys.exit(main())

