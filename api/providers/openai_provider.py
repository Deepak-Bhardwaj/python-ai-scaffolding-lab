from __future__ import annotations

from api.config import Settings
from api.errors import ProviderError
from api.models import ChatRequest, ProviderResult, Usage


class OpenAIProvider:
    name = "openai"
    is_mock = False

    def __init__(self, settings: Settings):
        if not settings.openai_api_key:
            raise ProviderError("OPENAI_API_KEY not set")
        from openai import AsyncOpenAI  # lazy import

        self._client = AsyncOpenAI(api_key=settings.openai_api_key)
        self._model = settings.openai_model

    async def chat(self, request: ChatRequest) -> ProviderResult:
        resp = await self._client.chat.completions.create(
            model=self._model,
            messages=[{"role": m.role, "content": m.content} for m in request.messages],
            max_tokens=request.max_tokens,
        )
        choice = resp.choices[0].message.content or ""
        usage = resp.usage
        return ProviderResult(
            model=resp.model,
            content=choice,
            usage=Usage(
                prompt_tokens=getattr(usage, "prompt_tokens", 0),
                completion_tokens=getattr(usage, "completion_tokens", 0),
            ),
        )

    async def call_tool(self, request: ChatRequest, tools: list[dict]) -> dict:
        schema = tools[0]
        resp = await self._client.chat.completions.create(
            model=self._model,
            messages=[{"role": m.role, "content": m.content} for m in request.messages],
            tools=[{
                "type": "function",
                "function": {"name": schema["name"], "parameters": schema["parameters"]},
            }],
            tool_choice="auto",
        )
        calls = resp.choices[0].message.tool_calls
        if not calls:
            return {"name": schema["name"], "arguments": "{}"}
        return {"name": calls[0].function.name, "arguments": calls[0].function.arguments}
