# Tasks — NLA-005: `config/db_config.py`

Branch: `feature/config/NLA-005-impl-db-config`

---

## Phase 1 — Foundation

No new package scaffolding needed — `config/` and `tests/config/` already exist from NLA-003/004.

- [x] Verify `config/__init__.py` and `tests/config/__init__.py` are present (no action if they exist)

> **Checkpoint:**
> ```bash
> uv run ruff check config/ tests/
> ```
> Expected: 0 errors

---

## Phase 2 — Core Implementation

- [x] Create `config/db_config.py` — add imports: `from __future__ import annotations`, `from sqlalchemy import create_engine as _sa_create_engine, text`, `from sqlalchemy.engine import Engine`, `from config.env_config import AppConfig`
- [x] Add module-level constant `MAX_RESULT_ROWS: int = 10_000`
- [x] Implement `get_engine(config: AppConfig) -> Engine` — declare `global MAX_RESULT_ROWS`, set `MAX_RESULT_ROWS = config.max_result_rows`, call `_sa_create_engine(config.database_url)` (raises `ArgumentError` for malformed URL)
- [x] Add connectivity probe inside `get_engine()` — `with engine.connect() as conn: conn.execute(text("SELECT 1"))` (raises `OperationalError` for unreachable host)
- [x] Return `engine` from `get_engine()`

> **Checkpoint:**
> ```bash
> uv run ruff format config/db_config.py
> uv run ruff check config/db_config.py
> ```
> Expected: 0 format diffs, 0 lint errors

---

## Phase 3 — Integration

- [x] Verify imports in `config/db_config.py` — confirm only `sqlalchemy`, `sqlalchemy.engine`, and `AppConfig` are imported; no `os`, `dotenv`, `streamlit`, or provider SDK

```bash
grep -n "^import\|^from" config/db_config.py
```

Expected output contains only: `from __future__`, `from sqlalchemy import …`, `from sqlalchemy.engine import Engine`, `from config.env_config import AppConfig`

---

## Phase 4 — Tests

File: `tests/config/test_db_config.py`

- [x] Add imports: `from unittest.mock import MagicMock`, `from sqlalchemy.exc import ArgumentError as SAArgumentError, OperationalError as SAOperationalError`, `from sqlalchemy.engine import Engine`, `import config.db_config`, `from config.db_config import get_engine`
- [x] Add `make_config()` helper — constructs `AppConfig` directly via dataclass constructor; default `database_url="sqlite:///:memory:"`, `max_result_rows=10_000`
- [x] `test_valid_sqlite_url_returns_engine` — call `get_engine(make_config())`; assert result is instance of `Engine`
- [x] `test_connectivity_probe_succeeds_for_memory_sqlite` — call `get_engine(make_config())`; assert no exception raised
- [x] `test_get_engine_sets_max_result_rows` — call `get_engine(make_config(max_result_rows=500))`; assert `config.db_config.MAX_RESULT_ROWS == 500`
- [x] `test_max_result_rows_default_is_10000` — call `get_engine(make_config())`; assert `config.db_config.MAX_RESULT_ROWS == 10_000`
- [x] `test_unreachable_host_raises_operational_error` — `monkeypatch.setattr(config.db_config, "_sa_create_engine", lambda *a, **kw: mock_engine)` where `mock_engine.connect.side_effect = SAOperationalError("unreachable", None, None)`; assert `pytest.raises(SAOperationalError)`
- [x] `test_malformed_url_raises_argument_error` — call `get_engine(make_config(database_url="notavalidurl"))`; assert `pytest.raises(SAArgumentError)`
- [x] `test_no_streamlit_import` — read `config/db_config.py` source; filter to import lines (`startswith(("import ", "from "))`); assert `"streamlit"` not in filtered lines
- [x] `test_no_env_var_access` — read `config/db_config.py` as text; assert none of `"os.getenv"`, `"os.environ"`, `"load_dotenv"` appear anywhere in source

> **Checkpoint:**
> ```bash
> uv run ruff format .
> uv run ruff check .
> uv run pytest tests/config/test_db_config.py -v
> ```
> Expected: 10 tests green, 0 lint errors

---

## Final Quality Gate

```bash
uv run ruff format . && uv run ruff check . && uv run pytest
```

All green → ready for `/pr`.
