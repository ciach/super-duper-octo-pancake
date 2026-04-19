from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Callable


ToolHandler = Callable[..., dict[str, Any]]


@dataclass(slots=True)
class ToolDefinition:
    name: str
    description: str
    parameters: dict[str, Any]
    handler: ToolHandler

    def as_openai_tool(self) -> dict[str, Any]:
        return {
            "type": "function",
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
            "strict": True,
        }


@dataclass
class StripeLikeStore:
    charges: dict[str, dict[str, Any]] = field(default_factory=dict)
    refunds: list[dict[str, Any]] = field(default_factory=list)
    tickets: list[dict[str, Any]] = field(default_factory=list)

    @classmethod
    def demo(cls) -> "StripeLikeStore":
        return cls(
            charges={
                "ch_001": {
                    "charge_id": "ch_001",
                    "customer_id": "cus_123",
                    "amount_usd": 49,
                    "status": "succeeded",
                    "refundable": True,
                    "duplicate_of": "ch_000",
                },
                "ch_002": {
                    "charge_id": "ch_002",
                    "customer_id": "cus_456",
                    "amount_usd": 19,
                    "status": "succeeded",
                    "refundable": False,
                    "duplicate_of": None,
                },
            }
        )


def build_tool_registry(store: StripeLikeStore | None = None) -> dict[str, ToolDefinition]:
    data = store or StripeLikeStore.demo()

    def lookup_charge(charge_id: str) -> dict[str, Any]:
        charge = data.charges.get(charge_id)
        if charge is None:
            return {"ok": False, "error": "charge_not_found", "charge_id": charge_id}
        return {"ok": True, "charge": charge}

    def issue_refund(charge_id: str, reason: str) -> dict[str, Any]:
        charge = data.charges.get(charge_id)
        if charge is None:
            return {"ok": False, "error": "charge_not_found", "charge_id": charge_id}
        if not charge["refundable"]:
            return {"ok": False, "error": "not_refundable", "charge_id": charge_id}
        refund = {
            "refund_id": f"re_{len(data.refunds) + 1:03d}",
            "charge_id": charge_id,
            "customer_id": charge["customer_id"],
            "amount_usd": charge["amount_usd"],
            "reason": reason,
            "status": "succeeded",
        }
        data.refunds.append(refund)
        return {"ok": True, "refund": refund}

    def create_support_ticket(customer_id: str, issue: str, priority: str) -> dict[str, Any]:
        ticket = {
            "ticket_id": f"tk_{len(data.tickets) + 1:03d}",
            "customer_id": customer_id,
            "issue": issue,
            "priority": priority,
            "status": "open",
        }
        data.tickets.append(ticket)
        return {"ok": True, "ticket": ticket}

    return {
        "lookup_charge": ToolDefinition(
            name="lookup_charge",
            description="Look up a mock billing charge by charge ID.",
            parameters={
                "type": "object",
                "properties": {
                    "charge_id": {
                        "type": "string",
                        "description": "Mock charge ID, for example ch_001.",
                    }
                },
                "required": ["charge_id"],
                "additionalProperties": False,
            },
            handler=lookup_charge,
        ),
        "issue_refund": ToolDefinition(
            name="issue_refund",
            description="Issue a refund for a refundable mock charge.",
            parameters={
                "type": "object",
                "properties": {
                    "charge_id": {"type": "string"},
                    "reason": {
                        "type": "string",
                        "enum": ["duplicate", "fraud", "service_issue", "other"],
                    },
                },
                "required": ["charge_id", "reason"],
                "additionalProperties": False,
            },
            handler=issue_refund,
        ),
        "create_support_ticket": ToolDefinition(
            name="create_support_ticket",
            description="Open a mock support ticket when billing cannot be resolved immediately.",
            parameters={
                "type": "object",
                "properties": {
                    "customer_id": {"type": "string"},
                    "issue": {"type": "string"},
                    "priority": {
                        "type": "string",
                        "enum": ["low", "normal", "high"],
                    },
                },
                "required": ["customer_id", "issue", "priority"],
                "additionalProperties": False,
            },
            handler=create_support_ticket,
        ),
    }


def select_tools(names: list[str], registry: dict[str, ToolDefinition] | None = None) -> dict[str, ToolDefinition]:
    available = registry or build_tool_registry()
    selected: dict[str, ToolDefinition] = {}
    for name in names:
        if name not in available:
            raise KeyError(f"unknown tool {name!r}; available tools: {', '.join(sorted(available))}")
        selected[name] = available[name]
    return selected


def call_tool(tool: ToolDefinition, raw_arguments: str) -> str:
    arguments = json.loads(raw_arguments or "{}")
    result = tool.handler(**arguments)
    return json.dumps(result, sort_keys=True)

