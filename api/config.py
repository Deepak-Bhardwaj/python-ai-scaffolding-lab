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
