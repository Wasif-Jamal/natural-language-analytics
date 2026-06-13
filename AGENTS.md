# AGENTS.md — Natural Language Analytics Dashboard

Single source of truth for all AI tools on this team.

---

## 1. Project Overview

A Streamlit application that lets business users query structured SQL data in plain English and receive results as charts, plain-language answers, actionable insights, and suggested follow-up questions. Users need no SQL knowledge. The system generates SQL via an LLM, validates it is read-only, executes it, and renders the output through a layered module pipeline.

---

## 2. Repository Structure

```
natural-language-analytics/
├── app.py                    # Streamlit entry point; renders all UI components
├── starter.py                # Bootstrap — runs once at startup, loads session_state
├── services/
│   ├── nl_to_sql.py          # NL → SQL via LLM (LLMClient.complete)
│   ├── sql_executor.py       # SQL validation (keyword + AST) and execution
│   ├── chart_engine.py       # Result-shape detection and Matplotlib rendering
│   ├── insight_engine.py     # LLM-generated insights + follow-up questions
│   └── history.py            # Session-level query history (st.session_state)
├── config/
│   ├── env_config.py         # Env var loader and validator (fails fast)
│   ├── db_config.py          # SQLAlchemy engine factory
│   ├── llm_config.py         # LLM provider, model, API key config
│   └── log_config.py         # Root logger setup
├── docs/                     # FRS, SDS, spec (read before coding)
├── .env                      # Local secrets (never committed)
├── pyproject.toml            # Dependencies (uv)
└── uv.lock                   # Locked dependency tree (commit this)
```

---

## 3. Tech Stack

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

## 4. Key Commands

```bash
uv sync                        # Install all dependencies
uv run streamlit run app.py    # Start dev server (http://localhost:8501)
uv run pytest                  # Run test suite
uv run ruff check .            # Lint
uv run ruff format .           # Format
```

Copy `.env.example` → `.env` and populate before running.

---

## 5. Architecture Patterns

Strict one-way dependency: **UI → Services → Config**. No layer may call upward.

```
app.py  →  services/*.py  →  config/*.py
```

- `starter.py` bootstraps once at app start; all shared resources (`db_engine`, `llm_client`, `db_schema`) live in `st.session_state` and are reused per query — never re-initialised inside a service.
- `LLMClient` is the only place that touches provider SDKs. `nl_to_sql.py` and `insight_engine.py` call `LLMClient.complete(system, user) -> str` only.
- `chart_engine.py` returns a typed `ChartResult` dict (`{"type": "figure"|"text"|"table", ...}`); `app.py` switches on `type` to render.

---

## 6. Coding Standards

- **Naming:** `snake_case` for all Python identifiers. Module names match the SDS file list exactly.
- **Custom exceptions:** `NLQueryError`, `SQLValidationError`, `DBExecutionError`, `EmptyResultError`, `InsightError` — raise these from the service that owns each failure; catch all of them in `app.py` only.
- **Error display:** All errors show the exact user-facing strings from FRS §7. Never surface raw stack traces or exception messages in the UI.
- **Logging:** Use the configured logger (`log_config.py`). Log at `ERROR` for caught exceptions, `INFO` for lifecycle events. Format: `timestamp | level | module | message`.
- **LLM responses:** Always strip markdown fences and parse/validate before use. Never `eval` or `exec` LLM output.
- **Result rows:** Always apply the `MAX_RESULT_ROWS` cap (default 10 000) from `db_config.py` before returning query results.

---

## 7. Auth Approach

**No authentication.** The FRS explicitly scopes auth out; the app assumes a trusted user environment. Do not add login flows, session tokens, or role checks. Database credentials are env-var-only and must never appear in UI, logs, or committed files.

---

## 8. API Design Conventions

This is a Streamlit app — there is no HTTP API surface. All inter-module communication is direct Python function calls following these contracts:

| Service | Inputs | Output |
|---|---|---|
| `nl_to_sql.generate(question, schema, llm_client)` | str, dict, LLMClient | `str` (clean SQL) |
| `sql_executor.run(sql, engine)` | str, Engine | `(list[str], list[tuple])` |
| `chart_engine.render(columns, rows, question)` | list, list, str | `ChartResult` dict |
| `insight_engine.generate(question, columns, rows, llm_client)` | str, list, list, LLMClient | `{"insights": [...], "suggested_questions": [...]}` |
| `history.append(question, sql)` / `.get_all()` / `.clear()` | — | side-effects on session_state |

---

## 9. DB Schema Summary

The target schema is introspected at startup by `starter.py` (table names, column names, types) and cached in `st.session_state["db_schema"]`. Supported databases: **SQLite**, **PostgreSQL**, **MySQL** (via SQLAlchemy URL). The sample/dev dataset covers sales data with at minimum: orders, products, revenue, regions, and time dimensions. Full schema is defined in the source database; no ORM models are maintained in code.

---

## 10. Testing Approach

- Framework: **pytest** (`uv run pytest`)
- Tests live in `tests/` mirroring the `services/` and `config/` structure
- Unit-test each service in isolation; mock `LLMClient` and SQLAlchemy engine at the boundary
- `sql_executor.py` validation logic must be tested against real `sqlglot` parsing — do not mock the parser
- Cover all five error types (`NLQueryError`, `SQLValidationError`, `DBExecutionError`, `EmptyResultError`, `InsightError`) with explicit test cases
- Cover all six shape-detection branches in `chart_engine.py`

---

## 11. Do NOT Do

- **Do not write SQL to the database.** The system is read-only. No `INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, `TRUNCATE` — ever.
- **Do not skip validation layers.** Both the keyword block list AND the `sqlglot` AST check must run before execution.
- **Do not put provider SDK calls outside `LLMClient`.** Provider logic must not leak into `nl_to_sql.py`, `insight_engine.py`, or `app.py`.
- **Do not re-initialise `db_engine` or `llm_client` per query.** They live in `st.session_state` and are created once in `starter.py`.
- **Do not pass the full result set to the LLM for insights.** Only top-10 rows + aggregates; this bounds token usage.
- **Do not commit `.env`, credentials, or API keys.**
- **Do not add auth, forecasting, multi-DB federation, or RBAC** — these are explicitly out of scope (FRS §11).
- **Do not show raw exceptions or stack traces in the UI.** Use the exact user-facing messages from FRS §7.

---

## 12. Shared Packages

No `/packages/shared` directory exists in this project. All shared logic lives within the `config/` layer (env vars, DB connection, LLM config, logging). `LLMClient` in `config/llm_config.py` is the closest equivalent to a shared utility — it is the single abstraction over all LLM providers.
