"""Mock employee directory + the lookup_employee tool exposed to the model."""

from __future__ import annotations

from typing import Any

EMPLOYEE_DIRECTORY: dict[str, dict[str, str]] = {
    "Priya Raman":    {"email": "priya.raman@acme.com",    "team": "Platform", "manager": "Devon Park"},
    "Marcus Liu":     {"email": "marcus.liu@acme.com",     "team": "SRE",      "manager": "Devon Park"},
    "Sofia Andrade":  {"email": "sofia.andrade@acme.com",  "team": "Platform", "manager": "Priya Raman"},
    "Aisha Khan":     {"email": "aisha.khan@acme.com",     "team": "Platform", "manager": "Priya Raman"},
    "Hiroshi Tanaka": {"email": "hiroshi.tanaka@acme.com", "team": "SRE",      "manager": "Marcus Liu"},
    "Jamal Okonkwo":  {"email": "jamal.okonkwo@acme.com",  "team": "Data Infra", "manager": "Marcus Liu"},
}


def lookup_employee(name: str) -> dict[str, Any]:
    """Look up an Acme Corp employee by exact full name.

    TODO:
      - Trim whitespace from `name`.
      - If the trimmed name is in EMPLOYEE_DIRECTORY, return the dict.
      - Otherwise return {"error": "not_found", "queried_name": name}.
    """
    raise NotImplementedError("TODO: implement lookup_employee")


LOOKUP_EMPLOYEE_TOOL: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "lookup_employee",
        "description": (
            "Look up an Acme Corp employee's email, team, and manager by exact full "
            "name. Use this to fill in missing email/team fields for attendees mentioned "
            "in a transcript. Only call this when you don't already know the email."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "The employee's full name (first and last).",
                },
            },
            "required": ["name"],
            "additionalProperties": False,
        },
    },
}


TOOL_DISPATCH = {
    "lookup_employee": lookup_employee,
}


def dispatch_tool(name: str, args: dict[str, Any]) -> dict[str, Any]:
    """Dispatch a tool call by name to its Python implementation.

    TODO:
      - If `name` is in TOOL_DISPATCH, call it with **args and return the result.
      - Otherwise return {"error": "unknown_tool", "tool": name}.
        (Do NOT use eval/getattr — that's how you turn a tool call into RCE.)
    """
    raise NotImplementedError("TODO: implement dispatch_tool")


ALL_TOOLS = [LOOKUP_EMPLOYEE_TOOL]
