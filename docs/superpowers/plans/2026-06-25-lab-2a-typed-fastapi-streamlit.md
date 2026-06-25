# Lab 2-A — Typed FastAPI + Streamlit Teaching App — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a finished, self-explanatory teaching lab where a Streamlit UI drives a typed FastAPI wrapper around the LLM SDKs, demonstrating async patterns, strict Pydantic v2, typed clients with retries, and function-calling contracts — fully offline by default.

**Architecture:** A FastAPI app (`api/`) exposes typed endpoints backed by pluggable providers (mock by default; OpenAI/Anthropic/Azure when keys are present). A resilient async client adds timeout + bounded exponential backoff. A Streamlit app (`ui/`) is an HTTP client to the API with five concept tabs, each pairing a live demo with an inline hint panel. The mock provider is the teaching engine: deterministic failure injection (retry demo) and deterministic tool-call emission (function-calling demo).

**Tech Stack:** Python 3.12 · `uv` · FastAPI · Pydantic v2 (+ pydantic-settings) · httpx · uvicorn · Streamlit · pytest + pytest-asyncio. Optional: `openai`, `anthropic` SDKs (lazy, key-gated).

## Global Constraints

- Python `>=3.12`; package managed with `uv` (fall back to `python3.12 -m venv` + `pip -e .`).
- All request/response models are **strict** Pydantic v2: `ConfigDict(strict=True, extra="forbid")`.
- **Offline-first:** default provider is `mock`; the full app + all non-optional tests must pass with **zero API keys**.
- Live SDKs (`openai`, `anthropic`) are **lazily imported** inside provider methods and **key-gated** — importing `api/` must never require them.
- Anthropic model id default: `claude-opus-4-8`. OpenAI/Azure default model: `gpt-4o-mini`.
- Self-contained folder convention (matches D02 kit): own `.venv`, `setup.sh`, `run.sh`, `.vscode/`, `.env.example`, `.gitignore`.
- Streamlit reads `API_BASE_URL` (default `http://localhost:8000`); it never imports the SDKs or `api` package internals — it only calls HTTP.
- Package import root is `api` and `ui`; `[tool.setuptools] packages = ["api", "api.providers"]`.
- All work happens under `Batch-1/prep/python-ai-scaffolding/`. Paths below are relative to that folder.
- Commit after each task. The repo's convention is direct commits to `main`.

---

### Task 1: Project scaffolding & packaging

**Files:**
- Create: `pyproject.toml`, `.python-version`, `.gitignore`, `.env.example`, `setup.sh`, `.vscode/settings.json`, `.vscode/launch.json`
- Create: `api/__init__.py`, `api/providers/__init__.py` (empty placeholder, replaced in Task 5), `ui/__init__.py`, `tests/__init__.py`

**Interfaces:**
- Consumes: nothing.
- Produces: an installable package `lab2a` exposing import roots `api` and `ui`; `setup.sh` that creates `.venv` and runs `pytest`.

- [ ] **Step 1: Create `pyproject.toml`**

```toml
[project]
name = "lab2a"
version = "0.1.0"
description = "Lab 2-A — typed FastAPI + Streamlit teaching app"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.111",
    "uvicorn>=0.30",
    "pydantic>=2.7",
    "pydantic-settings>=2.2",
    "httpx>=0.27",
    "streamlit>=1.36",
]

[project.optional-dependencies]
dev = ["pytest>=8.2", "pytest-asyncio>=0.23"]
openai = ["openai>=1.30"]
anthropic = ["anthropic>=0.40"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]

[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[tool.setuptools]
packages = ["api", "api.providers", "ui"]
```

- [ ] **Step 2: Create supporting dotfiles**

`.python-version`:
```
3.12
```

`.gitignore`:
```
.venv/
__pycache__/
*.pyc
.pytest_cache/
.env
.DS_Store
```

`.env.example`:
```
# Lab 2-A runs fully offline with the mock provider — no keys needed.
# Set any of these to light up a real provider in the UI.
# OPENAI_API_KEY=sk-...
# OPENAI_MODEL=gpt-4o-mini
# ANTHROPIC_API_KEY=sk-ant-...
# ANTHROPIC_MODEL=claude-opus-4-8
# AZURE_OPENAI_API_KEY=...
# AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com
# AZURE_OPENAI_DEPLOYMENT=gpt-4o-mini
# DEFAULT_PROVIDER=mock
# API_BASE_URL=http://localhost:8000
```

- [ ] **Step 3: Create package `__init__.py` files**

Create empty files: `api/__init__.py`, `api/providers/__init__.py`, `ui/__init__.py`, `tests/__init__.py`.

- [ ] **Step 4: Create `setup.sh`**

```bash
#!/usr/bin/env bash
# Lab 2-A — one-shot setup. Prefers uv; falls back to python3.12 venv.
set -euo pipefail
cd "$(dirname "$0")"

if command -v uv >/dev/null 2>&1; then
  uv venv --python 3.12 .venv
  uv pip install --python .venv/bin/python -e ".[dev]"
else
  python3.12 -m venv .venv
  ./.venv/bin/python -m pip install --upgrade pip
  ./.venv/bin/python -m pip install -e ".[dev]"
fi

echo "Running tests..."
./.venv/bin/python -m pytest -q
echo "Setup complete. Run ./run.sh to launch the API + Streamlit UI."
```

- [ ] **Step 5: Create `.vscode/settings.json` and `.vscode/launch.json`**

`.vscode/settings.json`:
```json
{
  "python.defaultInterpreterPath": "./.venv/bin/python",
  "python.testing.pytestEnabled": true,
  "python.testing.pytestArgs": ["tests"],
  "python.analysis.typeCheckingMode": "basic"
}
```

`.vscode/launch.json`:
```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Run API (uvicorn)",
      "type": "debugpy",
      "request": "launch",
      "module": "uvicorn",
      "args": ["api.main:app", "--reload", "--port", "8000"],
      "console": "integratedTerminal"
    }
  ]
}
```

