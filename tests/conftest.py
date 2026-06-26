"""Hermetic test environment.

The lab "runs fully offline on the mock provider", and the test suite encodes that
assumption: it expects no live provider keys and `default_provider == "mock"`. But
`api.config.Settings` reads the developer's real `.env` (which may carry a live
OPENAI_API_KEY and DEFAULT_PROVIDER=openai once you've gone live). Without isolation,
those values leak in and break offline tests (unconfigured-provider 400s, mock-echo
assertions, retry demos).

pytest imports conftest.py before any test module, so setting these env vars here —
before `api.config` / `api.main` are imported — makes them authoritative. In
pydantic-settings, environment variables take precedence over values in `.env`.
"""

import os

# Force a clean, offline, keyless environment regardless of the on-disk .env.
os.environ["DEFAULT_PROVIDER"] = "mock"
os.environ["OPENAI_API_KEY"] = ""
os.environ["ANTHROPIC_API_KEY"] = ""
os.environ["AZURE_OPENAI_API_KEY"] = ""
os.environ["AZURE_OPENAI_ENDPOINT"] = ""
