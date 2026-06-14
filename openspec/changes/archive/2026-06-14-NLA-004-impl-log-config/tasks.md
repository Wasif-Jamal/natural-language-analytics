# Tasks — NLA-004: `config/log_config.py`

Branch: `feature/config/NLA-004-impl-log-config`

---

## Phase 1 — Foundation

No new package scaffolding needed — `config/` and `tests/config/` already exist from NLA-003.

- [x] Verify `config/__init__.py` and `tests/config/__init__.py` are present (no action if they exist)

> **Checkpoint:**
> ```bash
> uv run ruff check config/ tests/
> ```
> Expected: 0 errors

---

## Phase 2 — Core Implementation

- [x] Create `config/log_config.py` — add imports: `from __future__ import annotations`, `import logging`, `import sys`, `from config.env_config import AppConfig`
- [x] Define `setup_logging(config: AppConfig) -> None` — clear root logger handlers (`root_logger.handlers.clear()`), set level (`root_logger.setLevel(config.log_level)`), create shared `Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")`, add `StreamHandler(sys.stdout)` with formatter
- [x] Extend `setup_logging()` — add conditional `FileHandler(config.log_file)` with same formatter when `config.log_file is not None`

> **Checkpoint:**
> ```bash
> uv run ruff format config/log_config.py
> uv run ruff check config/log_config.py
> ```
> Expected: 0 format diffs, 0 lint errors

---

## Phase 3 — Integration

- [x] Verify imports in `config/log_config.py` — confirm only `logging`, `sys`, and `AppConfig` are imported; no `os`, `dotenv`, `streamlit`, or provider SDK

```bash
grep -n "^import\|^from" config/log_config.py
```

Expected output contains only: `from __future__`, `import logging`, `import sys`, `from config.env_config import AppConfig`

---

## Phase 4 — Tests

File: `tests/config/test_log_config.py`

- [x] Add `make_config()` helper — constructs `AppConfig` directly via dataclass constructor (no env vars, no `load_config()`)
- [x] Add `reset_root_logger` autouse fixture — clears root logger handlers and resets level to `WARNING` after each test
- [x] `test_returns_none` — assert `setup_logging(make_config())` returns `None`
- [x] `test_default_info_level` — `make_config(log_level="INFO")`; assert `logging.getLogger().level == logging.INFO`
- [x] `test_custom_debug_level` — `make_config(log_level="DEBUG")`; assert `logging.getLogger().level == logging.DEBUG`
- [x] `test_formatter_contains_required_fields` — assert all four of `%(asctime)s`, `%(levelname)s`, `%(name)s`, `%(message)s` appear in `handler.formatter._fmt` for each handler
- [x] `test_stream_handler_present` — `log_file=None`; assert at least one `logging.StreamHandler` in `root.handlers`
- [x] `test_exactly_one_handler_no_file` — `log_file=None`; assert `len(logging.getLogger().handlers) == 1`
- [x] `test_file_handler_added` — `log_file=str(tmp_path / "app.log")`; assert `len(root.handlers) == 2` and a `logging.FileHandler` is present
- [x] `test_no_file_handler_when_none` — `log_file=None`; assert no `logging.FileHandler` in `root.handlers`
- [x] `test_idempotent_no_duplicates` — call `setup_logging` twice; assert `len(root.handlers)` equals count from a single call
- [x] `test_no_env_var_access` — read `config/log_config.py` as text; assert none of `"os.getenv"`, `"os.environ"`, `"load_dotenv"` appear
- [x] `test_no_streamlit_import` — read import lines only; assert `"streamlit"` not in them

> **Checkpoint:**
> ```bash
> uv run ruff format .
> uv run ruff check .
> uv run pytest tests/config/test_log_config.py -v
> ```
> Expected: 13 tests green, 0 lint errors

---

## Final Quality Gate

```bash
uv run ruff format . && uv run ruff check . && uv run pytest
```

All green → ready for `/pr`.
