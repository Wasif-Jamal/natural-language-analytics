# System Design Specification
# Natural Language Analytics Dashboard

| Field | Value |
|---|---|
| **Project** | Natural Language Analytics Dashboard |
| **Version** | 1.0 |
| **Date** | 2026-06-12 |
| **Status** | Approved |
| **Architecture** | Layered modules (Streamlit UI → Services → Config) |
| **Source of Truth** | docs/nl-analytics-dashboard-spec.md |

---

## 1. Architecture Overview

The system follows a **layered module architecture**:

```
┌──────────────────────────────────────────┐
│              Streamlit UI                │
│              app.py                      │
│  (renders components, handles events)    │
└──────────────┬───────────────────────────┘
               │ calls
┌──────────────▼───────────────────────────┐
│            Services Layer                │
│  nl_to_sql.py     insight_engine.py      │
│  sql_executor.py  history.py             │
│  chart_engine.py                         │
└──────────────┬───────────────────────────┘
               │ reads from
┌──────────────▼───────────────────────────┐
│            Config Layer                  │
│  env_config.py    llm_config.py          │
│  db_config.py     log_config.py          │
└──────────────────────────────────────────┘
               │ initialised by
┌──────────────▼───────────────────────────┐
│            starter.py                    │
│  (bootstrap; runs once at app startup)   │
└──────────────────────────────────────────┘
```

Each layer has one direction of dependency: UI → Services → Config. Services do not call the UI; config modules do not call services.

---

## 2. Project Structure

```
natural-language-analytics/
├── app.py                    # Streamlit entry point
├── starter.py                # Application bootstrap (runs at startup)
├── services/
│   ├── nl_to_sql.py          # NL → SQL via LLM
│   ├── sql_executor.py       # SQL validation and execution
│   ├── chart_engine.py       # Result shape detection and chart rendering
│   ├── insight_engine.py     # LLM-generated insights and follow-up questions
│   └── history.py            # Session-level query history
├── config/
│   ├── env_config.py         # Base env var loader and validator
│   ├── db_config.py          # Database connection factory
│   ├── llm_config.py         # LLM provider, model, and API key config
│   └── log_config.py         # Logging setup
├── docs/
│   ├── nl-analytics-dashboard-spec.md
│   ├── FRS.md
│   └── SDS.md
├── .env                      # Local env vars (not committed)
├── .gitignore
├── pyproject.toml            # Project metadata and dependencies (uv)
└── uv.lock                   # Locked dependency tree (committed)
```

---

## 3. Bootstrap — `starter.py`

Runs once when the Streamlit app starts. Stores all initialised resources in `st.session_state` for reuse across queries.

**Startup sequence:**

1. Load and validate all required env vars via `env_config.py`
2. Configure logging via `log_config.py`
3. Load LLM config via `llm_config.py` (provider, model, API key)
4. Initialise `LLMClient` and verify provider reachability
5. Create SQLAlchemy engine via `db_config.py` and test DB connectivity
6. Introspect DB schema (table names, column names, types) and cache in `st.session_state`
7. Initialise empty query history list in `st.session_state`

If any step fails, `starter.py` raises a descriptive fatal error that Streamlit displays before the app renders.

---

## 4. Config Layer

### 4.1 `env_config.py`

Loads all environment variables. Validates that required vars are present at startup and raises a clear error for any that are missing.

### 4.2 `llm_config.py`

| Env Var | Required | Description |
|---|---|---|
| `LLM_PROVIDER` | Yes | One of: `anthropic`, `openai`, `gemini`, `ollama` |
| `LLM_API_KEY` | Yes (except ollama) | API key for the configured provider |
| `LLM_MODEL` | No | Overrides the default model for the provider |

**Default models per provider:**

| Provider | Default Model |
|---|---|
| `anthropic` | `claude-sonnet-4-6` |
| `openai` | `gpt-4o` |
| `gemini` | `gemini-2.0-flash` |
| `ollama` | Configured locally; no default enforced |

### 4.3 `db_config.py`

| Env Var | Required | Default | Description |
|---|---|---|---|
| `DATABASE_URL` | Yes | — | SQLAlchemy connection string for SQLite, PostgreSQL, or MySQL |
| `MAX_RESULT_ROWS` | No | `10000` | Row cap applied to all queries to prevent resource exhaustion |

Returns a SQLAlchemy `Engine` instance. Supported URL formats:

```
SQLite:     sqlite:///path/to/database.db
PostgreSQL: postgresql://user:password@host:port/dbname
MySQL:      mysql+pymysql://user:password@host:port/dbname
```

### 4.4 `log_config.py`

