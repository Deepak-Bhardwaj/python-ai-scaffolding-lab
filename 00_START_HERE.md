# Lab 2-A — Start Here

A self-explanatory teaching app: a **typed FastAPI wrapper** around the LLM SDKs, driven by a
**Streamlit UI** with five concept tabs. Runs **fully offline** on a mock provider — no API keys needed.

## Run it (2 commands)

```bash
./setup.sh     # creates .venv (uv or python3.12), installs, runs the tests
./run.sh       # starts the API on :8000 and the Streamlit UI on :8501  (override: API_PORT=9000 ./run.sh)
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