- [ ] **Step 6: Make scripts executable and verify install**

Run:
```bash
chmod +x setup.sh
./setup.sh
```
Expected: install succeeds; pytest runs and reports `no tests ran` (or collects 0) without import errors. (Tests arrive in later tasks.)

- [ ] **Step 7: Commit**

```bash
git add pyproject.toml .python-version .gitignore .env.example setup.sh .vscode api ui tests
git commit -m "chore: scaffold Lab 2-A package + uv setup"
```

---

### Task 2: Strict Pydantic v2 models

**Files:**
- Create: `api/models.py`
- Test: `tests/test_models.py`

**Interfaces:**
- Produces:
  - `ChatMessage(role: Literal["system","user","assistant"], content: str)`
  - `ChatRequest(messages: list[ChatMessage], provider: str | None = None, max_tokens: int = 256, fail_first_k: int = 0)`
  - `Usage(prompt_tokens: int = 0, completion_tokens: int = 0)`
  - `ChatResponse(provider: str, model: str, content: str, usage: Usage, attempts: int)`
  - `ProviderResult(model: str, content: str, usage: Usage)` — what providers return; client wraps it into `ChatResponse`.
  - `ToolCallRequest(tool_name: str, prompt: str, provider: str | None = None, force_bad_args: bool = False)`
  - `ToolCallResult(tool_name: str, raw_args: str, validated: bool, parsed_args: dict | None = None, error: str | None = None)`
  - `STRICT` = `ConfigDict(strict=True, extra="forbid")`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_models.py
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `./.venv/bin/python -m pytest tests/test_models.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'api.models'`.

- [ ] **Step 3: Write the implementation**

```python
# api/models.py
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

STRICT = ConfigDict(strict=True, extra="forbid")


class ChatMessage(BaseModel):
    model_config = STRICT
    role: Literal["system", "user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    model_config = STRICT
    messages: list[ChatMessage] = Field(min_length=1)
    provider: str | None = None
    max_tokens: int = Field(default=256, ge=1, le=4096)
    # Teaching lever — honoured only by the mock provider (retry demo).
    fail_first_k: int = Field(default=0, ge=0, le=10)


class Usage(BaseModel):
    model_config = STRICT
    prompt_tokens: int = 0
    completion_tokens: int = 0


class ProviderResult(BaseModel):
    model_config = STRICT
    model: str
    content: str
    usage: Usage


class ChatResponse(BaseModel):
    model_config = STRICT
    provider: str
    model: str
    content: str
    usage: Usage
    attempts: int


class ToolCallRequest(BaseModel):
    model_config = STRICT
    tool_name: str
    prompt: str
    provider: str | None = None
    # Teaching lever — forces the mock to emit malformed args (error-handling demo).
    force_bad_args: bool = False


class ToolCallResult(BaseModel):
    model_config = STRICT
    tool_name: str
    raw_args: str
    validated: bool
    parsed_args: dict | None = None
    error: str | None = None
```

- [ ] **Step 4: Run test to verify it passes**

Run: `./.venv/bin/python -m pytest tests/test_models.py -v`
Expected: PASS (6 passed).

- [ ] **Step 5: Commit**

```bash
git add api/models.py tests/test_models.py
git commit -m "feat: strict Pydantic v2 request/response models"
```

---

### Task 3: Typed error envelope & exception types

**Files:**
- Create: `api/errors.py`
- Test: `tests/test_errors.py`

**Interfaces:**
- Produces:
  - `ErrorEnvelope(error_type: str, message: str, retryable: bool, attempts: int | None = None)`
  - `class TransientError(Exception)` — retryable (e.g. 429/503).
  - `class ProviderError(Exception)` — non-retryable.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_errors.py
from api.errors import ErrorEnvelope, TransientError, ProviderError


def test_transient_is_exception():
    assert issubclass(TransientError, Exception)
    assert issubclass(ProviderError, Exception)


def test_error_envelope_shape():
    env = ErrorEnvelope(error_type="TransientError", message="429", retryable=True, attempts=4)
    dumped = env.model_dump()
    assert dumped == {
        "error_type": "TransientError",
        "message": "429",
        "retryable": True,
        "attempts": 4,
    }


def test_error_envelope_attempts_optional():
    env = ErrorEnvelope(error_type="ProviderError", message="boom", retryable=False)
    assert env.attempts is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `./.venv/bin/python -m pytest tests/test_errors.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'api.errors'`.

- [ ] **Step 3: Write the implementation**

```python
# api/errors.py
from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class ErrorEnvelope(BaseModel):
    """The single typed shape every failure is surfaced as."""
    model_config = ConfigDict(extra="forbid")
    error_type: str
    message: str
    retryable: bool
    attempts: int | None = None


class TransientError(Exception):
    """Retryable provider error (rate limit / 5xx). The client will back off and retry."""


class ProviderError(Exception):
    """Non-retryable provider error (bad request / auth). The client gives up immediately."""
```

- [ ] **Step 4: Run test to verify it passes**

Run: `./.venv/bin/python -m pytest tests/test_errors.py -v`
Expected: PASS (3 passed).

- [ ] **Step 5: Commit**

```bash
git add api/errors.py tests/test_errors.py
git commit -m "feat: typed error envelope + exception taxonomy"
```

---

### Task 4: Provider Protocol & deterministic mock provider

**Files:**
- Create: `api/providers/base.py`, `api/providers/mock.py`
- Test: `tests/test_mock_provider.py`

