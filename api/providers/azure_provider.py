from __future__ import annotations

from api.config import Settings
from api.errors import ProviderError
from api.models import ChatRequest, ProviderResult, Usage


class AzureProvider:
    name = "azure"
    is_mock = False

    def __init__(self, settings: Settings):
        if not (settings.azure_openai_api_key and settings.azure_openai_endpoint):
            raise ProviderError("AZURE_OPENAI_API_KEY / AZURE_OPENAI_ENDPOINT not set")
        from openai import AsyncAzureOpenAI  # lazy import

        self._client = AsyncAzureOpenAI(
            api_key=settings.azure_openai_api_key,
            azure_endpoint=settings.azure_openai_endpoint,
            api_version="2024-06-01",
        )
        self._deployment = settings.azure_openai_deployment

    async def chat(self, request: ChatRequest) -> ProviderResult:
        resp = await self._client.chat.completions.create(
            model=self._deployment,
            messages=[{"role": m.role, "content": m.content} for m in request.messages],
            max_tokens=request.max_tokens,
        )
        usage = resp.usage
        return ProviderResult(
            model=resp.model,
            content=resp.choices[0].message.content or "",
            usage=Usage(
                prompt_tokens=getattr(usage, "prompt_tokens", 0),
                completion_tokens=getattr(usage, "completion_tokens", 0),
            ),
        )

    async def call_tool(self, request: ChatRequest, tools: list[dict]) -> dict:
        schema = tools[0]
        resp = await self._client.chat.completions.create(
            model=self._deployment,
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