| Env Var | Required | Default | Description |
|---|---|---|---|
| `LOG_LEVEL` | No | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `LOG_FILE` | No | None | Optional file path for log output |

Configures the root logger with a structured format: `timestamp | level | module | message`.

---

## 5. Services Layer

### 5.1 `nl_to_sql.py`

**Responsibility:** Converts a natural-language question into a SQL SELECT statement using the configured LLM.

**Inputs:** `question: str`, `schema: dict` (from session state), `llm_client: LLMClient`

**Output:** `sql: str`

**Prompt structure:**

```
System: You are a SQL expert. The database schema is:
        {schema}
        Rules: generate SELECT only. No INSERT, UPDATE, DELETE, DROP, ALTER, TRUNCATE.
        Return only the SQL query — no explanation, no markdown fences.

User:   {question}
```

**Post-processing:** Strips markdown code fences (```sql ... ```) from the LLM response before returning. Raises `NLQueryError` if the cleaned response fails basic SQL parse.

---

### 5.2 `sql_executor.py`

**Responsibility:** Validates and executes SQL queries against the configured database.

**Inputs:** `sql: str`, `engine: Engine`

**Output:** `(columns: list[str], rows: list[tuple])`

**Validation — two layers:**

1. **Keyword block list:** Case-insensitive, whole-word regex check for `INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, `TRUNCATE`. Raises `SQLValidationError` on match.
2. **AST parse check:** Uses `sqlglot` to parse the SQL and assert the root node is a `SELECT`. Rejects obfuscated statements (e.g. `WITH ... DELETE`). Raises `SQLValidationError` on failure.

**Execution:** Runs the query via SQLAlchemy `text()`. Row count is capped at 10,000 (configurable via `MAX_RESULT_ROWS` env var) to prevent runaway queries. Raises `DBExecutionError` on database-level failures.

---

### 5.3 `chart_engine.py`

**Responsibility:** Detects the shape of a result set and renders the appropriate Matplotlib figure, or formats a plain-language sentence for scalar results.

**Inputs:** `columns: list[str]`, `rows: list[tuple]`, `question: str`

**Output:** `ChartResult` — one of:
- `{"type": "figure", "figure": matplotlib.Figure}` — for chart results
- `{"type": "text", "text": str}` — for scalar results
- `{"type": "table"}` — for ambiguous shapes (table-only fallback)

**Shape detection logic:**

| Condition | Chart Type |
|---|---|
| 1 row × 1 column | Plain-language sentence |
| One column is a date/time type | Line chart |
| Two numeric columns | Scatter plot |
| One categorical + one measure, values sum ≈ 100% | Pie chart |
| One categorical + one measure (general) | Bar chart |
| All other shapes | Table only |

Figures are rendered with Matplotlib, styled cleanly, and are PNG-exportable via `figure.savefig()`.

---

### 5.4 `insight_engine.py`

**Responsibility:** Generates actionable insights and suggested follow-up questions from the query result.

**Inputs:** `question: str`, `columns: list[str]`, `rows: list[tuple]`, `llm_client: LLMClient`

**Output:** `{"insights": list[str], "suggested_questions": list[str]}`

**Context passed to LLM:** Top 10 rows + basic aggregates (min, max, sum, mean for numeric columns) — not the full dataset. This bounds token usage while grounding the response in real data.

**Prompt structure:**

```
System: You are a business analyst. Given a query result summary, generate
        2-4 concise actionable insights and exactly 3 follow-up questions.
        Base insights strictly on the data provided — do not invent figures
        or make claims not supported by the data.
        Return valid JSON only:
        {"insights": ["...", "..."], "suggested_questions": ["...", "...", "..."]}

User:   Question: {question}
        Result summary: {top_10_rows_and_aggregates}
```

Raises `InsightError` (non-fatal) if LLM returns unparseable JSON; the UI skips the insights panel gracefully in this case.

---

### 5.5 `history.py`

**Responsibility:** Manages session-level query history stored in `st.session_state`.

**Operations:**
- `append(question, sql)` — adds `{question, sql, timestamp}` to history list
- `get_all()` — returns history list in reverse-chronological order
- `clear()` — resets history (session end or manual clear)

History is in-memory only; it does not persist across Streamlit sessions or page refreshes.

---

### 5.6 `LLMClient`

**Responsibility:** Provider-agnostic LLM wrapper. Routes calls to the correct SDK based on `LLM_PROVIDER`.

**Supported providers:**

| Provider Value | SDK | Auth Env Var |
|---|---|---|
| `anthropic` | `anthropic` Python SDK | `LLM_API_KEY` |
| `openai` | `openai` Python SDK | `LLM_API_KEY` |
| `gemini` | `google-genai` Python SDK | `GEMINI_API_KEY` (SDK-expected name) |
| `ollama` | Ollama REST API | None |

**Interface:** `LLMClient.complete(system: str, user: str) -> str`

All provider-specific SDK calls are encapsulated here. No provider logic leaks into `nl_to_sql.py` or `insight_engine.py`.

---

## 6. End-to-End Data Flow

```
User submits question
        │
        ▼
