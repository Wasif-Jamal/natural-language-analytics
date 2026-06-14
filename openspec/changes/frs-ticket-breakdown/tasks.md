## 1. Project Bootstrap & Config Layer

- [x] NLA-001-create-pyproject-toml Create `pyproject.toml` with all dependencies: `streamlit`, `sqlalchemy`, `sqlglot`, `anthropic`, `openai`, `google-genai`, `pandas`, `matplotlib`, `seaborn`, `python-dotenv`; add `uv` dev tools (`ruff`, `pytest`)
- [x] NLA-002-create-env-example Create `.env.example` with all required and optional env vars documented (`DATABASE_URL`, `LLM_PROVIDER`, `LLM_API_KEY`, `LLM_MODEL`, `MAX_RESULT_ROWS`, `LOG_LEVEL`, `LOG_FILE`)
- [x] NLA-003-impl-env-config Implement `config/env_config.py` — load all env vars via `python-dotenv`, validate required vars (raising `ValueError` for missing), return a config object; implement optional `LLM_API_KEY` skip for `LLM_PROVIDER=ollama` — [specs/config-bootstrap/spec.md](specs/config-bootstrap/spec.md)
- [x] NLA-004-impl-log-config Implement `config/log_config.py` — configure root logger with format `timestamp | level | module | message`, support `LOG_LEVEL` override and optional `LOG_FILE` file handler — [specs/config-bootstrap/spec.md](specs/config-bootstrap/spec.md)
- [ ] NLA-005-impl-db-config Implement `config/db_config.py` — create SQLAlchemy `Engine` from `DATABASE_URL`; expose `MAX_RESULT_ROWS` as a constant; raise a descriptive error for invalid URLs or unreachable hosts — [specs/config-bootstrap/spec.md](specs/config-bootstrap/spec.md)
- [ ] NLA-006-impl-llm-client Implement `config/llm_config.py` — `LLMClient` class with `complete(system: str, user: str) -> str`; route to correct provider SDK (`anthropic`, `openai`, `google-genai`, Ollama REST); apply per-provider default models; raise `ValueError` for unsupported providers — [specs/config-bootstrap/spec.md](specs/config-bootstrap/spec.md)
- [ ] NLA-007-test-env-config Write tests `tests/config/test_env_config.py` — cover: all vars present, missing `DATABASE_URL`, missing `LLM_API_KEY` for non-Ollama, Ollama skips key check, `MAX_RESULT_ROWS` default — [specs/config-bootstrap/spec.md](specs/config-bootstrap/spec.md)
- [ ] NLA-008-test-db-config Write tests `tests/config/test_db_config.py` — cover: valid SQLite URL, invalid URL raises, `MAX_RESULT_ROWS` constant is `10000` by default — [specs/config-bootstrap/spec.md](specs/config-bootstrap/spec.md)
- [ ] NLA-009-test-llm-client Write tests `tests/config/test_llm_config.py` — mock provider SDKs; cover: correct default model per provider, `LLM_MODEL` override, unsupported provider raises, `complete()` returns string — [specs/config-bootstrap/spec.md](specs/config-bootstrap/spec.md)
- [ ] NLA-010-quality-gates-config Run quality gates: `uv run ruff format .` → `uv run ruff check .` → `uv run pytest tests/config/`

## 2. Application Bootstrap (starter.py)

- [ ] NLA-011-impl-starter-bootstrap Implement `starter.py` — call `env_config`, `log_config`, `db_config`, `llm_config` in sequence; introspect DB schema (table names, column names, types) via SQLAlchemy `inspect(engine)`; store `db_engine`, `llm_client`, `db_schema`, `query_history=[]` into `st.session_state`; guard with `if "db_engine" not in st.session_state` — [specs/config-bootstrap/spec.md](specs/config-bootstrap/spec.md)
- [ ] NLA-012-test-starter-bootstrap Write tests `tests/test_starter.py` — mock SQLAlchemy engine and `LLMClient`; cover: all session state keys populated, guard prevents re-run, schema dict is non-empty — [specs/config-bootstrap/spec.md](specs/config-bootstrap/spec.md)
- [ ] NLA-013-quality-gates-starter Run quality gates: `uv run ruff format .` → `uv run ruff check .` → `uv run pytest tests/test_starter.py`

## 3. Custom Exception Hierarchy

- [ ] NLA-014-create-exception-classes Create `services/exceptions.py` — define `NLQueryError`, `SQLValidationError`, `DBExecutionError`, `EmptyResultError`, `InsightError` as subclasses of `Exception` — [specs/error-handling/spec.md](specs/error-handling/spec.md)
- [ ] NLA-015-test-exception-classes Write `tests/services/test_exceptions.py` — assert each exception is raiseable and is a subclass of `Exception` — [specs/error-handling/spec.md](specs/error-handling/spec.md)

