# Implementation Plan — NLA-016: `services/nl_to_sql.py`

## Context

Branch: `feature/services/Issue-8-NL-to-SQL`  
`services/__init__.py` and `tests/services/__init__.py` exist (created in NLA-014).  
`services/exceptions.py` exists with `NLQueryError` (NLA-014).  
`config/llm_config.py` exists with `LLMClient` (NLA-006).  
`starter.py` (NLA-011) will set `schema["dialect"]` — this ticket defines that contract.

---

## Files to Create

| Path | Action | Notes |
|---|---|---|
| `services/nl_to_sql.py` | Create | Main implementation |
| `tests/services/test_nl_to_sql.py` | Create | 11 tests covering all spec scenarios |

No files modified. No files deleted.

---

## Architecture Decisions

### Dialect passed via `schema["dialect"]` — no signature change

`generate(question, schema, llm_client)` is the published API contract (AGENTS.md). Rather than adding a fourth `dialect` parameter, `starter.py` includes `"dialect": engine.dialect.name` in the `db_schema` dict it stores to `st.session_state`. `generate` reads `schema.get("dialect", "SQL")` — graceful fallback if the key is absent. This keeps the API contract stable and makes `starter.py` the single writer of the schema dict.

### Schema serialized as CREATE TABLE DDL

Preferred over JSON because LLMs trained on SQL corpora respond better to DDL-style schema than to JSON object notation. Format: `CREATE TABLE {name} ({col} {type}, …);` — one statement per table, joined by newlines.

### Module-level `_SYSTEM_PROMPT_TEMPLATE`

```python
_SYSTEM_PROMPT_TEMPLATE = """\
You are a SQL expert. Generate a {dialect}-compatible SQL SELECT query for the schema below.

{schema_ddl}

Rules:
- Return a SELECT statement only.
- Do NOT use INSERT, UPDATE, DELETE, DROP, ALTER, or TRUNCATE.
- Return only the SQL — no explanation, no markdown fences, no comments.\
"""
```

Built into a final `system` string each call via `.format(dialect=…, schema_ddl=…)`. Passed as the `system` argument to `LLMClient.complete(system, user)`.

### Fence stripping with regex

```python
import re

_FENCE_RE = re.compile(r"```(?:sql)?\s*([\s\S]*?)```", re.IGNORECASE)

def _strip_fences(text: str) -> str:
    match = _FENCE_RE.search(text)
    return match.group(1).strip() if match else text.strip()
```

Handles ` ```sql `, ` ```SQL `, and bare ` ``` ` delimiters. Falls back to the full stripped string if no fences are found.

### Empty response check before sqlglot

```python
if not cleaned.strip():
    raise NLQueryError("LLM returned an empty response")
```

Runs after fence stripping. Avoids misleading `ParseError` from sqlglot on empty input.

### sqlglot validation — parse + SELECT assert

```python
import sqlglot

try:
    parsed = sqlglot.parse_one(cleaned)
except sqlglot.errors.ParseError as exc:
    raise NLQueryError(f"LLM response is not valid SQL: {exc}") from exc

if not isinstance(parsed, sqlglot.exp.Select):
    raise NLQueryError(
        f"LLM returned a non-SELECT statement: {type(parsed).__name__}"
    )
```

Defence-in-depth: `sql_executor.py` re-validates via its own AST check, but catching here gives a clearer `NLQueryError` message before the string reaches the executor layer.

### Exception chaining for LLM API failures

```python
try:
    raw = llm_client.complete(system, question)
except Exception as exc:
    raise NLQueryError(f"LLM API call failed: {exc}") from exc
```

`raise … from exc` sets `__cause__`, so the logger in `app.py` can call `logging.exception(...)` and see the full original traceback.

---

## Implementation — `services/nl_to_sql.py`

### Imports (complete list)

```python
from __future__ import annotations

import re

import sqlglot

