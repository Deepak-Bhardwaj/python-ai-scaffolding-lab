from __future__ import annotations

from typing import Protocol

from api.models import ChatRequest, ProviderResult


class LLMProvider(Protocol):
    """The contract every provider satisfies. Structural typing — no inheritance needed."""
    name: str
    is_mock: bool

    async def chat(self, request: ChatRequest) -> ProviderResult: ...

    async def call_tool(self, request: ChatRequest, tools: list[dict]) -> dict: ...
