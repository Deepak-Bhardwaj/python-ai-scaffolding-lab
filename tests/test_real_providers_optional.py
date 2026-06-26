import os
import pytest
from api.config import Settings
from api.models import ChatRequest, ToolCallRequest


def _req():
    return ChatRequest.model_validate({"messages": [{"role": "user", "content": "Say hi in 3 words."}]})


class _FakeFn:
    name = "get_weather"
    arguments = '{"city": "Paris", "units": "celsius"}'


class _FakeCall:
    function = _FakeFn()


class _FakeMsg:
    tool_calls = [_FakeCall()]


class _FakeChoice:
    message = _FakeMsg()


class _FakeToolResponse:
    """Mimics an OpenAI chat-completion response carrying one tool call."""
    choices = [_FakeChoice()]


def test_openai_call_tool_uses_prompt_not_messages():
    """Regression: /tools/call passes a ToolCallRequest (has .prompt, no .messages).

    Previously call_tool read request.messages → AttributeError → 500 → empty body
    → the UI's resp.json() raised JSONDecodeError on the Function-calling tab.
    """
    from api.providers.openai_provider import OpenAIProvider

    p = OpenAIProvider.__new__(OpenAIProvider)  # skip __init__ (no key/SDK needed)
    p._model = "gpt-4o-mini"
    captured = {}

    class _Completions:
        async def create(self, **kwargs):
            captured.update(kwargs)
            return _FakeToolResponse()

    class _Chat:
        completions = _Completions()

    class _Client:
        chat = _Chat()

    p._client = _Client()

    req = ToolCallRequest.model_validate({"tool_name": "get_weather", "prompt": "Weather in Paris?"})
    schema = {"name": "get_weather", "parameters": {"type": "object", "properties": {}}}

    import asyncio
    out = asyncio.run(p.call_tool(req, [schema]))

    assert out["name"] == "get_weather"
    assert out["arguments"] == '{"city": "Paris", "units": "celsius"}'
    # The prompt must be forwarded as a user message.
    assert captured["messages"] == [{"role": "user", "content": "Weather in Paris?"}]


def test_modules_import_without_sdk_at_top_level():
    # Importing the package must NOT require the SDKs (offline-safe).
    import importlib
    for mod in (
        "api.providers.openai_provider",
        "api.providers.anthropic_provider",
        "api.providers.azure_provider",
    ):
        importlib.import_module(mod)  # import is fine; instantiation needs keys + SDK


@pytest.mark.skipif(not os.getenv("OPENAI_API_KEY"), reason="no OPENAI_API_KEY")
async def test_openai_live():
    from api.providers.openai_provider import OpenAIProvider
    p = OpenAIProvider(Settings())
    result = await p.chat(_req())
    assert result.content


@pytest.mark.skipif(not os.getenv("ANTHROPIC_API_KEY"), reason="no ANTHROPIC_API_KEY")
async def test_anthropic_live():
    from api.providers.anthropic_provider import AnthropicProvider
    p = AnthropicProvider(Settings())
    result = await p.chat(_req())
    assert result.content
