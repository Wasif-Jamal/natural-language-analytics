## ADDED Requirements

### Requirement: Typed custom exception hierarchy
The codebase SHALL define five custom exception classes. Each SHALL be raised only by the service that owns it. All five SHALL be caught exclusively in `app.py`.

| Exception | Raised By | Trigger |
|---|---|---|
| `NLQueryError` | `nl_to_sql.py` | LLM fails to produce valid SQL |
| `SQLValidationError` | `sql_executor.py` | Blocked keyword or non-SELECT AST |
| `DBExecutionError` | `sql_executor.py` | Database-level failure during execution |
| `EmptyResultError` | `sql_executor.py` | Query returns zero rows |
| `InsightError` | `insight_engine.py` | LLM returns unparseable JSON or API error |

**FRS reference:** FRS §7, SDS §9  
**Module:** defined in a shared exceptions module (e.g. `services/exceptions.py`) or inline per service; imported by `app.py`

#### Scenario: NLQueryError is raised and caught
- **WHEN** `nl_to_sql.generate` raises `NLQueryError`
- **THEN** `app.py` catches it and displays `"Unable to identify requested entities."` inline in the UI

#### Scenario: SQLValidationError is raised and caught
- **WHEN** `sql_executor.run` raises `SQLValidationError`
- **THEN** `app.py` catches it and displays `"Generated query could not be validated."` inline in the UI

#### Scenario: DBExecutionError is raised and caught
- **WHEN** `sql_executor.run` raises `DBExecutionError`
- **THEN** `app.py` catches it and displays `"Unable to retrieve data at this time."` inline in the UI

#### Scenario: EmptyResultError is raised and caught
- **WHEN** `sql_executor.run` raises `EmptyResultError`
- **THEN** `app.py` catches it and displays `"No data found for the requested query."` inline in the UI

#### Scenario: InsightError is non-fatal — panel silently hidden
- **WHEN** `insight_engine.generate` raises `InsightError`
- **THEN** `app.py` catches it, does NOT display any error message, and silently omits the insights panel; chart and table are still rendered

---

### Requirement: LLM API unavailable error
When the LLM provider is unreachable or returns an unrecoverable API error (not wrapped into `NLQueryError` or `InsightError`), `app.py` SHALL catch the exception and display the exact message: `"Unable to process your question at this time. Please try again."`. The app SHALL NOT crash or require a restart.

**FRS reference:** FRS §7 (LLM API unavailable row)  
**Module:** `app.py`, `config/llm_config.py`

#### Scenario: LLM unavailable during NL-to-SQL
- **WHEN** `LLMClient.complete` raises a provider API error during SQL generation
- **THEN** `app.py` displays `"Unable to process your question at this time. Please try again."`

#### Scenario: App remains operable after an LLM error
- **WHEN** an LLM API error occurs
- **THEN** the user can submit a new question without restarting the app

---

### Requirement: No raw exceptions or stack traces in the UI
`app.py` SHALL NEVER render a raw Python exception message, traceback, or stack trace to the user. All error display SHALL use the exact strings from FRS §7. Errors SHALL be logged at `ERROR` level via the configured logger.

**FRS reference:** FRS §7, SDS §9  
**Module:** `app.py`

#### Scenario: Exception message is not shown in UI
- **WHEN** any of the five typed exceptions are raised
- **THEN** the text rendered to the user matches exactly the FRS §7 string for that exception — no raw Python error message

#### Scenario: Error is logged at ERROR level
- **WHEN** a typed exception is caught in `app.py`
- **THEN** the exception is logged at `ERROR` level with the module name and exception details (not shown in UI)

#### Scenario: Stack traces are not visible in the UI
- **WHEN** an unhandled exception propagates to the Streamlit level
- **THEN** Streamlit's default error display is superseded by the catch-all handler in `app.py` showing the LLM-unavailable message

---

### Requirement: Out of Scope for error-handling
`app.py` SHALL NOT raise any of the five typed exceptions — it only catches them. Services SHALL NOT catch each other's exceptions. No exception SHALL be silently swallowed without at minimum logging at `ERROR` level (except `InsightError`, which is intentionally non-fatal and may be logged at `WARNING`).

#### Scenario: Services do not catch foreign exceptions
- **WHEN** `nl_to_sql.py` raises `NLQueryError`
- **THEN** `sql_executor.py` and `insight_engine.py` do not have a `try/except NLQueryError` block

#### Scenario: InsightError is logged (not silently swallowed)
- **WHEN** `InsightError` is caught in `app.py`
- **THEN** the exception is logged at `WARNING` or `ERROR` level before the insights panel is hidden
