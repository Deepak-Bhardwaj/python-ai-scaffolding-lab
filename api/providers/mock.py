from __future__ import annotations

from api.errors import TransientError
from api.models import ChatRequest, ProviderResult, Usage


class MockProvider:
    """Deterministic, offline provider — the teaching engine.

    fail_first_k: raise TransientError on the first k calls (retry/backoff demo).
    bad_args:     emit malformed tool arguments (function-calling error-handling demo).
    """
    name = "mock"
    is_mock = True

    def __init__(self, fail_first_k: int = 0, bad_args: bool = False):
        self._fails_left = fail_first_k
        self.bad_args = bad_args

    async def chat(self, request: ChatRequest) -> ProviderResult:
        if self._fails_left > 0:
            self._fails_left -= 1
            raise TransientError("429 rate limited (mock)")
        last = request.messages[-1].content
        return ProviderResult(
            model="mock-1",
            content=f"echo: {last}",
            usage=Usage(prompt_tokens=len(last.split()), completion_tokens=2),
        )

    async def call_tool(self, request: ChatRequest, tools: list[dict]) -> dict:
        name = tools[0]["name"]
        if self.bad_args:
            return {"name": name, "arguments": "{not-json"}
        return {"name": name, "arguments": '{"city": "London", "units": "celsius"}'}