**Interfaces:**
- Consumes: `ChatRequest`, `ProviderResult`, `Usage` (Task 2); `TransientError` (Task 3).
- Produces:
  - `class LLMProvider(Protocol)` with `name: str`, `is_mock: bool`, `async def chat(self, request: ChatRequest) -> ProviderResult`, `async def call_tool(self, request: ChatRequest, tools: list[dict]) -> dict`.
  - `class MockProvider` with `__init__(self, fail_first_k: int = 0, bad_args: bool = False)`, `name = "mock"`, `is_mock = True`. `chat` echoes the last user message and raises `TransientError` the first `fail_first_k` calls. `call_tool` returns `{"name": <tool>, "arguments": <json-or-broken-string>}`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_mock_provider.py
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `./.venv/bin/python -m pytest tests/test_mock_provider.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'api.providers.mock'`.

- [ ] **Step 3: Write the implementations**

```python
# api/providers/base.py
from __future__ import annotations

from typing import Protocol

from api.models import ChatRequest, ProviderResult


class LLMProvider(Protocol):
    """The contract every provider satisfies. Structural typing — no inheritance needed."""
    name: str
    is_mock: bool

    async def chat(self, request: ChatRequest) -> ProviderResult: ...

    async def call_tool(self, request: ChatRequest, tools: list[dict]) -> dict: ...
```

```python
# api/providers/mock.py
from __future__ import annotations

from api.errors import TransientError
from api.models import ChatRequest, ProviderResult, Usage


class MockProvider:
    """Deterministic, offline provider — the teaching engine.

    fail_first_k: raise TransientError on the first k calls (retry/backoff demo).
    bad_args:     emit malformed tool arguments (function-calling error-handling demo).
    """
    name = "mock"
    is_mock = True

    def __init__(self, fail_first_k: int = 0, bad_args: bool = False):
        self._fails_left = fail_first_k
        self.bad_args = bad_args

    async def chat(self, request: ChatRequest) -> ProviderResult:
        if self._fails_left > 0:
            self._fails_left -= 1
            raise TransientError("429 rate limited (mock)")
        last = request.messages[-1].content
        return ProviderResult(
            model="mock-1",
            content=f"echo: {last}",
            usage=Usage(prompt_tokens=len(last.split()), completion_tokens=2),
        )

    async def call_tool(self, request: ChatRequest, tools: list[dict]) -> dict:
        name = tools[0]["name"]
        if self.bad_args:
            return {"name": name, "arguments": "{not-json"}
        return {"name": name, "arguments": '{"city": "London", "units": "celsius"}'}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `./.venv/bin/python -m pytest tests/test_mock_provider.py -v`
Expected: PASS (4 passed).

- [ ] **Step 5: Commit**

```bash
git add api/providers/base.py api/providers/mock.py tests/test_mock_provider.py
git commit -m "feat: provider Protocol + deterministic mock provider"
```

---

### Task 5: Settings & provider registry

**Files:**
- Create: `api/config.py`
- Modify: `api/providers/__init__.py` (replace the empty placeholder)
- Test: `tests/test_registry.py`

**Interfaces:**
- Consumes: `MockProvider` (Task 4).
- Produces:
  - `class Settings(BaseSettings)` with fields: `openai_api_key`, `anthropic_api_key`, `azure_openai_api_key`, `azure_openai_endpoint` (all `str | None`); `openai_model="gpt-4o-mini"`, `anthropic_model="claude-opus-4-8"`, `azure_openai_deployment="gpt-4o-mini"`, `default_provider="mock"`. Module-level singleton `settings`.
  - `available_providers(settings) -> list[dict]` → `[{"name", "available": bool, "is_mock": bool}, ...]` (mock always available).
  - `make_provider(name, settings, *, fail_first_k=0, bad_args=False) -> LLMProvider` — returns `MockProvider` for `"mock"`/`None`; for live names raises `ProviderError` if the key is missing, else lazily constructs the live provider (added in Task 9).

- [ ] **Step 1: Write the failing test**

```python
# tests/test_registry.py
import pytest
from api.config import Settings
from api.providers import available_providers, make_provider
from api.providers.mock import MockProvider
from api.errors import ProviderError


def _offline_settings():
    return Settings(_env_file=None)  # ignore any real .env during tests


def test_mock_always_available():
    names = {p["name"]: p for p in available_providers(_offline_settings())}
    assert names["mock"]["available"] is True
    assert names["mock"]["is_mock"] is True
    assert names["openai"]["available"] is False  # no key in test env


def test_make_mock_provider():
    p = make_provider("mock", _offline_settings(), fail_first_k=2)
    assert isinstance(p, MockProvider)
    assert p._fails_left == 2


def test_make_none_defaults_to_mock():
    p = make_provider(None, _offline_settings())
    assert isinstance(p, MockProvider)


def test_make_live_provider_without_key_raises():
    with pytest.raises(ProviderError):
        make_provider("openai", _offline_settings())
```

- [ ] **Step 2: Run test to verify it fails**

Run: `./.venv/bin/python -m pytest tests/test_registry.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'api.config'`.

- [ ] **Step 3: Write `api/config.py`**

```python
# api/config.py
from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    openai_api_key: str | None = None
    anthropic_api_key: str | None = None
    azure_openai_api_key: str | None = None
    azure_openai_endpoint: str | None = None

    openai_model: str = "gpt-4o-mini"
    anthropic_model: str = "claude-opus-4-8"
    azure_openai_deployment: str = "gpt-4o-mini"

    default_provider: str = "mock"


