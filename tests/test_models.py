import pytest
from pydantic import ValidationError
from api.models import ChatMessage, ChatRequest, Usage, ChatResponse


def test_valid_chat_request_parses():
    req = ChatRequest.model_validate(
        {"messages": [{"role": "user", "content": "hi"}]}
    )
    assert req.max_tokens == 256
    assert req.fail_first_k == 0
    assert req.messages[0].role == "user"


def test_extra_field_is_rejected():
    with pytest.raises(ValidationError):
        ChatRequest.model_validate(
            {"messages": [{"role": "user", "content": "hi"}], "temperature": 0.7}
        )


def test_strict_mode_rejects_type_coercion():
    # strict mode: a string is NOT silently coerced to int
    with pytest.raises(ValidationError):
        ChatRequest.model_validate(
            {"messages": [{"role": "user", "content": "hi"}], "max_tokens": "256"}
        )


def test_invalid_role_rejected():
    with pytest.raises(ValidationError):
        ChatMessage.model_validate({"role": "robot", "content": "hi"})


def test_empty_messages_rejected():
    with pytest.raises(ValidationError):
        ChatRequest.model_validate({"messages": []})


def test_chat_response_roundtrips():
    resp = ChatResponse(
        provider="mock", model="mock-1", content="echo: hi",
        usage=Usage(prompt_tokens=1, completion_tokens=2), attempts=1,
    )
    assert resp.model_dump()["attempts"] == 1
