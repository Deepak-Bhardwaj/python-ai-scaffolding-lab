from __future__ import annotations

from api.config import Settings
from api.errors import ProviderError
from api.providers.base import LLMProvider
from api.providers.mock import MockProvider


def _live_availability(settings: Settings) -> dict[str, bool]:
    return {
        "openai": bool(settings.openai_api_key),
        "anthropic": bool(settings.anthropic_api_key),
        "azure": bool(settings.azure_openai_api_key and settings.azure_openai_endpoint),
    }


def available_providers(settings: Settings) -> list[dict]:
    avail = _live_availability(settings)
    rows = [{"name": "mock", "available": True, "is_mock": True}]
    for name in ("openai", "anthropic", "azure"):
        rows.append({"name": name, "available": avail[name], "is_mock": False})
    return rows


def make_provider(
    name: str | None,
    settings: Settings,
    *,
    fail_first_k: int = 0,
    bad_args: bool = False,
) -> LLMProvider:
    if name in (None, "mock"):
        return MockProvider(fail_first_k=fail_first_k, bad_args=bad_args)

    avail = _live_availability(settings)
    if name not in avail:
        raise ProviderError(f"unknown provider: {name}")
    if not avail[name]:
        raise ProviderError(f"provider '{name}' is not configured (missing key)")

    # Lazy imports — live SDK modules are only imported on demand to keep startup fast and SDK-free.
    if name == "openai":
        from api.providers.openai_provider import OpenAIProvider
        return OpenAIProvider(settings)
    if name == "anthropic":
        from api.providers.anthropic_provider import AnthropicProvider
        return AnthropicProvider(settings)
    if name == "azure":
        from api.providers.azure_provider import AzureProvider
        return AzureProvider(settings)
    raise ProviderError(f"unknown provider: {name}")  # unreachable
