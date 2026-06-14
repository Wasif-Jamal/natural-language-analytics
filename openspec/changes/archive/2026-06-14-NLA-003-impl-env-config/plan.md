# Implementation Plan — NLA-003: `config/env_config.py`

## Context

Greenfield — no Python source files exist yet. This is the first implementation ticket.
Branch: `feature/config/NLA-003-impl-env-config`

---

## Files to Create

| Path | Action | Notes |
|---|---|---|
| `config/__init__.py` | Create (empty) | Required for `config` to be a Python package |
| `config/env_config.py` | Create | Main implementation |
| `tests/__init__.py` | Create (empty) | Required for pytest discovery |
| `tests/config/__init__.py` | Create (empty) | Required for pytest discovery |

No files are modified. No files are deleted.

---

## Architecture Decisions

### Return type: `@dataclass` (not TypedDict, SimpleNamespace, or module-level constants)

Chosen for: type safety, attribute access, IDE autocompletion, easy `replace()` in tests via `dataclasses.replace`. All downstream modules receive an `AppConfig` instance — they never call `os.getenv` directly.

### API key routing lives in `env_config.py`

`load_config()` detects `LLM_PROVIDER` and routes to the correct env var before returning `AppConfig.llm_api_key`. `llm_config.py` receives a pre-resolved key — it never reads env vars. This keeps API key logic in one place and makes it easy to test the routing in isolation.

### `load_dotenv()` called inside `load_config()`

Not at module import time. This means tests can set `os.environ` keys directly without `.env` file interference — monkeypatching works cleanly.

### `MAX_RESULT_ROWS` cast to `int` here

Not in `db_config.py`. Centralized type coercion at the config boundary means `db_config.py` receives a typed `int` and never deals with `ValueError` on cast.

---

## Implementation — `config/env_config.py`

### Dataclass definition

```python
@dataclass
class AppConfig:
    database_url: str
    llm_provider: str
    llm_api_key: str | None        # None for ollama; GEMINI_API_KEY value for gemini
    llm_model: str | None          # None means use provider default (resolved in llm_config.py)
    max_result_rows: int           # default 10_000
    log_level: str                 # default "INFO"
    log_file: str | None           # None means stdout only
```

### `load_config()` — validation order

Execute in this exact sequence (fail-fast, each step visible in any error):

1. `load_dotenv()` — loads `.env` if present; silently no-ops if absent
2. Read + validate `DATABASE_URL` (required, non-empty)
3. Read + validate `LLM_PROVIDER` (required, non-empty)
4. Validate `LLM_PROVIDER` is in `_ALLOWED_PROVIDERS = {"anthropic", "openai", "gemini", "ollama"}`
5. Resolve `llm_api_key` via provider routing (see below)
6. Resolve `llm_model` — `None` if absent or empty string
7. Cast `MAX_RESULT_ROWS` — default `10_000`; `ValueError` if set but non-numeric
8. Resolve `log_level` — default `"INFO"`
9. Resolve `log_file` — `None` if absent or empty string
10. Return `AppConfig(...)`

### API key routing logic

```
if llm_provider == "ollama":
    llm_api_key = None
elif llm_provider == "gemini":
    key = os.getenv("GEMINI_API_KEY", "")
    if not key:
        raise ValueError("GEMINI_API_KEY is required for provider 'gemini' but not set.")
    llm_api_key = key
else:  # anthropic | openai
    key = os.getenv("LLM_API_KEY", "")
    if not key:
        raise ValueError(f"LLM_API_KEY is required for provider '{llm_provider}' but not set.")
    llm_api_key = key
```

### Error message format (exact strings, used in tests)

| Condition | ValueError message |
|---|---|
| `DATABASE_URL` missing | `"DATABASE_URL is required but not set."` |
| `LLM_PROVIDER` missing | `"LLM_PROVIDER is required but not set."` |
| `LLM_PROVIDER` invalid | `"LLM_PROVIDER must be one of: anthropic, gemini, ollama, openai. Got: '<value>'."` |
| `LLM_API_KEY` missing (non-Gemini, non-Ollama) | `"LLM_API_KEY is required for provider '<provider>' but not set."` |
| `GEMINI_API_KEY` missing | `"GEMINI_API_KEY is required for provider 'gemini' but not set."` |
| `MAX_RESULT_ROWS` non-numeric | `"MAX_RESULT_ROWS must be a positive integer. Got: '<value>'."` |

Note: the allowed-values list in the provider error is sorted alphabetically so the message is deterministic in tests.

### Imports (complete list — nothing else)

```python
from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv
```

No `streamlit`, no provider SDK, no service import.

---

## Test Scaffolding Note (NLA-007)

Tests will use `monkeypatch.setenv` / `monkeypatch.delenv` to control the environment. Because `load_dotenv()` is called inside `load_config()` (not at import time), tests do not need to create a `.env` file — they just manipulate `os.environ` directly. No mocking of `load_dotenv` is needed.

Minimum test cases for NLA-007:
1. All vars present → returns `AppConfig` instance
2. Missing `DATABASE_URL` → `ValueError` containing `"DATABASE_URL"`
3. Missing `LLM_PROVIDER` → `ValueError` containing `"LLM_PROVIDER"`
4. Invalid `LLM_PROVIDER` → `ValueError` containing the bad value
5. `LLM_PROVIDER=anthropic`, no `LLM_API_KEY` → `ValueError` containing `"LLM_API_KEY"`
6. `LLM_PROVIDER=gemini`, `GEMINI_API_KEY` set → success, `config.llm_api_key == key`
7. `LLM_PROVIDER=gemini`, no `GEMINI_API_KEY` → `ValueError` containing `"GEMINI_API_KEY"`
8. `LLM_PROVIDER=ollama`, no `LLM_API_KEY` → success, `config.llm_api_key is None`
9. `MAX_RESULT_ROWS` absent → `config.max_result_rows == 10000`
10. `MAX_RESULT_ROWS=lots` → `ValueError` containing `"MAX_RESULT_ROWS"`

---

## Quality Gate Commands

Run in order after implementation:

```bash
uv run ruff format config/env_config.py
uv run ruff check config/env_config.py
uv run pytest tests/config/test_env_config.py   # run after NLA-007 tests are written
```

Full suite before commit:

```bash
uv run ruff format . && uv run ruff check . && uv run pytest
```

---

## Out of Scope for This Ticket

- `log_config.py`, `db_config.py`, `llm_config.py` — separate tickets (NLA-004, NLA-005, NLA-006)
- `starter.py` — NLA-011
- Tests for `env_config.py` — NLA-007 (written after this implementation is committed)
- Validating `LOG_LEVEL` is one of `{DEBUG, INFO, WARNING, ERROR}` — not specified in the spec; log_config handles level mapping