settings = Settings()
```

- [ ] **Step 4: Write `api/providers/__init__.py`**

```python
# api/providers/__init__.py
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

    # Lazy imports — live SDK modules are added in Task 9 and only imported on demand.
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
```

> Note: the live-provider imports reference modules created in Task 9. Until then, `make_provider("openai", ...)` with a key set would fail to import — but the offline tests never set keys, so all Task 5 tests pass. The lazy import is exactly the point.

- [ ] **Step 5: Run test to verify it passes**

Run: `./.venv/bin/python -m pytest tests/test_registry.py -v`
Expected: PASS (4 passed).

- [ ] **Step 6: Commit**

```bash
git add api/config.py api/providers/__init__.py tests/test_registry.py
git commit -m "feat: pydantic-settings config + key-gated provider registry"
```

---

### Task 6: Resilient async client (retries / backoff / timeout)

**Files:**
- Create: `api/client.py`
- Test: `tests/test_client.py`

**Interfaces:**
- Consumes: `ChatRequest`, `ChatResponse` (Task 2); `TransientError` (Task 3); `LLMProvider` (Task 4).
- Produces:
  - `async def resilient_chat(provider: LLMProvider, request: ChatRequest, *, max_retries: int = 3, base_delay: float = 0.01, timeout: float = 10.0) -> ChatResponse` — retries `TransientError` with bounded exponential backoff (`base_delay * 2**(attempt-1)`), wraps the `ProviderResult` into a `ChatResponse` with the real `attempts` count, and re-raises `TransientError` once retries are exhausted. `asyncio.TimeoutError` propagates.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_client.py
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `./.venv/bin/python -m pytest tests/test_client.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'api.client'`.

- [ ] **Step 3: Write the implementation**

```python
# api/client.py
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `./.venv/bin/python -m pytest tests/test_client.py -v`
Expected: PASS (4 passed).

- [ ] **Step 5: Commit**

```bash
git add api/client.py tests/test_client.py
git commit -m "feat: resilient async client with backoff + timeout"
```

---

### Task 7: Function-calling contracts (schema · validation · error handling)

**Files:**
- Create: `api/function_calling.py`
- Test: `tests/test_function_calling.py`

**Interfaces:**
- Produces:
  - `TOOLS: dict[str, type[BaseModel]]` — registry mapping tool name → strict Pydantic args model. Includes `"get_weather"` → `GetWeatherArgs(city: str, units: Literal["celsius","fahrenheit"]="celsius")`.
  - `tool_names() -> list[str]`
  - `tool_schema(name: str) -> dict` → `{"name": name, "parameters": <json schema>}`
  - `validate_tool_call(name: str, raw_args: str) -> tuple[bool, dict | None, str | None]` → `(validated, parsed_args, error)`. Handles unknown tool, non-JSON args, and schema-invalid args without raising.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_function_calling.py
from api.function_calling import tool_names, tool_schema, validate_tool_call


def test_tool_names_includes_get_weather():
    assert "get_weather" in tool_names()


def test_tool_schema_has_parameters():
    schema = tool_schema("get_weather")
    assert schema["name"] == "get_weather"
    props = schema["parameters"]["properties"]
    assert "city" in props and "units" in props


def test_validate_good_args():
    ok, parsed, err = validate_tool_call("get_weather", '{"city": "London", "units": "celsius"}')
    assert ok is True
    assert parsed == {"city": "London", "units": "celsius"}
    assert err is None


def test_validate_non_json_args():
    ok, parsed, err = validate_tool_call("get_weather", "{not-json")
    assert ok is False
    assert parsed is None
    assert "JSON" in err


def test_validate_schema_violation():
    # units must be one of the Literal values
    ok, parsed, err = validate_tool_call("get_weather", '{"city": "London", "units": "kelvin"}')
    assert ok is False
    assert parsed is None
    assert err  # human-readable validation error


def test_validate_unknown_tool():
    ok, parsed, err = validate_tool_call("nonexistent", "{}")
    assert ok is False
    assert "unknown tool" in err.lower()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `./.venv/bin/python -m pytest tests/test_function_calling.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'api.function_calling'`.

- [ ] **Step 3: Write the implementation**

```python
# api/function_calling.py
from __future__ import annotations

import json
from typing import Literal

from pydantic import BaseModel, ConfigDict, ValidationError


class GetWeatherArgs(BaseModel):
    """The typed contract for the get_weather tool's arguments."""
    model_config = ConfigDict(strict=True, extra="forbid")
    city: str
    units: Literal["celsius", "fahrenheit"] = "celsius"


# Registry: tool name -> strict args model. Add new tools here.
TOOLS: dict[str, type[BaseModel]] = {
    "get_weather": GetWeatherArgs,
}


def tool_names() -> list[str]:
    return list(TOOLS)


def tool_schema(name: str) -> dict:
    """JSON schema the model would be handed to produce a valid tool call."""
    model = TOOLS[name]
    return {"name": name, "parameters": model.model_json_schema()}


def validate_tool_call(name: str, raw_args: str) -> tuple[bool, dict | None, str | None]:
    """Validate a raw (string) tool-call payload against its Pydantic contract.

    Returns (validated, parsed_args, error). Never raises — every failure mode
    (unknown tool, non-JSON, schema violation) returns a human-readable error string.
    """
    model = TOOLS.get(name)
    if model is None:
        return False, None, f"unknown tool: {name}"

    try:
        data = json.loads(raw_args)
    except json.JSONDecodeError as exc:
        return False, None, f"arguments are not valid JSON: {exc}"

    try:
        parsed = model.model_validate(data)
    except ValidationError as exc:
        return False, None, f"arguments failed validation: {exc.errors(include_url=False)}"

    return True, parsed.model_dump(), None
```

- [ ] **Step 4: Run test to verify it passes**

Run: `./.venv/bin/python -m pytest tests/test_function_calling.py -v`
Expected: PASS (6 passed).

- [ ] **Step 5: Commit**

```bash
git add api/function_calling.py tests/test_function_calling.py
git commit -m "feat: function-calling contracts — schema, validation, error handling"
```

---

### Task 8: FastAPI app & endpoints

**Files:**
- Create: `api/main.py`
- Test: `tests/test_api.py`

**Interfaces:**
- Consumes: everything from Tasks 2–7.
- Produces: `app = FastAPI(...)` with:
  - `GET /health` → `{"status": "ok"}`
  - `GET /providers` → `{"providers": [...], "default": settings.default_provider}`
  - `POST /chat` (body `ChatRequest`) → `ChatResponse`; maps exhausted `TransientError`→502, `ProviderError`→400, `asyncio.TimeoutError`→504, each as an `ErrorEnvelope`.
  - `POST /chat/stream` (body `ChatRequest`) → `text/event-stream` of the response content, word by word.
  - `POST /tools/call` (body `ToolCallRequest`) → `ToolCallResult`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_api.py
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `./.venv/bin/python -m pytest tests/test_api.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'api.main'`.

