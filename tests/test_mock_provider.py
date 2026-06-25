import pytest
from api.models import ChatRequest
from api.errors import TransientError
from api.providers.mock import MockProvider


def _req():
    return ChatRequest.model_validate({"messages": [{"role": "user", "content": "ping"}]})


async def test_mock_chat_echoes_last_message():
    p = MockProvider()
    result = await p.chat(_req())
    assert result.content == "echo: ping"
    assert result.model == "mock-1"
    assert p.is_mock is True
    assert p.name == "mock"


async def test_mock_chat_fails_first_k_times():
    p = MockProvider(fail_first_k=2)
    with pytest.raises(TransientError):
        await p.chat(_req())
    with pytest.raises(TransientError):
        await p.chat(_req())
    # third call succeeds
    result = await p.chat(_req())
    assert result.content == "echo: ping"


async def test_mock_tool_call_good_args_is_json():
    p = MockProvider()
    out = await p.call_tool(_req(), [{"name": "get_weather"}])
    assert out["name"] == "get_weather"
    assert out["arguments"] == '{"city": "London", "units": "celsius"}'


async def test_mock_tool_call_bad_args_is_broken_json():
    p = MockProvider(bad_args=True)
    out = await p.call_tool(_req(), [{"name": "get_weather"}])
    assert out["arguments"] == "{not-json"
