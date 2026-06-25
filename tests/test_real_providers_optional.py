import os
import pytest
from api.config import Settings
from api.models import ChatRequest


def _req():
    return ChatRequest.model_validate({"messages": [{"role": "user", "content": "Say hi in 3 words."}]})


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