- [ ] **Step 3: Write the implementation**

```python
# api/main.py
from __future__ import annotations

import asyncio

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse

from api.client import resilient_chat
from api.config import settings
from api.errors import ErrorEnvelope, ProviderError, TransientError
from api.function_calling import validate_tool_call
from api.models import ChatRequest, ChatResponse, ToolCallRequest, ToolCallResult
from api.providers import available_providers, make_provider

app = FastAPI(title="Lab 2-A — Typed LLM Wrapper", version="0.1.0")


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@app.get("/providers")
async def providers() -> dict:
    return {"providers": available_providers(settings), "default": settings.default_provider}


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    try:
        provider = make_provider(
            request.provider or settings.default_provider,
            settings,
            fail_first_k=request.fail_first_k,
        )
    except ProviderError as exc:
        raise HTTPException(
            status_code=400,
            detail=ErrorEnvelope(error_type="ProviderError", message=str(exc), retryable=False).model_dump(),
        )

    attempt_holder = {"n": 0}
    try:
        # max_retries=3 means fail_first_k>3 demonstrates exhaustion in the UI.
        return await resilient_chat(provider, request, max_retries=3, base_delay=0.05)
    except TransientError as exc:
        raise HTTPException(
            status_code=502,
            detail=ErrorEnvelope(
                error_type="TransientError", message=str(exc), retryable=True, attempts=4,
            ).model_dump(),
        )
    except asyncio.TimeoutError:
        raise HTTPException(
            status_code=504,
            detail=ErrorEnvelope(error_type="TimeoutError", message="provider timed out", retryable=True).model_dump(),
        )
    finally:
        del attempt_holder


@app.post("/chat/stream")
async def chat_stream(request: ChatRequest) -> StreamingResponse:
    provider = make_provider(request.provider or settings.default_provider, settings)

    async def event_gen():
        resp = await resilient_chat(provider, request, max_retries=3, base_delay=0.05)
        for word in resp.content.split():
            yield f"data: {word}\n\n"
            await asyncio.sleep(0.02)
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_gen(), media_type="text/event-stream")


@app.post("/tools/call", response_model=ToolCallResult)
async def tools_call(request: ToolCallRequest) -> ToolCallResult:
    provider = make_provider(
        request.provider or settings.default_provider, settings, bad_args=request.force_bad_args
    )
    from api.function_calling import tool_schema

    raw = await provider.call_tool(request, [tool_schema(request.tool_name)])
    validated, parsed, error = validate_tool_call(request.tool_name, raw["arguments"])
    return ToolCallResult(
        tool_name=request.tool_name,
        raw_args=raw["arguments"],
        validated=validated,
        parsed_args=parsed,
        error=error,
    )
```

> Note: the `attempt_holder` scaffold is removed in Step 4 cleanup — see below. (Kept out: do not ship dead code.)

- [ ] **Step 4: Remove the dead `attempt_holder` scaffold**

Edit `api/main.py` to delete the three `attempt_holder` lines (the `attempt_holder = {"n": 0}` assignment and the `finally: del attempt_holder` block). The `chat` body should read straight from `try:` to the `except` handlers with no `finally`.

- [ ] **Step 5: Run test to verify it passes**

Run: `./.venv/bin/python -m pytest tests/test_api.py -v`
Expected: PASS (9 passed).

- [ ] **Step 6: Commit**

```bash
git add api/main.py tests/test_api.py
git commit -m "feat: FastAPI endpoints — chat, stream, tools, providers, health"
```

---

### Task 9: Live providers (OpenAI · Anthropic · Azure) — lazy, key-gated

**Files:**
- Create: `api/providers/openai_provider.py`, `api/providers/anthropic_provider.py`, `api/providers/azure_provider.py`
- Test: `tests/test_real_providers_optional.py`

**Interfaces:**
- Consumes: `Settings` (Task 5); `ChatRequest`, `ProviderResult`, `Usage` (Task 2); `ProviderError` (Task 3).
- Produces: `OpenAIProvider(settings)`, `AnthropicProvider(settings)`, `AzureProvider(settings)`, each with `name`, `is_mock=False`, `async def chat(...) -> ProviderResult`, `async def call_tool(...) -> dict`. SDKs are imported **inside `__init__`/methods**, never at module top level.

- [ ] **Step 1: Write the (skip-by-default) test**

```python
# tests/test_real_providers_optional.py
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
```

- [ ] **Step 2: Run test to verify import test passes, live tests skip**

Run: `./.venv/bin/python -m pytest tests/test_real_providers_optional.py -v`
Expected: FAIL initially — `ModuleNotFoundError: No module named 'api.providers.openai_provider'`.

- [ ] **Step 3: Write `api/providers/openai_provider.py`**

```python
# api/providers/openai_provider.py
from __future__ import annotations

import json

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
```

- [ ] **Step 4: Write `api/providers/anthropic_provider.py`**

