# OpenAI Harness

A small, SDK-first harness for testing prompts, tool calling, and structured outputs with the OpenAI Responses API.

The repo starts with a Stripe-like support "minions" example. The tools are mocked billing fixtures, so local tests and CI never call Stripe and never need `OPENAI_API_KEY`.

## Why this shape

Paper Lantern recommended starting with a minimal Responses API harness, then adding Agents SDK orchestration only when handoffs and trace-heavy workflows become necessary. This keeps the first version cheap to run, easy to test, and aligned with OpenAI's current SDK guidance:

- OpenAI's quickstart shows SDK clients reading `OPENAI_API_KEY` from the environment and using `client.responses.create(...)`.
- OpenAI's function-calling guide shows a loop that preserves response output, executes function calls, and submits `function_call_output` items.
- OpenAI's structured-output guide recommends schema-constrained outputs when callers need reliable JSON.
- OpenAI's GPT-5.4 guidance recommends preserving response state with `previous_response_id` for multi-turn reasoning models.
- OpenAI's eval guidance favors small, versioned datasets with clear success criteria before scaling up.

Source links are listed in [docs/openai-notes.md](docs/openai-notes.md).

## Quickstart

Run the deterministic offline check:

```bash
PYTHONPATH=src python -m harness.cli run --offline
```

Run the unit tests:

```bash
PYTHONPATH=src python -m unittest discover -s tests
```

Install as a local package:

```bash
uv sync
uv run openai-harness run --offline
```

Run against the OpenAI API:

```bash
export OPENAI_API_KEY="sk-..."
uv run openai-harness run --cases examples/cases/stripe_minions.jsonl
```

The default model is `gpt-5.4`. Override it with `--model` or `OPENAI_MODEL`.

## Case format

Cases are JSONL records. Each case can define:

- `instructions`: system/developer-style guidance passed to the response.
- `input`: the user request.
- `tools`: registered mock tools the model may call.
- `response_schema`: a named schema from `harness.schemas` or an inline JSON schema.
- `expected`: local assertions for output text, JSON fields, and tool usage.
- `offline`: scripted tool-call rounds and final output for CI-safe regression checks.

See [examples/cases/stripe_minions.jsonl](examples/cases/stripe_minions.jsonl).

## Useful commands

```bash
PYTHONPATH=src python -m harness.cli list-tools
PYTHONPATH=src python -m harness.cli show-case stripe_refund_minion
PYTHONPATH=src python -m harness.cli run --offline --json
PYTHONPATH=src python -m harness.cli run --model gpt-5.4 --reasoning-effort low
```

## Repo layout

```text
src/harness/
  cases.py       Load and validate JSONL cases.
  cli.py         Command-line entrypoint.
  evaluator.py   Local pass/fail assertions.
  offline.py     Scripted Responses API adapter for CI.
  runner.py      Responses API tool loop.
  schemas.py     Structured-output schema registry.
  tools.py       Mock Stripe-like support tools.
examples/cases/
  stripe_minions.jsonl
tests/
  unittest coverage for loader, runner, and CLI-safe behavior.
```

