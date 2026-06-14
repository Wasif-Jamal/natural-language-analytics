# Implementation Plan — NLA-005: `config/db_config.py`

## Context

Branch: `feature/config/NLA-005-impl-db-config`  
Existing config modules: `config/env_config.py` (NLA-003), `config/log_config.py` (NLA-004).  
`AppConfig` is the established pattern: config-layer functions receive a pre-resolved `AppConfig` rather than calling `os.getenv` themselves.

---

## Files to Create

| Path | Action | Notes |
|---|---|---|
| `config/db_config.py` | Create | Main implementation |
| `tests/config/test_db_config.py` | Create | 8 tests covering all spec scenarios |

No files modified. No files deleted.

---

## Architecture Decisions

### Function name: `get_engine(config: AppConfig) -> Engine`

Mirrors the pattern from `setup_logging(config)` — a single public factory function that receives an already-resolved `AppConfig`. The name avoids shadowing SQLAlchemy's own `create_engine`, which is aliased internally as `_sa_create_engine`.

### `MAX_RESULT_ROWS` as a module-level variable set by `get_engine()`

The spec requires exposing `MAX_RESULT_ROWS` as a constant importable from `config.db_config`. Since its value comes from `config.max_result_rows` at runtime, `get_engine()` sets it via `global MAX_RESULT_ROWS`. The initial value (`10_000`) matches the `AppConfig` default, so callers that import before `get_engine()` is called still see a correct value for the default case.

**Downstream consumer note (NLA-020):** `sql_executor.py` MUST access `MAX_RESULT_ROWS` as `import config.db_config; config.db_config.MAX_RESULT_ROWS` — NOT `from config.db_config import MAX_RESULT_ROWS`. The `from … import` form binds to the value at import time; attribute access on the module always reads the current value after `get_engine()` has been called by `starter.py`.

### Connectivity probe: `SELECT 1` inside `with engine.connect()`

After `_sa_create_engine(url)`, the engine is lazy — no real connection is made until `.connect()` is called. The probe pattern:

```python
with engine.connect() as conn:
    conn.execute(text("SELECT 1"))
```

The `with` block ensures the connection is released regardless of outcome. `SELECT 1` is the canonical liveness check and works across SQLite, PostgreSQL, and MySQL without any schema dependency.

### Native SQLAlchemy exceptions propagate — no wrapping

- Malformed URL → `sqlalchemy.exc.ArgumentError` (raised at `_sa_create_engine` call)
- Unreachable host → `sqlalchemy.exc.OperationalError` (raised at `engine.connect()`)

`starter.py` (NLA-011) is responsible for catching these and rendering a fatal error in the UI. Wrapping them in `RuntimeError` or `ValueError` here would discard useful SQLAlchemy context.

### Intra-config import: `from config.env_config import AppConfig`

Same pattern as `log_config.py` — permitted intra-layer dependency. No circular risk since `env_config.py` does not import from `db_config.py`.

---

## Implementation — `config/db_config.py`

### Imports (complete list)

```python
from __future__ import annotations

from sqlalchemy import create_engine as _sa_create_engine, text
from sqlalchemy.engine import Engine

from config.env_config import AppConfig
```

No `os`, no `dotenv`, no `streamlit`, no provider SDK.

### Module-level constant

```python
MAX_RESULT_ROWS: int = 10_000
```

Initial value matches the `AppConfig` default. Updated by `get_engine()` at startup.

### `get_engine()` implementation steps

```
1. global MAX_RESULT_ROWS
2. MAX_RESULT_ROWS = config.max_result_rows
3. engine = _sa_create_engine(config.database_url)   # raises ArgumentError for malformed URL
4. with engine.connect() as conn:
5.     conn.execute(text("SELECT 1"))                 # raises OperationalError for unreachable host
6. return engine
```

### Invariants

