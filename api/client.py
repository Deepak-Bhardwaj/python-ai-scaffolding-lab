from __future__ import annotations

import asyncio

from api.errors import TransientError
from api.models import ChatRequest, ChatResponse
from api.providers.base import LLMProvider


async def resilient_chat(
    provider: LLMProvider,
    request: ChatRequest,
    *,
    max_retries: int = 3,
    base_delay: float = 0.01,
    timeout: float = 10.0,
) -> ChatResponse:
    """Call a provider with a timeout and bounded exponential backoff on TransientError.

    Returns a ChatResponse stamped with the real attempt count. Re-raises TransientError
    once retries are exhausted; asyncio.TimeoutError propagates to the caller.
    """
    attempt = 0
    while True:
        attempt += 1
        try:
            result = await asyncio.wait_for(provider.chat(request), timeout=timeout)
        except TransientError:
            if attempt > max_retries:
                raise
            await asyncio.sleep(base_delay * (2 ** (attempt - 1)))
            continue
        return ChatResponse(
            provider=provider.name,
            model=result.model,
            content=result.content,
            usage=result.usage,
            attempts=attempt,
        )