from config.llm_config import LLMClient
from services.exceptions import NLQueryError
```

No `sqlalchemy`, no provider SDK, no `streamlit`.

### Internal helpers

```python
_FENCE_RE = re.compile(r"```(?:sql)?\s*([\s\S]*?)```", re.IGNORECASE)

_SYSTEM_PROMPT_TEMPLATE = "..."  # see above

def _strip_fences(text: str) -> str: ...

def _schema_to_ddl(schema: dict) -> str:
    lines = []
    for table, columns in schema.get("tables", {}).items():
        col_defs = ", ".join(f"{c['name']} {c['type']}" for c in columns)
        lines.append(f"CREATE TABLE {table} ({col_defs});")
    return "\n".join(lines)
```

### `generate()` — step-by-step

```
1. dialect = schema.get("dialect", "SQL")
2. schema_ddl = _schema_to_ddl(schema)
3. system = _SYSTEM_PROMPT_TEMPLATE.format(dialect=dialect, schema_ddl=schema_ddl)
4. try: raw = llm_client.complete(system, question)
   except Exception as exc: raise NLQueryError(…) from exc
5. cleaned = _strip_fences(raw)
6. if not cleaned.strip(): raise NLQueryError("LLM returned empty response")
7. try: parsed = sqlglot.parse_one(cleaned)
   except sqlglot.errors.ParseError as exc: raise NLQueryError(…) from exc
8. if not isinstance(parsed, sqlglot.exp.Select): raise NLQueryError(…)
9. return cleaned
```

---

## Test Implementation — `tests/services/test_nl_to_sql.py`

### Mock strategy

```python
from unittest.mock import MagicMock
from config.llm_config import LLMClient

def make_llm_client(return_value: str = "SELECT 1") -> LLMClient:
    mock = MagicMock(spec=LLMClient)
    mock.complete.return_value = return_value
    return mock
```

### Test cases

| Test | Mock returns | Asserts |
|---|---|---|
| `test_valid_question_returns_clean_sql` | `"SELECT region FROM orders"` | return value equals SQL string |
| `test_markdown_fences_stripped` | ` ```sql\nSELECT * FROM orders\n``` ` | return value is `"SELECT * FROM orders"` |
| `test_schema_tables_in_system_prompt` | `"SELECT 1"` | `complete` called with system containing `"CREATE TABLE orders"` |
| `test_dialect_in_system_prompt` | `"SELECT 1"` | `complete` called with system containing `"sqlite"` |
| `test_empty_response_raises_nl_query_error` | `""` | `NLQueryError` raised |
| `test_whitespace_response_raises_nl_query_error` | `"   "` | `NLQueryError` raised |
| `test_unparseable_response_raises_nl_query_error` | `"not SQL at all"` | `NLQueryError` raised |
| `test_non_select_raises_nl_query_error` | `"INSERT INTO t VALUES (1)"` | `NLQueryError` raised |
| `test_llm_exception_raises_nl_query_error_with_cause` | raises `RuntimeError("timeout")` | `NLQueryError` raised; `exc.__cause__` is `RuntimeError` |
| `test_no_sqlalchemy_import` | — | source scan: no `sqlalchemy` in import lines |
| `test_no_provider_sdk_import` | — | source scan: none of `anthropic`, `openai`, `google.genai`, `requests` |

---

## Quality Gate Commands

```bash
uv run ruff format services/nl_to_sql.py tests/services/test_nl_to_sql.py
uv run ruff check services/nl_to_sql.py tests/services/test_nl_to_sql.py
uv run pytest tests/services/test_nl_to_sql.py -v
```

Full suite before commit:

```bash
uv run ruff format . && uv run ruff check . && uv run pytest
```

---

## Out of Scope for This Ticket

- SQL validation via keyword blocklist — `sql_executor.py` (NLA-020)
- SQL execution — `sql_executor.py` (NLA-020)
- `starter.py` bootstrap sequence — NLA-011 (this ticket defines the `schema` dict contract; NLA-011 implements it)
- Multi-turn / conversation history in prompt — not in spec
- Prompt caching or token optimisation — not in spec
