from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_providers_lists_mock_available():
    r = client.get("/providers")
    assert r.status_code == 200
    body = r.json()
    names = {p["name"]: p for p in body["providers"]}
    assert names["mock"]["available"] is True
    assert body["default"] == "mock"


def test_chat_happy_path():
    r = client.post("/chat", json={"messages": [{"role": "user", "content": "hi"}]})
    assert r.status_code == 200
    body = r.json()
    assert body["content"] == "echo: hi"
    assert body["attempts"] == 1
    assert body["provider"] == "mock"


def test_chat_retries_then_succeeds():
    r = client.post("/chat", json={"messages": [{"role": "user", "content": "hi"}], "fail_first_k": 2})
    assert r.status_code == 200
    assert r.json()["attempts"] == 3


def test_chat_retry_exhausted_returns_502_envelope():
    r = client.post("/chat", json={"messages": [{"role": "user", "content": "hi"}], "fail_first_k": 9})
    assert r.status_code == 502
    env = r.json()["detail"]
    assert env["error_type"] == "TransientError"
    assert env["retryable"] is True


def test_chat_rejects_extra_field_422():
    r = client.post("/chat", json={"messages": [{"role": "user", "content": "hi"}], "temperature": 0.5})
    assert r.status_code == 422


def test_tools_call_good():
    r = client.post("/tools/call", json={"tool_name": "get_weather", "prompt": "weather in London?"})
    assert r.status_code == 200
    body = r.json()
    assert body["validated"] is True
    assert body["parsed_args"] == {"city": "London", "units": "celsius"}


def test_tools_call_bad_args():
    r = client.post(
        "/tools/call",
        json={"tool_name": "get_weather", "prompt": "weather?", "force_bad_args": True},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["validated"] is False
    assert body["error"]


def test_chat_stream_returns_event_stream():
    r = client.post("/chat/stream", json={"messages": [{"role": "user", "content": "hi there"}]})
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/event-stream")
    assert "echo" in r.text


def test_chat_stream_unconfigured_provider_returns_400_envelope():
    r = client.post(
        "/chat/stream",
        json={"messages": [{"role": "user", "content": "hi"}], "provider": "openai"},
    )
    assert r.status_code == 400
    assert r.json()["detail"]["error_type"] == "ProviderError"


def test_tools_call_unconfigured_provider_returns_400_envelope():
    r = client.post(
        "/tools/call",
        json={"tool_name": "get_weather", "prompt": "x", "provider": "openai"},
    )
    assert r.status_code == 400
    assert r.json()["detail"]["error_type"] == "ProviderError"
