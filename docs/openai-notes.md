# OpenAI implementation notes

These notes record the docs used while shaping the harness.

## Current SDK practice

The OpenAI quickstart shows the official SDK reading `OPENAI_API_KEY` from the environment and using `client.responses.create(...)` for text generation, tools, streaming, and agent examples.

Source: https://developers.openai.com/api/docs/quickstart

## Function calling

The function-calling guide describes the application loop this repo implements:

1. Send a request with tool definitions.
2. Read `function_call` items from `response.output`.
3. Execute the matching local function.
4. Send `function_call_output` items back to the model.
5. Continue until the response has final text.

Source: https://developers.openai.com/api/docs/guides/function-calling

## Structured output

Structured Outputs constrain final text to a JSON schema and are preferred over loose JSON prompting when a caller needs predictable machine-readable output.

Source: https://developers.openai.com/api/docs/guides/structured-outputs

## GPT-5.4 state

GPT-5.4 is documented as a reasoning model. For multi-turn interactions, OpenAI recommends preserving previous reasoning state; this harness uses `previous_response_id` when available.

Source: https://developers.openai.com/api/docs/guides/latest-model

## Evaluation practice

This harness follows the eval guidance at a repo-local scale: version the dataset, define expected behavior in each row, and keep CI deterministic by using offline fixtures unless a live API run is explicitly requested.

Sources:

- https://developers.openai.com/api/docs/guides/evaluation-getting-started
- https://developers.openai.com/api/docs/guides/evaluation-best-practices