## 4. NL-to-SQL Service

- [ ] NLA-016-impl-nl-to-sql Implement `services/nl_to_sql.py` — `generate(question: str, schema: dict, llm_client: LLMClient) -> str`; inject schema into system prompt (SELECT-only instruction); call `llm_client.complete`; strip markdown fences; validate with `sqlglot`; raise `NLQueryError` on parse failure or LLM error — [specs/nl-to-sql/spec.md](specs/nl-to-sql/spec.md)
- [ ] NLA-017-test-nl-to-sql Write tests `tests/services/test_nl_to_sql.py` — mock `LLMClient`; cover: valid SQL returned, fences stripped, schema in system prompt, unparseable response raises `NLQueryError`, LLM exception raises `NLQueryError` — [specs/nl-to-sql/spec.md](specs/nl-to-sql/spec.md)
- [ ] NLA-018-nl-to-sql-import-guard Assert `services/nl_to_sql.py` has no import of `sqlalchemy`, `anthropic`, `openai`, or `google.genai` (import guard test) — [specs/nl-to-sql/spec.md](specs/nl-to-sql/spec.md)
- [ ] NLA-019-quality-gates-nl-to-sql Run quality gates: `uv run ruff format .` → `uv run ruff check .` → `uv run pytest tests/services/test_nl_to_sql.py`

## 5. SQL Executor Service

- [ ] NLA-020-impl-sql-executor Implement `services/sql_executor.py` — `run(sql: str, engine: Engine) -> (list[str], list[tuple])`; layer 1: whole-word regex for `INSERT|UPDATE|DELETE|DROP|ALTER|TRUNCATE` → raise `SQLValidationError`; layer 2: `sqlglot` AST check root is `SELECT` → raise `SQLValidationError`; execute via `text()`; cap at `MAX_RESULT_ROWS`; raise `EmptyResultError` for zero rows; raise `DBExecutionError` for execution failures — [specs/sql-execution/spec.md](specs/sql-execution/spec.md)
- [ ] NLA-021-test-sql-executor Write tests `tests/services/test_sql_executor.py` using real `sqlglot` (do NOT mock parser); cover: valid SELECT passes, `INSERT` blocked (layer 1), `UPDATE` blocked, `DELETE` blocked, `DROP` blocked, CTE-wrapped write blocked (layer 2), non-SQL blocked, successful execution returns columns+rows, result capped at `MAX_RESULT_ROWS`, empty result raises `EmptyResultError`, DB error raises `DBExecutionError` — [specs/sql-execution/spec.md](specs/sql-execution/spec.md)
- [ ] NLA-022-sql-executor-import-guard Assert `services/sql_executor.py` has no import of `LLMClient` or provider SDK — [specs/sql-execution/spec.md](specs/sql-execution/spec.md)
- [ ] NLA-023-quality-gates-sql-executor Run quality gates: `uv run ruff format .` → `uv run ruff check .` → `uv run pytest tests/services/test_sql_executor.py`

## 6. Chart Engine Service

- [ ] NLA-024-impl-chart-engine Implement `services/chart_engine.py` — `render(columns: list[str], rows: list[tuple], question: str) -> ChartResult`; implement all 6 shape-detection branches in order (1×1 text, time+measure line, two numeric scatter, cat+measure ≈100% pie, cat+measure bar, fallback table); return typed `ChartResult` dict (`{"type": "figure"|"text"|"table", ...}`); use Matplotlib for rendering; no file I/O — [specs/result-presentation/spec.md](specs/result-presentation/spec.md)
- [ ] NLA-025-test-chart-engine Write tests `tests/services/test_chart_engine.py` — cover all 6 shape branches: 1×1 → text, time+measure → figure (line), two numeric → figure (scatter), cat+measure ≈100% → figure (pie), cat+measure → figure (bar), ambiguous → table; assert correct `type` key in all cases — [specs/result-presentation/spec.md](specs/result-presentation/spec.md)
- [ ] NLA-026-chart-engine-import-guard Assert `services/chart_engine.py` has no import of `sqlalchemy` or `LLMClient` — [specs/result-presentation/spec.md](specs/result-presentation/spec.md)
- [ ] NLA-027-quality-gates-chart-engine Run quality gates: `uv run ruff format .` → `uv run ruff check .` → `uv run pytest tests/services/test_chart_engine.py`

## 7. Insight Engine Service