```python
# api/providers/anthropic_provider.py
from __future__ import annotations

import json

from api.config import Settings
from api.errors import ProviderError
from api.models import ChatRequest, ProviderResult, Usage


class AnthropicProvider:
    name = "anthropic"
    is_mock = False

    def __init__(self, settings: Settings):
        if not settings.anthropic_api_key:
            raise ProviderError("ANTHROPIC_API_KEY not set")
        from anthropic import AsyncAnthropic  # lazy import

        self._client = AsyncAnthropic(api_key=settings.anthropic_api_key)
        self._model = settings.anthropic_model

    def _split(self, request: ChatRequest):
        system = "\n".join(m.content for m in request.messages if m.role == "system")
        msgs = [{"role": m.role, "content": m.content} for m in request.messages if m.role != "system"]
        return system or None, msgs

    async def chat(self, request: ChatRequest) -> ProviderResult:
        system, msgs = self._split(request)
        resp = await self._client.messages.create(
            model=self._model,
            system=system or "",
            messages=msgs,
            max_tokens=request.max_tokens,
        )
        text = "".join(block.text for block in resp.content if block.type == "text")
        return ProviderResult(
            model=resp.model,
            content=text,
            usage=Usage(
                prompt_tokens=resp.usage.input_tokens,
                completion_tokens=resp.usage.output_tokens,
            ),
        )

    async def call_tool(self, request: ChatRequest, tools: list[dict]) -> dict:
        schema = tools[0]
        system, msgs = self._split(request)
        resp = await self._client.messages.create(
            model=self._model,
            system=system or "",
            messages=msgs,
            max_tokens=request.max_tokens,
            tools=[{
                "name": schema["name"],
                "description": f"Call {schema['name']}",
                "input_schema": schema["parameters"],
            }],
        )
        for block in resp.content:
            if block.type == "tool_use":
                return {"name": block.name, "arguments": json.dumps(block.input)}
        return {"name": schema["name"], "arguments": "{}"}
```

- [ ] **Step 5: Write `api/providers/azure_provider.py`**

```python
# api/providers/azure_provider.py
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
```

- [ ] **Step 6: Run test to verify import passes, live tests skip**

