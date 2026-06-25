from __future__ import annotations

import json
from typing import Literal

from pydantic import BaseModel, ConfigDict, ValidationError


class GetWeatherArgs(BaseModel):
    """The typed contract for the get_weather tool's arguments."""
    model_config = ConfigDict(strict=True, extra="forbid")
    city: str
    units: Literal["celsius", "fahrenheit"] = "celsius"


# Registry: tool name -> strict args model. Add new tools here.
TOOLS: dict[str, type[BaseModel]] = {
    "get_weather": GetWeatherArgs,
}


def tool_names() -> list[str]:
    return list(TOOLS)


def tool_schema(name: str) -> dict:
    """JSON schema the model would be handed to produce a valid tool call."""
    model = TOOLS[name]
    return {"name": name, "parameters": model.model_json_schema()}


def validate_tool_call(name: str, raw_args: str) -> tuple[bool, dict | None, str | None]:
    """Validate a raw (string) tool-call payload against its Pydantic contract.

    Returns (validated, parsed_args, error). Never raises — every failure mode
    (unknown tool, non-JSON, schema violation) returns a human-readable error string.
    """
    model = TOOLS.get(name)
    if model is None:
        return False, None, f"unknown tool: {name}"

    try:
        data = json.loads(raw_args)
    except json.JSONDecodeError as exc:
        return False, None, f"arguments are not valid JSON: {exc}"

    try:
        parsed = model.model_validate(data)
    except ValidationError as exc:
        return False, None, f"arguments failed validation: {exc.errors(include_url=False)}"

    return True, parsed.model_dump(), None
