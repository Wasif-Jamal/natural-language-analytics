# Project Context — Natural Language Analytics Dashboard

## Project

A Streamlit application that lets business users query structured SQL data in plain English and receive results as charts, plain-language answers, actionable insights, and suggested follow-up questions. Users need no SQL knowledge; the system generates SQL via an LLM, validates it is read-only, executes it, and renders the output through a layered module pipeline.

---

## Tech Stack

| Component | Technology |
|---|---|
| Language | Python 3.11+ |
| UI framework | Streamlit |
| Charts | Matplotlib + Seaborn |
| Database ORM | SQLAlchemy |
| SQL parsing/validation | sqlglot |
| LLM — Anthropic | `anthropic` Python SDK |
| LLM — OpenAI | `openai` Python SDK |
| LLM — Google Gemini | `google-genai` Python SDK |
| LLM — Ollama | Ollama REST API (HTTP) |
| Data manipulation | pandas |
| Env var management | `python-dotenv` |
| Package manager | `uv` |

---

## Architecture

Strict one-way dependency: `app.py → services/*.py → config/*.py`. No layer calls upward.

- **`starter.py`** bootstraps once at app start. All shared resources (`db_engine`, `llm_client`, `db_schema`) go into `st.session_state` and are never re-initialised inside a service.
- **`LLMClient`** (in `config/llm_config.py`) is the only place that imports provider SDKs. Services call `LLMClient.complete(system, user) -> str` only.
- **`chart_engine.py`** returns a typed `ChartResult` dict: `{"type": "figure"|"text"|"table", ...}`. `app.py` switches on `type` to render — no `isinstance` checks on raw data.
- **`app.py`** is the sole exception catch boundary — catches all five typed errors plus LLM unavailable.

---

## Module Contracts

| Service | Signature | Output |
|---|---|---|
| `nl_to_sql.generate` | `(question: str, schema: dict, llm_client: LLMClient)` | `str` (clean SQL) |
| `sql_executor.run` | `(sql: str, engine: Engine)` | `(list[str], list[tuple])` |
| `chart_engine.render` | `(columns: list, rows: list, question: str)` | `ChartResult` dict |
| `insight_engine.generate` | `(question: str, columns: list, rows: list, llm_client: LLMClient)` | `{"insights": [...], "suggested_questions": [...]}` |
| `history.append / get_all / clear` | session state side-effects | — |

---

## Custom Exceptions

| Exception | Raised By | User-Facing Message |
|---|---|---|
| `NLQueryError` | `nl_to_sql.py` | `Unable to identify requested entities.` |
| `SQLValidationError` | `sql_executor.py` | `Generated query could not be validated.` |
| `DBExecutionError` | `sql_executor.py` | `Unable to retrieve data at this time.` |
| `EmptyResultError` | `sql_executor.py` | `No data found for the requested query.` |
| `InsightError` | `insight_engine.py` | Insights panel silently skipped (non-fatal) |

All are caught in `app.py` only. Error strings are exact — never substitute.

---

## Team Conventions

- **Naming:** `snake_case` for all Python identifiers. Module names match the SDS file list exactly.
- **Commits:** `<type>(<scope>): <description> [AB#ticket]` — types: `feat`, `fix`, `refactor`, `test`, `docs`, `chore`. Include `AB#ticket` when work traces to a ticket.
- **Branches:** `feature/{domain}/AB-{ticket}-{short-name}` / `fix/{domain}/AB-{ticket}-{short-name}`
- **LLM responses:** Always strip markdown fences; parse/validate before use. Never `eval` or `exec` LLM output.
- **Result rows:** Always apply `MAX_RESULT_ROWS` cap (default 10 000) before returning query results.

---

## Quality Standards

- **Gates (run in order before every commit):** `uv run ruff format .` → `uv run ruff check .` (0 errors) → `uv run pytest` (all green)
- **Tests:** pytest in `tests/` mirroring `services/` and `config/`. Mock `LLMClient` and `Engine` at boundaries. Do NOT mock `sqlglot` parser.
- **Coverage required:** all five exception types, all six chart shape-detection branches in `chart_engine.py`.
- **Never commit:** failing tests, lint errors, or staged `.env`/credentials.

---

## Constraints & Out of Scope

- **Read-only SQL only.** `INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, `TRUNCATE` are blocked at two layers (keyword block list + sqlglot AST check) and must never reach the database.
- **No authentication.** App assumes a trusted user environment; do not add login flows, session tokens, or role checks.
- **Out of scope:** statistical forecasting, ML recommendations, multi-database federation, RBAC, dashboard sharing.
- **No provider SDK calls outside `LLMClient`.** Provider logic must not leak into `nl_to_sql.py`, `insight_engine.py`, or `app.py`.
- **No full result sets to the LLM.** `insight_engine` passes only top-10 rows + aggregates.
