from __future__ import annotations

import asyncio

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse

from api.client import resilient_chat
from api.config import settings
from api.errors import ErrorEnvelope, ProviderError, TransientError
from api.function_calling import validate_tool_call, tool_schema
from api.models import ChatRequest, ChatResponse, ToolCallRequest, ToolCallResult
from api.providers import available_providers, make_provider

app = FastAPI(title="Lab 2-A — Typed LLM Wrapper", version="0.1.0")

CHAT_MAX_RETRIES = 3


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
            detail=ErrorEnvelope(
                error_type="ProviderError", message=str(exc), retryable=False
            ).model_dump(),
        )

    try:
        return await resilient_chat(provider, request, max_retries=CHAT_MAX_RETRIES, base_delay=0.05)
    except TransientError as exc:
        raise HTTPException(
            status_code=502,
            detail=ErrorEnvelope(
                error_type="TransientError", message=str(exc), retryable=True, attempts=CHAT_MAX_RETRIES + 1
            ).model_dump(),
        )
    except asyncio.TimeoutError:
        raise HTTPException(
            status_code=504,
            detail=ErrorEnvelope(
                error_type="TimeoutError", message="provider timed out", retryable=True
            ).model_dump(),
        )


@app.post("/chat/stream")
async def chat_stream(request: ChatRequest) -> StreamingResponse:
    try:
        provider = make_provider(request.provider or settings.default_provider, settings)
    except ProviderError as exc:
        raise HTTPException(
            status_code=400,
            detail=ErrorEnvelope(
                error_type="ProviderError", message=str(exc), retryable=False
            ).model_dump(),
        )

    async def event_gen():
        resp = await resilient_chat(provider, request, max_retries=CHAT_MAX_RETRIES, base_delay=0.05)
        for word in resp.content.split():
            yield f"data: {word}\n\n"
            await asyncio.sleep(0.02)
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_gen(), media_type="text/event-stream")


@app.post("/tools/call", response_model=ToolCallResult)
async def tools_call(request: ToolCallRequest) -> ToolCallResult:
    try:
        provider = make_provider(
            request.provider or settings.default_provider,
            settings,
            bad_args=request.force_bad_args,
        )
    except ProviderError as exc:
        raise HTTPException(
            status_code=400,
            detail=ErrorEnvelope(
                error_type="ProviderError", message=str(exc), retryable=False
            ).model_dump(),
        )
    raw = await provider.call_tool(request, [tool_schema(request.tool_name)])
    validated, parsed, error = validate_tool_call(request.tool_name, raw["arguments"])
    return ToolCallResult(
        tool_name=request.tool_name,
        raw_args=raw["arguments"],
        validated=validated,
        parsed_args=parsed,
        error=error,
    )
