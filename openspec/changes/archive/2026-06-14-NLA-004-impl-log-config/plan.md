# Implementation Plan — NLA-004: `config/log_config.py`

## Context

Branch: `feature/config/NLA-004-impl-log-config`  
Only existing config module: `config/env_config.py` (merged via NLA-003).  
`AppConfig` is the established pattern for passing config into config-layer functions.

---

## Files to Create

| Path | Action | Notes |
|---|---|---|
| `config/log_config.py` | Create | Main implementation |
| `tests/config/test_log_config.py` | Create | 11 tests covering all spec scenarios |

No files modified. No files deleted.

---

## Architecture Decisions

### Signature: `setup_logging(config: AppConfig) -> None`

Mirrors the pattern established in NLA-003: config-layer functions receive a pre-resolved `AppConfig` rather than reading `os.getenv` themselves. This keeps env var logic in one place and makes unit tests trivial — pass a dataclasses-constructed `AppConfig` with the values you want to test.

### Clear handlers first — `root_logger.handlers.clear()`

Python's root logger is a module-level singleton. Without clearing, a second call (e.g. in a test suite that calls `setup_logging` multiple times) doubles the handlers, producing duplicate log lines. Clearing first costs nothing and makes behaviour deterministic.

### Explicit `StreamHandler(sys.stdout)` — always

Python's default `lastResort` handler writes to `sys.stderr` with no custom format. By adding an explicit `StreamHandler(sys.stdout)`, the structured format always applies and output goes to stdout — consistent with 12-factor app convention and easier to pipe/capture in tests.

### Single `Formatter` instance, shared by all handlers

Both the `StreamHandler` and optional `FileHandler` receive the same `Formatter` object. This guarantees format consistency whether log lines go to stdout, a file, or both.

### Format string: `%(asctime)s | %(levelname)s | %(name)s | %(message)s`

Matches SDS §4.4 `timestamp | level | module | message`. `%(name)s` resolves to the logger name (e.g. `services.nl_to_sql` for `logging.getLogger(__name__)`), giving precise module-level traceability. Timestamp uses Python's default `asctime` format — no `datefmt` override needed.

### Intra-config import: `from config.env_config import AppConfig`

`log_config.py` imports `AppConfig` from `env_config.py`. This is an intra-layer dependency within `config/` — permitted by the architecture (the rule is "config must not call services", not "config must not call config"). No circular import risk since `env_config.py` does not import from `log_config.py`.

---

## Implementation — `config/log_config.py`

### Imports (complete list)

```python
from __future__ import annotations

import logging
import sys

from config.env_config import AppConfig
```

No `os`, no `dotenv`, no `streamlit`, no provider SDK.

### `setup_logging()` implementation steps

```
1. root_logger = logging.getLogger()
2. root_logger.handlers.clear()                        # idempotency
3. root_logger.setLevel(config.log_level)
4. formatter = Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
5. stream_handler = StreamHandler(sys.stdout)
6. stream_handler.setFormatter(formatter)
7. root_logger.addHandler(stream_handler)
8. if config.log_file is not None:
       file_handler = FileHandler(config.log_file)
       file_handler.setFormatter(formatter)
       root_logger.addHandler(file_handler)
```

### Handler count invariants

| `config.log_file` | Expected handler count |
|---|---|
| `None` | 1 (`StreamHandler`) |
| `"/tmp/app.log"` | 2 (`StreamHandler` + `FileHandler`) |

---

## Test Implementation — `tests/config/test_log_config.py`

### Test helper — `make_config()`

```python
from config.env_config import AppConfig

def make_config(log_level="INFO", log_file=None):
    return AppConfig(
        database_url="sqlite:///test.db",
        llm_provider="anthropic",
        llm_api_key="test-key",
        llm_model=None,
        max_result_rows=10000,
        log_level=log_level,
        log_file=log_file,
    )
```

Constructs `AppConfig` directly via dataclass constructor — no env vars, no `load_config()` call.

### Teardown requirement

Each test that calls `setup_logging()` MUST reset the root logger afterward to avoid cross-test handler contamination. Use an `autouse` fixture:

```python
@pytest.fixture(autouse=True)
def reset_root_logger():
    yield
    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(logging.WARNING)
```

### Test cases (one per spec scenario)

| Test | Assertion |
|---|---|
| `test_returns_none` | `setup_logging(config)` returns `None` |
| `test_default_info_level` | `logging.getLogger().level == logging.INFO` |
| `test_custom_debug_level` | `logging.getLogger().level == logging.DEBUG` |
| `test_formatter_contains_required_fields` | All of `%(asctime)s`, `%(levelname)s`, `%(name)s`, `%(message)s` in handler's `formatter._fmt` |
| `test_stream_handler_present` | At least one `StreamHandler` in root logger handlers |
| `test_exactly_one_handler_no_file` | `len(root.handlers) == 1` when `log_file=None` |
| `test_file_handler_added` | `len(root.handlers) == 2` and a `FileHandler` present when `log_file` set (use `tmp_path`) |
| `test_no_file_handler_when_none` | No `FileHandler` in root logger handlers when `log_file=None` |
| `test_idempotent_no_duplicates` | Call twice → same `len(root.handlers)` as single call |
| `test_no_env_var_access` | Source text contains none of `os.getenv`, `os.environ`, `load_dotenv` |
| `test_no_streamlit_import` | Source import lines contain no `streamlit` |

---

## Quality Gate Commands

```bash
uv run ruff format config/log_config.py tests/config/test_log_config.py
uv run ruff check config/log_config.py tests/config/test_log_config.py
uv run pytest tests/config/test_log_config.py -v
```

Full suite before commit:

```bash
uv run ruff format . && uv run ruff check . && uv run pytest
```

---

## Out of Scope for This Ticket

- Per-module logger instances — callers do `logging.getLogger(__name__)` themselves
- Log level validation — Python's `logging.setLevel()` raises `ValueError` on invalid strings natively
- `db_config.py`, `llm_config.py` — NLA-005, NLA-006
- `starter.py` — NLA-011
