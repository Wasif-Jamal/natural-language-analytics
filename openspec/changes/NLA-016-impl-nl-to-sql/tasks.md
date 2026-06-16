# Tasks — NLA-016: `services/nl_to_sql.py`

Branch: `feature/services/NLA-016-impl-nl-to-sql`

---

## Phase 1 — Foundation

- [x] Verify `services/__init__.py`, `tests/services/__init__.py`, and `services/exceptions.py` exist (created in NLA-014 — no action if present)

> **Checkpoint:**
> ```bash
> uv run ruff check services/ tests/services/
> ```
> Expected: 0 errors

---

## Phase 2 — Core Implementation

File: `services/nl_to_sql.py`

- [x] Add imports: `from __future__ import annotations`, `import re`, `import sqlglot`, `from config.llm_config import LLMClient`, `from services.exceptions import NLQueryError`
- [x] Define `_FENCE_RE = re.compile(r"```(?:sql)?\s*([\s\S]*?)```", re.IGNORECASE)` at module level
- [x] Define `_SYSTEM_PROMPT_TEMPLATE` as a module-level string constant — include `{dialect}` and `{schema_ddl}` placeholders; instruct SELECT-only, no fences, no explanation
- [x] Implement `_strip_fences(text: str) -> str` — use `_FENCE_RE.search`; return `match.group(1).strip()` if match found, else `text.strip()`
- [x] Implement `_schema_to_ddl(schema: dict) -> str` — iterate `schema.get("tables", {}).items()`; build `CREATE TABLE {name} ({col} {type}, …);` per table; join with `"\n"`
- [x] Implement `generate(question: str, schema: dict, llm_client: LLMClient) -> str`:
  - [x] `dialect = schema.get("dialect", "SQL")`
  - [x] `schema_ddl = _schema_to_ddl(schema)`
  - [x] `system = _SYSTEM_PROMPT_TEMPLATE.format(dialect=dialect, schema_ddl=schema_ddl)`
  - [x] `try: raw = llm_client.complete(system, question)` / `except Exception as exc: raise NLQueryError(…) from exc`
  - [x] `cleaned = _strip_fences(raw)`
  - [x] `if not cleaned.strip(): raise NLQueryError("LLM returned an empty response")`
  - [x] `try: parsed = sqlglot.parse_one(cleaned)` / `except sqlglot.errors.ParseError as exc: raise NLQueryError(…) from exc`
  - [x] `if not isinstance(parsed, sqlglot.exp.Select): raise NLQueryError(…)`
  - [x] `return cleaned`

> **Checkpoint:**
> ```bash
> uv run ruff format services/nl_to_sql.py
> uv run ruff check services/nl_to_sql.py
> ```
> Expected: 0 format diffs, 0 lint errors

---

## Phase 3 — Tests

File: `tests/services/test_nl_to_sql.py`

- [x] Add imports: `from unittest.mock import MagicMock`, `import pytest`, `from config.llm_config import LLMClient`, `from services.exceptions import NLQueryError`, `from services.nl_to_sql import generate`
- [x] Define `make_llm_client(return_value)` helper — `MagicMock(spec=LLMClient)` with `mock.complete.return_value = return_value`
- [x] Define `sample_schema` fixture — `{"dialect": "sqlite", "tables": {"orders": [{"name": "id", "type": "INTEGER"}, {"name": "region", "type": "TEXT"}]}}`
- [x] `test_valid_question_returns_clean_sql` — mock returns `"SELECT id FROM orders"`; assert return value equals that string
- [x] `test_markdown_fences_stripped` — mock returns ` ```sql\nSELECT * FROM orders\n``` `; assert return is `"SELECT * FROM orders"`
- [x] `test_schema_tables_in_system_prompt` — call `generate`; assert `"CREATE TABLE orders"` in the `system` arg passed to `mock.complete`
- [x] `test_dialect_in_system_prompt` — schema has `"dialect": "sqlite"`; assert `"sqlite"` in `system` arg (case-insensitive)
- [x] `test_empty_response_raises_nl_query_error` — mock returns `""`; assert `pytest.raises(NLQueryError)`
- [x] `test_whitespace_response_raises_nl_query_error` — mock returns `"   "`; assert `pytest.raises(NLQueryError)`
- [x] `test_unparseable_response_raises_nl_query_error` — mock returns `"not SQL at all!!!"`; assert `pytest.raises(NLQueryError)`
- [x] `test_non_select_raises_nl_query_error` — mock returns `"INSERT INTO orders VALUES (1, 'a')"`; assert `pytest.raises(NLQueryError)`
- [x] `test_llm_exception_raises_nl_query_error_with_cause` — `mock.complete.side_effect = RuntimeError("timeout")`; catch `NLQueryError`; assert `exc.__cause__` is instance of `RuntimeError`
- [x] `test_no_sqlalchemy_import` — read `services/nl_to_sql.py`; filter import lines; assert `"sqlalchemy"` not present
- [x] `test_no_provider_sdk_import` — read `services/nl_to_sql.py`; filter import lines; assert none of `"anthropic"`, `"openai"`, `"google.genai"`, `"requests"` present

> **Checkpoint:**
> ```bash
> uv run ruff format .
> uv run ruff check .
> uv run pytest tests/services/test_nl_to_sql.py -v
> ```
> Expected: 11 tests green, 0 lint errors

---

## Final Quality Gate

```bash
uv run ruff format . && uv run ruff check . && uv run pytest
```

All green → ready for `/pr`.