nl_to_sql.py
  · Injects schema context into prompt
  · Calls LLMClient.complete() → raw SQL string
  · Strips markdown fences
  · Returns clean SQL
        │
        ▼
sql_executor.py
  · Layer 1: keyword block list check
  · Layer 2: sqlglot AST parse check
  · Executes via SQLAlchemy → (columns, rows)
        │
        ▼
chart_engine.py
  · Detects result shape
  · Renders Matplotlib figure OR formats plain-language sentence
  · Returns ChartResult
        │
        ▼
insight_engine.py
  · Builds result summary (top 10 rows + aggregates)
  · Calls LLMClient.complete() → JSON
  · Returns {insights, suggested_questions}
        │
        ▼
history.py
  · Appends {question, sql, timestamp} to session state
        │
        ▼
app.py
  · Renders: SQL display, chart/answer, insights,
    suggested questions, results table, query history
```

---

## 7. UI Layout

```
┌─────────────────────────────────────────────────────┐
│  Natural Language Analytics Dashboard                │
├─────────────────────────────────────────────────────┤
│  [ Question input                        ] [Execute] │
├─────────────────────────────────────────────────────┤
│  ▶ Generated SQL (expandable code block)             │
├───────────────────────┬─────────────────────────────┤
│  Chart / Answer Panel │  Insights Panel              │
│                       │  · Insight 1                 │
│  (Matplotlib figure   │  · Insight 2                 │
│   or plain sentence)  │  · Insight 3                 │
│  [Download PNG]       │                              │
├───────────────────────┴─────────────────────────────┤
│  Suggested Follow-up Questions                       │
│  [Question 1]  [Question 2]  [Question 3]            │
├─────────────────────────────────────────────────────┤
│  Results Table (paginated, sortable)  [Download CSV] │
├─────────────────────────────────────────────────────┤
│  ▶ Query History (expandable)                        │
│    · Question — timestamp  [Re-run]                  │
└─────────────────────────────────────────────────────┘
```

---

## 8. Session State

| Key | Type | Set By | Purpose |
|---|---|---|---|
| `db_engine` | `sqlalchemy.Engine` | `starter.py` | Reused DB connection per query |
| `llm_client` | `LLMClient` | `starter.py` | Reused LLM client per query |
| `db_schema` | `dict` | `starter.py` | Cached schema introspection |
| `query_history` | `list[dict]` | `history.py` | Session query history |
| `current_result` | `dict` | `app.py` | Active query result (columns, rows, chart, insights, suggestions) |

---

## 9. Error Handling

| Exception | Raised By | UI Message |
|---|---|---|
| `NLQueryError` | `nl_to_sql.py` | `Unable to identify requested entities.` |
| `SQLValidationError` | `sql_executor.py` | `Generated query could not be validated.` |
| `DBExecutionError` | `sql_executor.py` | `Unable to retrieve data at this time.` |
| `EmptyResultError` | `sql_executor.py` | `No data found for the requested query.` |
| `InsightError` | `insight_engine.py` | Insights panel silently skipped (non-fatal) |
| LLM API unavailable | `LLMClient` | `Unable to process your question at this time. Please try again.` |

All exceptions are caught in `app.py`. Raw stack traces are never shown to users. Errors are logged at `ERROR` level via the configured logger.

---

## 10. Technology Stack

| Component | Technology |
|---|---|
| UI framework | Streamlit |
| Charts | Matplotlib + Seaborn |
| Database ORM | SQLAlchemy |
| SQL parsing / validation | sqlglot |
| LLM — Anthropic | `anthropic` Python SDK |
| LLM — OpenAI | `openai` Python SDK |
| LLM — Google Gemini | `google-genai` Python SDK |
| LLM — Ollama | Ollama REST API (HTTP) |
| Env var management | `python-dotenv` |
| Data manipulation | pandas |
| Package management | `uv` (`pyproject.toml` + `uv.lock`) |
| Language | Python 3.11+ |

---

## 11. Security Considerations

- All SQL is validated before execution; write operations never reach the database.
- Database credentials are loaded from env vars only; never exposed in the UI or logged.
- LLM API keys are loaded from env vars; never hardcoded or committed.
- Query results are row-capped (default 10,000) to prevent resource exhaustion.
- LLM responses are stripped and parsed before use; not executed as code.