Run: `./.venv/bin/python -m pytest tests/test_real_providers_optional.py -v`
Expected: PASS for `test_modules_import_without_sdk_at_top_level`; the two live tests reported as SKIPPED (no keys). (If `openai`/`anthropic` SDKs aren't installed, the import test still passes because the SDK import is inside `__init__`, not module top-level.)

- [ ] **Step 7: Commit**

```bash
git add api/providers/openai_provider.py api/providers/anthropic_provider.py api/providers/azure_provider.py tests/test_real_providers_optional.py
git commit -m "feat: lazy key-gated OpenAI/Anthropic/Azure providers"
```

---

### Task 10: Streamlit teaching app (5 tabs)

**Files:**
- Create: `ui/streamlit_app.py`
- Test: `tests/test_ui_smoke.py`

**Interfaces:**
- Consumes: the running FastAPI app over HTTP at `API_BASE_URL` (default `http://localhost:8000`).
- Produces: a Streamlit script with helper `api_url(path: str) -> str` and a `main()` that renders five tabs. Importing the module must have no side effects (no network calls at import).

- [ ] **Step 1: Write the failing smoke test**

```python
# tests/test_ui_smoke.py
def test_streamlit_app_imports_without_side_effects():
    # Importing must not call the network or render anything.
    import importlib
    mod = importlib.import_module("ui.streamlit_app")
    assert hasattr(mod, "main")
    assert mod.api_url("/health").endswith("/health")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `./.venv/bin/python -m pytest tests/test_ui_smoke.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'ui.streamlit_app'`.

- [ ] **Step 3: Write the implementation**

```python
# ui/streamlit_app.py
"""Lab 2-A — self-explanatory Streamlit teaching app.

Every tab pairs a LIVE demo with a "What's happening / Why it matters" hint panel.
This UI is a pure HTTP client to the FastAPI wrapper — it never imports the SDKs.
Run the API first (./run.sh does both): uvicorn api.main:app --port 8000
"""
from __future__ import annotations

import asyncio
import os
import time

import httpx
import streamlit as st

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")


def api_url(path: str) -> str:
    return f"{API_BASE_URL.rstrip('/')}{path}"


def _get(path: str):
    return httpx.get(api_url(path), timeout=30.0)


def _post(path: str, payload: dict):
    return httpx.post(api_url(path), json=payload, timeout=30.0)


def hint(title: str, body: str) -> None:
    with st.expander(f"💡 {title}"):
        st.markdown(body)


# ---- Tab renderers -------------------------------------------------------

def tab_overview() -> None:
    st.subheader("Provider status")
    st.caption("This lab runs fully offline on the **mock** provider. Real providers light up when their keys are set.")
    try:
        resp = _get("/providers")
        data = resp.json()
    except Exception as exc:  # API not running
        st.error(f"Cannot reach the API at {API_BASE_URL}. Start it with ./run.sh. ({exc})")
        return
    cols = st.columns(len(data["providers"]))
    for col, p in zip(cols, data["providers"]):
        with col:
            state = "🟢 live" if p["available"] else "⚪ off"
            badge = "mock" if p["is_mock"] else "real"
            st.metric(p["name"], state, help=f"{badge} provider")
    st.info(f"Default provider: **{data['default']}**")
    hint(
        "Why a client/server split?",
        "The Streamlit UI you're using makes **HTTP calls** to a typed FastAPI wrapper "
        "(`api/main.py`). The UI never touches the OpenAI/Anthropic SDKs — that boundary is "
        "exactly what an FDE ships: a typed service other apps call. Provider availability comes "
        "from `GET /providers`, computed in `api/providers/__init__.py`.",
    )


def tab_async() -> None:
    st.subheader("Async patterns: concurrent vs sequential")
    n = st.slider("How many requests to fire?", 1, 10, 5)
    prompt = st.text_input("Prompt", "hello", key="async_prompt")
    if st.button("Run concurrently", key="async_run"):
        async def fire_all():
            async with httpx.AsyncClient(timeout=30.0) as ac:
                tasks = [
                    ac.post(api_url("/chat"), json={"messages": [{"role": "user", "content": f"{prompt} {i}"}]})
                    for i in range(n)
                ]
                return await asyncio.gather(*tasks)

        start = time.perf_counter()
        results = asyncio.run(fire_all())
        elapsed = time.perf_counter() - start
        st.success(f"{len(results)} concurrent requests finished in {elapsed:.3f}s")
        st.json([r.json()["content"] for r in results])
    hint(
        "Why async for AI workloads?",
        "LLM calls are **I/O-bound** — most of the time is spent waiting on the network. "
        "`asyncio.gather` fires all requests concurrently so total time ≈ the *slowest* call, "
        "not the *sum*. The server side uses `async def` endpoints + `asyncio.wait_for` "
        "(`api/client.py`) so one slow call never blocks the event loop.",
    )


def tab_pydantic() -> None:
    st.subheader("Strict Pydantic v2 validation")
    st.caption("Edit the JSON and send it to `POST /chat`. Strict mode rejects extra fields and type coercion.")
    default = '{\n  "messages": [{"role": "user", "content": "hi"}],\n  "max_tokens": 64\n}'
    raw = st.text_area("Request body (JSON)", default, height=180, key="pyd_body")
    if st.button("Validate + send", key="pyd_run"):
        import json
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError as exc:
            st.error(f"Not valid JSON: {exc}")
            return
        resp = _post("/chat", payload)
        if resp.status_code == 200:
            st.success("Accepted by the strict model ✅")
            st.json(resp.json())
        else:
            st.error(f"Rejected (HTTP {resp.status_code}) — this is strict validation at work:")
            st.json(resp.json())
    hint(
        "What 'strict' buys you",
        "`ChatRequest` (`api/models.py`) uses `ConfigDict(strict=True, extra='forbid')`. "
        "Try adding `\"temperature\": 0.7` → **422**, an unknown field is rejected. "
        "Try `\"max_tokens\": \"64\"` (a string) → **422**, strict mode refuses to coerce "
        "`\"64\"`→`64`. In production this turns silent, hard-to-debug payload drift into a "
        "loud, typed error at the boundary.",
    )


def tab_retries() -> None:
    st.subheader("Typed client with retries + backoff")
    k = st.slider("Inject failures: fail the first K calls", 0, 6, 2, key="retry_k")
    st.caption("The client retries up to 3 times with exponential backoff. K>3 exhausts retries → typed 502.")
    if st.button("Send", key="retry_run"):
        resp = _post("/chat", {"messages": [{"role": "user", "content": "hi"}], "fail_first_k": k})
        if resp.status_code == 200:
            body = resp.json()
            st.success(f"Succeeded after **{body['attempts']}** attempt(s)")
            st.json(body)
        else:
            st.error(f"Retries exhausted → HTTP {resp.status_code}. The failure is a *typed envelope*, not a stack trace:")
            st.json(resp.json())
    hint(
        "Retries, backoff, and typed failure",
        "`resilient_chat` (`api/client.py`) catches `TransientError`, waits "
        "`base_delay * 2**(attempt-1)`, and retries up to 3 times. The `fail_first_k` lever is "
        "honoured only by the mock provider so the demo is deterministic. When retries run out, "
        "the endpoint returns a typed `ErrorEnvelope` (`api/errors.py`) with `retryable=true` — "
        "callers can branch on the shape instead of parsing strings.",
    )


def tab_tools() -> None:
    st.subheader("Function-calling contracts")
    try:
        tool = "get_weather"
        schema = _get("/providers")  # liveness check
    except Exception as exc:
        st.error(f"Cannot reach the API: {exc}")
        return
    prompt = st.text_input("Prompt", "What's the weather in London?", key="tool_prompt")
    bad = st.checkbox("Force malformed arguments (see error handling)", key="tool_bad")
    if st.button("Call tool", key="tool_run"):
        resp = _post("/tools/call", {"tool_name": tool, "prompt": prompt, "force_bad_args": bad})
        body = resp.json()
        st.write("**Raw arguments returned by the model:**")
        st.code(body["raw_args"], language="json")
        if body["validated"]:
            st.success("Validated against the Pydantic contract ✅")
            st.json(body["parsed_args"])
        else:
            st.error("Validation failed — handled gracefully, not crashed:")
            st.code(str(body["error"]))
    hint(
        "Schema → validation → error handling",
        "The tool's argument contract is a strict Pydantic model `GetWeatherArgs` "
        "(`api/function_calling.py`); its JSON schema is what the model is handed. The raw "
        "string the model emits is validated with `validate_tool_call`, which **never raises** — "
        "non-JSON or schema-violating args come back as a typed `ToolCallResult.error`. Tick the "
        "box to watch malformed args be caught instead of blowing up your app.",
    )


def main() -> None:
    st.set_page_config(page_title="Lab 2-A — Typed AI Scaffolding", layout="wide")
    st.title("Lab 2-A — Typed FastAPI + LLM SDK, explained")
    st.caption("A self-explanatory tour of async, strict Pydantic, resilient typed clients, and function-calling contracts.")
    tabs = st.tabs([
        "0 · Overview",
        "1 · Async patterns",
        "2 · Strict Pydantic",
        "3 · Client + retries",
        "4 · Function calling",
    ])
    with tabs[0]:
        tab_overview()
    with tabs[1]:
        tab_async()
    with tabs[2]:
        tab_pydantic()
    with tabs[3]:
        tab_retries()
    with tabs[4]:
        tab_tools()


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `./.venv/bin/python -m pytest tests/test_ui_smoke.py -v`
Expected: PASS (1 passed).

- [ ] **Step 5: Commit**

```bash
git add ui/streamlit_app.py tests/test_ui_smoke.py
git commit -m "feat: Streamlit 5-tab teaching app over the typed API"
```

---

### Task 11: Runner, docs, and full offline-green verification

**Files:**
- Create: `run.sh`, `README.md`, `00_START_HERE.md`

**Interfaces:**
- Consumes: everything. Produces the learner entry point + the launch script.

- [ ] **Step 1: Create `run.sh`**

```bash
#!/usr/bin/env bash
# Lab 2-A — launch the API (background) then the Streamlit UI (foreground).
set -euo pipefail
cd "$(dirname "$0")"

PY="./.venv/bin/python"
[ -x "$PY" ] || { echo "Run ./setup.sh first."; exit 1; }

echo "Starting API on http://localhost:8000 ..."
"$PY" -m uvicorn api.main:app --port 8000 &
API_PID=$!
trap 'kill $API_PID 2>/dev/null || true' EXIT

# Wait for /health before launching the UI.
for _ in $(seq 1 30); do
  if "$PY" -c "import httpx,sys; sys.exit(0 if httpx.get('http://localhost:8000/health').status_code==200 else 1)" 2>/dev/null; then
    break
  fi
  sleep 0.5
done

echo "Starting Streamlit on http://localhost:8501 ..."
"$PY" -m streamlit run ui/streamlit_app.py
```

- [ ] **Step 2: Create `00_START_HERE.md`**

```markdown
# Lab 2-A — Start Here

A self-explanatory teaching app: a **typed FastAPI wrapper** around the LLM SDKs, driven by a
**Streamlit UI** with five concept tabs. Runs **fully offline** on a mock provider — no API keys needed.

## Run it (2 commands)

```bash
./setup.sh     # creates .venv (uv or python3.12), installs, runs the tests
./run.sh       # starts the API on :8000 and the Streamlit UI on :8501
```

Open http://localhost:8501 and walk the tabs left to right.

## What each tab teaches

| Tab | Concept | Source to read |
|-----|---------|----------------|
| 0 · Overview | client/server split, offline-first | `api/providers/__init__.py` |
| 1 · Async patterns | `async`/`await`, concurrency | `api/client.py` |
| 2 · Strict Pydantic | `strict=True`, `extra="forbid"` | `api/models.py` |
| 3 · Client + retries | backoff, timeout, typed errors | `api/client.py`, `api/errors.py` |
| 4 · Function calling | schema · validation · error handling | `api/function_calling.py` |

## Go live (optional)

Copy `.env.example` to `.env` and set any provider key (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, or the
Azure trio). Restart `./run.sh`; the Overview tab will show that provider as 🟢 live and you can pick it
per request.
```

- [ ] **Step 3: Create `README.md`**

```markdown
# Lab 2-A — Typed FastAPI + Streamlit AI Scaffolding

Teaching lab for FORGE Batch-1 (Python for AI Scaffolding). Demonstrates the FDE-foundational
Python/AI building blocks with a real typed service and a self-explanatory UI.

- **Topics:** async patterns · Pydantic v2 strict models · type hints · packaging with `uv` ·
  typed LLM clients with retries (OpenAI/Anthropic/Azure) · function-calling contracts.
- **Design:** Streamlit UI → HTTP → FastAPI wrapper → resilient async client → provider
  (mock by default; live when keys are set).
- **Offline-first:** every non-optional test and the whole UI work with zero API keys.

## Layout

```
api/    typed FastAPI wrapper (models, errors, client, function_calling, providers)
ui/     Streamlit teaching app (HTTP client to api/)
tests/  pytest — offline-green
```

## Commands

```bash
./setup.sh                         # venv + install + tests
./run.sh                           # API (:8000) + Streamlit (:8501)
./.venv/bin/python -m pytest -q    # tests only
```

> House rule: "works in `.venv`" is a **draft**. Final sign-off is a clean `./setup.sh` + `./run.sh`
> on the Techademy Azure VM.
```

- [ ] **Step 4: Make runner executable and run the full suite offline**

Run:
```bash
chmod +x run.sh
./.venv/bin/python -m pytest -q
```
Expected: all tests pass, the two live-provider tests skipped (e.g. `30+ passed, 2 skipped`), zero failures, no network access.

- [ ] **Step 5: Manually smoke-test the running app**

Run:
```bash
./.venv/bin/python -m uvicorn api.main:app --port 8000 &
sleep 2
curl -s localhost:8000/health
curl -s localhost:8000/providers
curl -s -X POST localhost:8000/chat -H 'content-type: application/json' -d '{"messages":[{"role":"user","content":"hi"}]}'
curl -s -X POST localhost:8000/chat -H 'content-type: application/json' -d '{"messages":[{"role":"user","content":"hi"}],"fail_first_k":9}'
kill %1
```
Expected: `{"status":"ok"}`; a providers list with `mock` available; an `echo: hi` ChatResponse with `attempts:1`; and a 502 `ErrorEnvelope` for the exhausted-retry case.

- [ ] **Step 6: Commit**

```bash
git add run.sh README.md 00_START_HERE.md
git commit -m "docs: runner script + learner start guide; verify offline-green"
```

---

## Self-Review

**Spec coverage:**
- async patterns → Task 6 (client), Task 8 (`/chat/stream`), Task 10 tab 1 ✅
- Pydantic v2 strict → Task 2, Task 10 tab 2 ✅
- type hints → present throughout (all signatures typed) ✅
- packaging with uv → Task 1 (`pyproject.toml`, `setup.sh`) ✅
- OpenAI/Anthropic/Azure typed clients with retries → Task 9 + Task 6 ✅
- function calling: schema/validation/error handling → Task 7, Task 10 tab 4 ✅
- offline-first / live optional → Tasks 4, 5, 9 ✅
- teaching/demo app with inline hints → Task 10 ✅
- self-contained folder convention → Tasks 1, 11 ✅
- error handling (typed envelope, status mapping) → Tasks 3, 8 ✅
- testing (strict, retries, tools, endpoints, smoke, optional live) → Tasks 2–10 ✅

**Placeholder scan:** No TBD/TODO; all code blocks complete. The one scaffold (`attempt_holder`) is explicitly removed in Task 8 Step 4 with a stated reason (no dead code shipped).

**Type consistency:** `ProviderResult`/`ChatResponse`/`Usage` names consistent across Tasks 2, 4, 6, 9. `make_provider`/`available_providers` signatures consistent between Task 5 and Task 8. `validate_tool_call` return tuple consistent between Task 7 and Task 10. Provider attribute contract (`name`, `is_mock`, `chat`, `call_tool`) consistent across mock (Task 4) and live (Task 9).
