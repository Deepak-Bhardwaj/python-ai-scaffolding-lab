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
        _get("/health")  # liveness check — raises on connection error
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
