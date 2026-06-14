# Tasks — NLA-003: `config/env_config.py`

Branch: `feature/config/NLA-003-impl-env-config`

---

## Phase 1 — Foundation (package scaffolding)

- [x] Create `config/__init__.py` — empty file; makes `config/` a Python package
- [x] Create `tests/__init__.py` — empty file; required for pytest discovery
- [x] Create `tests/config/__init__.py` — empty file; required for pytest discovery

> **Checkpoint:**
> ```bash
> uv run ruff check config/ tests/
> ```
> Expected: 0 errors (empty files pass trivially)

---

## Phase 2 — Core Implementation

- [x] Create `config/env_config.py` — add imports (`from __future__ import annotations`, `os`, `dataclasses.dataclass`, `dotenv.load_dotenv`) and module-level constant `_ALLOWED_PROVIDERS = {"anthropic", "openai", "gemini", "ollama"}`
- [x] Define `AppConfig` dataclass with 7 typed fields: `database_url: str`, `llm_provider: str`, `llm_api_key: str | None`, `llm_model: str | None`, `max_result_rows: int`, `log_level: str`, `log_file: str | None`
- [x] Implement `load_config()` steps 1–4: call `load_dotenv()`, validate `DATABASE_URL` (required, non-empty), validate `LLM_PROVIDER` (required, non-empty), validate provider in allowlist — raise `ValueError` with sorted list on mismatch
- [x] Implement `load_config()` step 5 — API key routing: `ollama` → `None`; `gemini` → read `GEMINI_API_KEY` (raise on missing); all others → read `LLM_API_KEY` (raise on missing, include provider name in message)
- [x] Implement `load_config()` steps 6–10: resolve `llm_model` (`None` if absent/empty), cast `MAX_RESULT_ROWS` to `int` (default `10_000`, `ValueError` if non-numeric), resolve `log_level` (default `"INFO"`), resolve `log_file` (`None` if absent/empty), return `AppConfig(...)`

> **Checkpoint:**
> ```bash
> uv run ruff format config/env_config.py
> uv run ruff check config/env_config.py
> ```
> Expected: 0 format diffs, 0 lint errors

---

## Phase 3 — Integration

- [x] Verify `config/env_config.py` imports — confirm no `streamlit`, `anthropic`, `openai`, `google`, `sqlalchemy`, or service module is imported (manual inspection + grep)

```bash
grep -n "^import\|^from" config/env_config.py
```

Expected output contains only: `from __future__`, `import os`, `from dataclasses`, `from dotenv`

---

## Phase 4 — Tests

File: `tests/config/test_env_config.py`

One test per spec scenario:

- [x] `test_all_required_vars_returns_appconfig` — set `DATABASE_URL`, `LLM_PROVIDER=anthropic`, `LLM_API_KEY`; assert `load_config()` returns an `AppConfig` instance
- [x] `test_appconfig_is_dataclass` — assert result is a dataclass instance; access `config.database_url` as attribute (not subscript)
- [x] `test_missing_database_url_raises` — unset `DATABASE_URL`; assert `ValueError` message contains `"DATABASE_URL"`
- [x] `test_missing_llm_provider_raises` — unset `LLM_PROVIDER`; assert `ValueError` message contains `"LLM_PROVIDER"`
- [x] `test_valid_providers_pass` — parametrize over `{anthropic, openai, gemini, ollama}`; each with appropriate key set; assert no exception raised
- [x] `test_invalid_provider_raises` — set `LLM_PROVIDER=cohere`; assert `ValueError` message contains `"cohere"` and lists allowed values
- [x] `test_gemini_reads_gemini_api_key` — set `LLM_PROVIDER=gemini`, `GEMINI_API_KEY=abc123` (no `LLM_API_KEY`); assert `config.llm_api_key == "abc123"`
- [x] `test_gemini_missing_gemini_api_key_raises` — set `LLM_PROVIDER=gemini`, unset `GEMINI_API_KEY`; assert `ValueError` message contains `"GEMINI_API_KEY"`
- [x] `test_ollama_no_api_key_required` — set `LLM_PROVIDER=ollama`, unset `LLM_API_KEY`; assert `config.llm_api_key is None`
- [x] `test_non_ollama_missing_llm_api_key_raises` — set `LLM_PROVIDER=anthropic`, unset `LLM_API_KEY`; assert `ValueError` message contains `"LLM_API_KEY"`
- [x] `test_max_result_rows_defaults_to_10000` — unset `MAX_RESULT_ROWS`; assert `config.max_result_rows == 10000` and `isinstance(config.max_result_rows, int)`
- [x] `test_max_result_rows_cast_to_int` — set `MAX_RESULT_ROWS=500`; assert `config.max_result_rows == 500` (type `int`)
- [x] `test_max_result_rows_non_numeric_raises` — set `MAX_RESULT_ROWS=lots`; assert `ValueError` message contains `"MAX_RESULT_ROWS"`
- [x] `test_log_level_defaults_to_info` — unset `LOG_LEVEL`; assert `config.log_level == "INFO"`
- [x] `test_log_file_defaults_to_none` — unset `LOG_FILE`; assert `config.log_file is None`
- [x] `test_llm_model_defaults_to_none` — unset `LLM_MODEL`; assert `config.llm_model is None`
- [x] `test_no_streamlit_import` — read `config/env_config.py` as text; assert `"streamlit"` not in contents
- [x] `test_no_provider_sdk_import` — read `config/env_config.py` as text; assert none of `"anthropic"`, `"openai"`, `"google"`, `"ollama"` appear in imports

> **Checkpoint:**
> ```bash
> uv run ruff format .
> uv run ruff check .
> uv run pytest tests/config/test_env_config.py -v
> ```
> Expected: 18 tests green, 0 lint errors

---

## Final Quality Gate (before commit)

```bash
uv run ruff format . && uv run ruff check . && uv run pytest
```

All green → ready for `/pr`.