| Input URL | `_sa_create_engine` | `engine.connect()` |
|---|---|---|
| `"sqlite:///:memory:"` | succeeds | succeeds |
| `"notavalidurl"` | raises `ArgumentError` | never reached |
| `"postgresql://…"` (unreachable) | succeeds | raises `OperationalError` |

---

## Test Implementation — `tests/config/test_db_config.py`

### Test helper — `make_config()`

```python
from config.env_config import AppConfig

def make_config(database_url: str = "sqlite:///:memory:", max_result_rows: int = 10_000) -> AppConfig:
    return AppConfig(
        database_url=database_url,
        llm_provider="anthropic",
        llm_api_key="test-key",
        llm_model=None,
        max_result_rows=max_result_rows,
        log_level="INFO",
        log_file=None,
    )
```

Constructs `AppConfig` directly — no env vars, no `load_config()` call. Uses `sqlite:///:memory:` as the default so connectivity tests have no I/O dependency.

### Test cases (one per spec scenario)

| Test | Method | Assertion |
|---|---|---|
| `test_valid_sqlite_url_returns_engine` | real call | result is `sqlalchemy.engine.Engine` |
| `test_connectivity_probe_succeeds_for_memory_sqlite` | real call | no exception raised |
| `test_get_engine_sets_max_result_rows` | real call with `max_result_rows=500` | `db_config.MAX_RESULT_ROWS == 500` after call |
| `test_max_result_rows_default_is_10000` | real call with default | `db_config.MAX_RESULT_ROWS == 10_000` |
| `test_unreachable_host_raises_operational_error` | monkeypatch | `OperationalError` propagates |
| `test_malformed_url_raises_argument_error` | real call `"notavalidurl"` | `ArgumentError` propagates |
| `test_no_streamlit_import` | source scan | no `streamlit` in import lines |
| `test_no_env_var_access` | source scan | no `os.getenv`, `os.environ`, `load_dotenv` in source |

### Mocking strategy for unreachable host

`_sa_create_engine` is aliased inside the module. Patch it via `monkeypatch.setattr` so the mock engine's `.connect()` raises `OperationalError`:

```python
from unittest.mock import MagicMock
from sqlalchemy.exc import OperationalError as SAOperationalError
import config.db_config

def test_unreachable_host_raises_operational_error(monkeypatch):
    mock_engine = MagicMock()
    mock_engine.connect.side_effect = SAOperationalError("unreachable", None, None)
    monkeypatch.setattr(config.db_config, "_sa_create_engine", lambda *a, **kw: mock_engine)
    with pytest.raises(SAOperationalError):
        get_engine(make_config(database_url="postgresql://user:pass@localhost/db"))
```

Patching via `monkeypatch.setattr(config.db_config, "_sa_create_engine", …)` patches the name in the module's namespace — the same reference `get_engine()` uses at call time.

### Source scan pattern (consistent with NLA-003/004)

```python
def test_no_streamlit_import():
    source = open("config/db_config.py").read()
    import_lines = "\n".join(
        line for line in source.splitlines() if line.startswith(("import ", "from "))
    )
    assert "streamlit" not in import_lines
```

Filters to import lines only — avoids false positives from string literals containing forbidden words.

---

## Quality Gate Commands

```bash
uv run ruff format config/db_config.py tests/config/test_db_config.py
uv run ruff check config/db_config.py tests/config/test_db_config.py
uv run pytest tests/config/test_db_config.py -v
```

Full suite before commit:

```bash
uv run ruff format . && uv run ruff check . && uv run pytest
```

---

## Out of Scope for This Ticket

- `check_same_thread=False` for SQLite — deferred to `starter.py` (NLA-011)
- Applying the `MAX_RESULT_ROWS` cap to query results — `sql_executor.py` (NLA-020)
- Connection pool tuning (`pool_size`, `pool_pre_ping`) — not in spec; defer to future if needed
- `llm_config.py` — NLA-006
- `starter.py` — NLA-011
