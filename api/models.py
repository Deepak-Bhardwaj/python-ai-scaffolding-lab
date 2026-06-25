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
