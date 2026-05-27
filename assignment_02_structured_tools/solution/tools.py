"""Reference solution: lookup_employee tool + dispatcher."""

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
    key = (name or "").strip()
    record = EMPLOYEE_DIRECTORY.get(key)
    if record is None:
        return {"error": "not_found", "queried_name": name}
    return dict(record)


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
    fn = TOOL_DISPATCH.get(name)
    if fn is None:
        return {"error": "unknown_tool", "tool": name}
    return fn(**args)


ALL_TOOLS = [LOOKUP_EMPLOYEE_TOOL]
