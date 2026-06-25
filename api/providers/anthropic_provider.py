from __future__ import annotations

import json

from api.config import Settings
from api.errors import ProviderError
from api.models import ChatRequest, ProviderResult, Usage


class AnthropicProvider:
    name = "anthropic"
    is_mock = False

    def __init__(self, settings: Settings):
        if not settings.anthropic_api_key:
            raise ProviderError("ANTHROPIC_API_KEY not set")
        from anthropic import AsyncAnthropic  # lazy import

        self._client = AsyncAnthropic(api_key=settings.anthropic_api_key)
        self._model = settings.anthropic_model

    def _split(self, request: ChatRequest):
        system = "\n".join(m.content for m in request.messages if m.role == "system")
        msgs = [{"role": m.role, "content": m.content} for m in request.messages if m.role != "system"]
        return system or None, msgs

    async def chat(self, request: ChatRequest) -> ProviderResult:
        system, msgs = self._split(request)
        resp = await self._client.messages.create(
            model=self._model,
            system=system or "",
            messages=msgs,
            max_tokens=request.max_tokens,
        )
        text = "".join(block.text for block in resp.content if block.type == "text")
        return ProviderResult(
            model=resp.model,
            content=text,
            usage=Usage(
                prompt_tokens=resp.usage.input_tokens,
                completion_tokens=resp.usage.output_tokens,
            ),
        )

    async def call_tool(self, request: ChatRequest, tools: list[dict]) -> dict:
        schema = tools[0]
        system, msgs = self._split(request)
        resp = await self._client.messages.create(
            model=self._model,
            system=system or "",
            messages=msgs,
            max_tokens=request.max_tokens,
            tools=[{
                "name": schema["name"],
                "description": f"Call {schema['name']}",
                "input_schema": schema["parameters"],
            }],
        )
        for block in resp.content:
            if block.type == "tool_use":
                return {"name": block.name, "arguments": json.dumps(block.input)}
        return {"name": schema["name"], "arguments": "{}"}