- [ ] NLA-028-impl-insight-engine Implement `services/insight_engine.py` — `generate(question: str, columns: list[str], rows: list[tuple], llm_client: LLMClient) -> dict`; build result summary from top 10 rows + numeric aggregates (min, max, sum, mean); call `llm_client.complete` with structured JSON prompt; parse response into `{"insights": [...], "suggested_questions": [...]}`; raise `InsightError` on JSON parse failure or LLM error — [specs/insights-and-followups/spec.md](specs/insights-and-followups/spec.md)
- [ ] NLA-029-test-insight-engine Write tests `tests/services/test_insight_engine.py` — mock `LLMClient`; cover: valid JSON returns dict with correct keys, only top 10 rows passed, aggregates included for numeric columns, unparseable response raises `InsightError`, LLM error raises `InsightError` — [specs/insights-and-followups/spec.md](specs/insights-and-followups/spec.md)
- [ ] NLA-030-insight-engine-import-guard Assert `services/insight_engine.py` has no import of `sqlalchemy` or provider SDK — [specs/insights-and-followups/spec.md](specs/insights-and-followups/spec.md)
- [ ] NLA-031-quality-gates-insight-engine Run quality gates: `uv run ruff format .` → `uv run ruff check .` → `uv run pytest tests/services/test_insight_engine.py`

## 8. Query History Service

- [ ] NLA-032-impl-query-history Implement `services/history.py` — `append(question: str, sql: str)` adds `{question, sql, timestamp}` to `st.session_state["query_history"]`; `get_all()` returns list reversed; `clear()` resets to `[]` — [specs/query-history/spec.md](specs/query-history/spec.md)
- [ ] NLA-033-test-query-history Write tests `tests/services/test_history.py` — mock `st.session_state`; cover: append adds entry, get_all returns reversed order, clear resets list, empty on init — [specs/query-history/spec.md](specs/query-history/spec.md)
- [ ] NLA-034-quality-gates-history Run quality gates: `uv run ruff format .` → `uv run ruff check .` → `uv run pytest tests/services/test_history.py`

## 9. Main UI (app.py)

- [ ] NLA-035-impl-app-pipeline Implement `app.py` — call `starter.py` at top; render question input (`st.text_area`) + Execute button; on submit: run pipeline (`nl_to_sql` → `sql_executor` → `chart_engine` → `insight_engine` → `history.append`); display generated SQL in `st.expander` with `st.code(..., language="sql")` — [specs/nl-query-input/spec.md](specs/nl-query-input/spec.md), [specs/nl-to-sql/spec.md](specs/nl-to-sql/spec.md)
- [ ] NLA-036-render-chart-result Render `ChartResult` by switching on `type`: `"figure"` → `st.pyplot` + PNG download button; `"text"` → plain-language answer panel; `"table"` → no chart — [specs/result-presentation/spec.md](specs/result-presentation/spec.md)
- [ ] NLA-037-render-insights-followups Render insights panel (2–4 bullets from `insight_engine`); render 3 follow-up question `st.button` elements — clicking re-submits as new query — [specs/insights-and-followups/spec.md](specs/insights-and-followups/spec.md)
- [ ] NLA-038-render-results-csv-export Render results table via `st.dataframe` with CSV download button (`st.download_button`, in-memory via `pandas.to_csv()`); hide when result is empty — [specs/data-export/spec.md](specs/data-export/spec.md)
- [ ] NLA-039-render-query-history Render query history in `st.expander` — reverse-chronological, each entry shows question + timestamp + Re-run button — [specs/query-history/spec.md](specs/query-history/spec.md)
- [ ] NLA-040-impl-error-handling Implement catch-all error handling in `app.py`: `NLQueryError` → `"Unable to identify requested entities."`, `SQLValidationError` → `"Generated query could not be validated."`, `DBExecutionError` → `"Unable to retrieve data at this time."`, `EmptyResultError` → `"No data found for the requested query."`, `InsightError` → silent skip; LLM unavailable → `"Unable to process your question at this time. Please try again."`; log all at `ERROR` level — [specs/error-handling/spec.md](specs/error-handling/spec.md)
- [ ] NLA-041-app-import-guard Assert `app.py` has no direct import of `anthropic`, `openai`, `google.genai`, `sqlalchemy`, or `sqlglot` — [specs/nl-query-input/spec.md](specs/nl-query-input/spec.md)
- [ ] NLA-042-quality-gates-app Run full quality gates: `uv run ruff format .` → `uv run ruff check .` → `uv run pytest`

## 10. Final Integration Verification

- [ ] NLA-043-full-test-suite Run complete test suite: `uv run pytest` — all tests green, 0 lint errors
- [ ] NLA-044-verify-exception-coverage Verify all 5 exception types have test coverage — [specs/error-handling/spec.md](specs/error-handling/spec.md)
- [ ] NLA-045-verify-chart-coverage Verify all 6 chart shape branches have test coverage — [specs/result-presentation/spec.md](specs/result-presentation/spec.md)
- [ ] NLA-046-security-credential-check Confirm no `.env`, credentials, or API keys are staged: `git status`
- [ ] NLA-047-create-test-conftest Create `tests/conftest.py` with shared fixtures (mock `LLMClient`, in-memory SQLite engine) if not already done during earlier phases
