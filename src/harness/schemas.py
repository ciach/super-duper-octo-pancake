from __future__ import annotations

from copy import deepcopy
from typing import Any


SUPPORT_DECISION_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "status": {
            "type": "string",
            "enum": ["refunded", "ticket_created", "answered"],
        },
        "route": {
            "type": "string",
            "enum": ["billing_minion", "risk_minion", "support_minion"],
        },
        "customer_message": {"type": "string"},
        "evidence": {
            "type": "array",
            "items": {"type": "string"},
        },
    },
    "required": ["status", "route", "customer_message", "evidence"],
    "additionalProperties": False,
}

SCHEMAS: dict[str, dict[str, Any]] = {
    "support_decision": SUPPORT_DECISION_SCHEMA,
}


def resolve_schema(schema_ref: str | dict[str, Any] | None) -> tuple[str, dict[str, Any]] | None:
    if schema_ref is None:
        return None
    if isinstance(schema_ref, str):
        if schema_ref not in SCHEMAS:
            raise KeyError(f"unknown response schema {schema_ref!r}")
        return schema_ref, deepcopy(SCHEMAS[schema_ref])
    return "case_response", deepcopy(schema_ref)


def response_text_format(schema_ref: str | dict[str, Any] | None) -> dict[str, Any] | None:
    resolved = resolve_schema(schema_ref)
    if resolved is None:
        return None
    name, schema = resolved
    return {
        "format": {
            "type": "json_schema",
            "name": name,
            "strict": True,
            "schema": schema,
        }
    }

