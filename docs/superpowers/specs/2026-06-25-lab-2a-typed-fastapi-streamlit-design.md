# Lab 2-A — Typed FastAPI + OpenAI SDK wrapper, explored through a Streamlit teaching app

**Date:** 2026-06-25
**Session:** Python for AI Scaffolding (FORGE Batch-1, D02 family)
**Author:** Lakshminarayanan (lead trainer)
**Status:** Approved design — ready for implementation plan

---

## 1. Purpose

A self-explanatory teaching lab that makes four FDE-foundational Python/AI concepts tangible:

- **Python for AI:** async patterns · Pydantic v2 strict models · type hints · packaging with `uv`
- **LLM SDK integration:** OpenAI · Anthropic · Azure OpenAI — typed clients with retries
- **Function-calling contracts:** schema definition · validation · error handling

The real artifact is a **typed FastAPI wrapper** around the LLM SDKs. A **Streamlit app** drives that
wrapper over HTTP and explains each concept inline, so learners both *use* and *see* the
client/server contract an FDE ships in production.

Lab 2-A is a **finished, self-explanatory teaching/demo app** — learners run it and explore. It is not
a build-it-yourself starter (that is the existing D02 starter→solution kit's job). Lab 2-A complements
the D02 kit; it does not replace it.

## 2. Key decisions (locked during brainstorming)

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Backend topology | **Streamlit calls FastAPI over HTTP** | Shows the full typed client/server boundary FDEs ship. |
| Provider strategy | **Offline-first, live optional** | Mock provider default → every learner runs with zero keys/quota; OpenAI/Anthropic/Azure auto-enable when their keys are present. |
| Lab style | **Teaching/demo app** | Concept tabs with live demos + inline hint panels; learners explore, not fill TODOs. |
| Packaging | `uv`, PEP 621 `pyproject.toml`, Python 3.12 | Matches existing kit convention. |
| Models | Latest Claude id `claude-opus-4-8` (Anthropic); a current OpenAI chat model | Per house guidance to default to latest capable models. |
| Run convention | Self-contained folder: `setup.sh`, `run.sh`, `.vscode/`, own `.venv` | Same learner muscle memory as the D02 kit. |

## 3. Folder layout

```
python-ai-scaffolding/                 (Lab 2-A)
├── 00_START_HERE.md, README.md        # learner orientation + concept map
├── pyproject.toml  .python-version    # uv packaging (PEP 621), Python 3.12
├── setup.sh   run.sh                  # setup.sh = uv venv+install+tests; run.sh = launch API+UI
├── .env.example   .gitignore  .vscode/# key template; pinned interpreter + F5 launch
├── api/                               # the typed FastAPI wrapper (the real lesson)
│   ├── __init__.py
│   ├── main.py            # endpoints: /health, /providers, /chat, /chat/stream, /tools/call
│   ├── config.py          # pydantic-settings; detects which providers are live
│   ├── models.py          # Pydantic v2 STRICT request/response models
│   ├── errors.py          # one typed error envelope {error_type, message, retryable}
│   ├── client.py          # async resilient call: timeout + bounded exponential backoff
│   ├── function_calling.py# tool schema (from Pydantic) + arg validation + dispatch
│   └── providers/
│       ├── __init__.py    # registry: which providers are available given env
│       ├── base.py        # Protocol all providers implement
│       ├── mock.py        # deterministic offline provider (failure injection + tool emit)
│       ├── openai_provider.py     # lazy SDK import, key-gated
│       ├── anthropic_provider.py  # lazy SDK import, key-gated
│       └── azure_provider.py      # lazy SDK import, key-gated
├── ui/
│   └── streamlit_app.py               # multi-tab teaching app (httpx client to api/)
└── tests/                             # pytest, offline-green
    ├── __init__.py
    ├── test_models.py        # strict accept/reject, extra-field rejection
    ├── test_client.py        # retry-then-succeed, retry-exhausted (mock failure injection)
    ├── test_function_calling.py  # good + bad tool args
    ├── test_api.py           # endpoint contracts via TestClient
    └── test_ui_smoke.py      # streamlit app imports cleanly
```

## 4. The five teaching tabs

Each tab = a **live interactive demo** + an **expandable "What's happening / Why it matters" hint panel**
that names the exact source file/symbol. Maps 1:1 to the topic list.

| Tab | Demo learners drive | Concept taught | Source it points at |
|-----|--------------------|----------------|---------------------|
| **0 · Overview** | Provider badges (mock/live) + health ping | offline-first design, client/server split | `config.py`, `providers/__init__.py` |
| **1 · Async patterns** | Fire N concurrent chats; live timing vs sequential | `async`/`await`, concurrency, gather | `client.py`, `main.py` |
| **2 · Strict Pydantic v2** | Edit raw JSON → accept/reject + field-level errors | `strict=True`, extra-field rejection, no coercion | `models.py` |
| **3 · Typed client + retries** | Slider "fail first K calls" → watch backoff, then typed result | retries/backoff, timeout, typed error envelope | `client.py`, `errors.py` |
| **4 · Function-calling contracts** | Pick a tool, send a prompt, see the tool-call **validated** against the Pydantic schema; toggle a bad-arg case | schema definition · validation · error handling | `function_calling.py` |

The **mock provider** is the teaching engine: it supports deterministic failure injection (for tab 3)
and deterministic tool-call emission (for tab 4) so every learner gets identical lessons with no keys.

## 5. Data flow

```
Streamlit tab
  → httpx (JSON)
    → FastAPI endpoint (validates request against strict Pydantic model)
      → ResilientClient.call(...)  (timeout + bounded exponential backoff)
        → Provider.chat(...)        (mock | openai | anthropic | azure)
      ← typed Pydantic response
    ← JSON (200) or typed ErrorEnvelope (4xx/5xx)
  ← Streamlit renders the result AND the validated objects/errors verbatim
```

## 6. API contract (sketch)

- `GET /health` → `{status: "ok"}`
- `GET /providers` → `{providers: [{name, available: bool, is_mock: bool}], default: str}`
- `POST /chat` → body `ChatRequest{provider?, messages[], max_tokens?, fail_first_k?}`; returns `ChatResponse{provider, model, content, usage, attempts}`
- `POST /chat/stream` → server-sent token stream (used by async tab to show streaming)
- `POST /tools/call` → body `ToolCallRequest{tool_name, prompt, force_bad_args?}`; returns `ToolCallResult{tool_name, raw_args, validated: bool, parsed_args?, error?}`

All request/response bodies are **strict** Pydantic v2 models. `fail_first_k` and `force_bad_args` are
teaching levers honoured only by the mock provider.

## 7. Error handling

- One typed `ErrorEnvelope{error_type, message, retryable: bool, attempts?}`.
- Request validation failure → HTTP 422 (FastAPI default, surfaced as envelope-shaped detail).
- Provider error after exhausted retries → 502; timeout → 504; bad tool args → 422 with field errors.
- The UI renders the envelope verbatim so learners see **structured failure**, never a raw stack trace.

## 8. Testing

- **pytest, fully offline (mock provider):**
  - `test_models.py` — strict accept/reject; extra fields rejected; no silent coercion.
  - `test_client.py` — retry-then-succeed with `fail_first_k`; retry-exhausted raises typed error; backoff bounded.
  - `test_function_calling.py` — valid args parse; `force_bad_args` produces a validation error, not a crash.
  - `test_api.py` — endpoint contracts via `fastapi.testclient.TestClient`.
  - `test_ui_smoke.py` — `ui/streamlit_app.py` imports without side effects.
- **Live-provider tests** are optional/skipped unless keys are set (mirrors D02's `test_real_providers_optional.py`).
- **Acceptance bar:** green offline in `.venv`. Per house rule, "works in `.venv`" is a draft until it
  runs on the Techademy Azure VM — final sign-off is a clean `setup.sh` + `run.sh` on the VM.

## 9. Run & packaging

- `setup.sh`: prefer `uv venv` + `uv pip install -e .`, fall back to `python3.12 -m venv` + `pip -e .`; then run `pytest`.
- `run.sh`: start `uvicorn api.main:app` in the background, wait for `/health`, then `streamlit run ui/streamlit_app.py`.
- Streamlit reads `API_BASE_URL` (default `http://localhost:8000`).
- `.vscode/`: interpreter pinned to `./.venv`, pytest runner on, F5 launches the API.

## 10. Out of scope (YAGNI)

- No auth, no persistence/DB, no Docker (local + VM venv only for this lab).
- No build-it-yourself TODOs or answer key (that is the D02 starter kit's role).
- No real-provider integration tests in the default run (key-gated/skipped only).
- No LMS PDF/PPTX build pipeline in this lab folder (D02 kit already owns that).

## 11. Relationship to the existing D02 kit

This lab lives alongside `Batch-1/prep/D02_python_ai_scaffolding/` and reuses its conventions
(self-contained folder, `uv`, `.vscode`, `setup.sh`, offline-first mock). It is an independent,
self-contained teaching app — no code import dependency on the D02 package — so it can be handed out
or demoed on its own.
