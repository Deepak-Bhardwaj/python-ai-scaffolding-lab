import asyncio
import pytest
from api.models import ChatRequest, ProviderResult, Usage
from api.errors import TransientError
from api.client import resilient_chat
from api.providers.mock import MockProvider


def _req(fail_first_k=0):
    return ChatRequest.model_validate(
        {"messages": [{"role": "user", "content": "ping"}], "fail_first_k": fail_first_k}
    )


async def test_succeeds_first_try_attempts_is_one():
    resp = await resilient_chat(MockProvider(), _req())
    assert resp.attempts == 1
    assert resp.provider == "mock"
    assert resp.content == "echo: ping"


async def test_retries_then_succeeds_counts_attempts():
    # mock fails twice, succeeds on the 3rd attempt
    resp = await resilient_chat(MockProvider(fail_first_k=2), _req(), max_retries=3, base_delay=0.0)
    assert resp.attempts == 3


async def test_retry_exhausted_reraises_transient():
    with pytest.raises(TransientError):
        await resilient_chat(MockProvider(fail_first_k=5), _req(), max_retries=3, base_delay=0.0)


async def test_timeout_propagates():
    class SlowProvider:
        name = "slow"
        is_mock = True

        async def chat(self, request):
            await asyncio.sleep(1.0)
            return ProviderResult(model="x", content="y", usage=Usage())

        async def call_tool(self, request, tools):
            return {}

    with pytest.raises(asyncio.TimeoutError):
        await resilient_chat(SlowProvider(), _req(), timeout=0.01)
