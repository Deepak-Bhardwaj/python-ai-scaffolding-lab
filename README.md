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
./run.sh                           # API (:8000) + Streamlit (:8501)  (override: API_PORT=9000 ./run.sh)
./.venv/bin/python -m pytest -q    # tests only
```

> House rule: "works in `.venv`" is a **draft**. Final sign-off is a clean `./setup.sh` + `./run.sh`
> on the Techademy Azure VM.
