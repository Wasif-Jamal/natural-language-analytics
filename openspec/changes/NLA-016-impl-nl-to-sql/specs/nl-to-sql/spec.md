## ADDED Requirements

### Requirement: Schema dict structure
`starter.py` SHALL build `db_schema` as a dict with the following top-level keys:

```python
{
    "dialect": str,          # engine.dialect.name — e.g. "sqlite", "postgresql", "mysql"
    "tables": {
        "<table_name>": [    # list of column dicts, in schema order
            {"name": str, "type": str},
            ...
        ],
        ...
    }
}
```

`nl_to_sql.generate` reads both `schema["dialect"]` and `schema["tables"]`. `starter.py` is the only writer of this dict; services are read-only consumers.

**FRS reference:** SDS §3 (bootstrap sequence), SDS §5.1  
**Module:** `starter.py` (writer), `services/nl_to_sql.py` (reader)

#### Scenario: dialect key is present after bootstrap
- **WHEN** `starter.py` completes its bootstrap sequence
- **THEN** `st.session_state["db_schema"]["dialect"]` is a non-empty lowercase string matching the database engine type

#### Scenario: tables key maps table names to column lists
- **WHEN** `starter.py` introspects a database with a table `orders(id INTEGER, region TEXT)`
- **THEN** `st.session_state["db_schema"]["tables"]["orders"]` equals `[{"name": "id", "type": "INTEGER"}, {"name": "region", "type": "TEXT"}]`

---

### Requirement: Schema serialized as CREATE TABLE DDL
`nl_to_sql.generate` SHALL serialize `schema["tables"]` into CREATE TABLE-style DDL strings — one statement per table — and include them in the system prompt. The format SHALL be:

```
CREATE TABLE orders (id INTEGER, region TEXT, revenue REAL);
CREATE TABLE products (id INTEGER, name TEXT, category TEXT, price REAL);
```

**FRS reference:** SDS §5.1 (Prompt structure)  
**Module:** `services/nl_to_sql.py`

#### Scenario: DDL string includes all tables from schema
- **WHEN** `schema["tables"]` contains tables `orders` and `products`
- **THEN** the system prompt passed to `llm_client.complete` contains both `CREATE TABLE orders (…)` and `CREATE TABLE products (…)`

#### Scenario: DDL preserves column names and types
- **WHEN** `orders` has columns `[{"name": "id", "type": "INTEGER"}, {"name": "revenue", "type": "REAL"}]`
- **THEN** the DDL string contains `CREATE TABLE orders (id INTEGER, revenue REAL)`

---

### Requirement: Dialect-specific instruction in system prompt
`nl_to_sql.generate` SHALL read `schema.get("dialect", "SQL")` and include a dialect instruction in the system prompt — e.g. `"Generate SQLite-compatible SQL."` If the key is missing, the instruction falls back to `"Generate standard SQL."`.

**FRS reference:** SDS §5.1  
**Module:** `services/nl_to_sql.py`

#### Scenario: Dialect instruction appears in system prompt
- **WHEN** `schema["dialect"] == "postgresql"`
- **THEN** the system prompt contains `"postgresql"` (case-insensitive)

#### Scenario: Missing dialect key falls back gracefully
- **WHEN** `schema` has no `"dialect"` key
- **THEN** `generate` does not raise; the system prompt uses a generic SQL instruction

---

### Requirement: Module-level system prompt template
`nl_to_sql.py` SHALL define `_SYSTEM_PROMPT_TEMPLATE` as a module-level string constant. The final system string SHALL be built dynamically each call by formatting the template with the current dialect and DDL.  The complete formatted string SHALL be passed as the `system` argument to `LLMClient.complete(system, user)`.

**FRS reference:** SDS §5.1  
**Module:** `services/nl_to_sql.py`

#### Scenario: System prompt is built fresh each call
- **WHEN** `generate` is called twice with different schema dicts
- **THEN** each call produces a distinct system prompt reflecting that call's schema

---

### Requirement: Empty or whitespace-only LLM response raises NLQueryError
If `llm_client.complete` returns a string that is empty or contains only whitespace after stripping markdown fences, `generate` SHALL raise `NLQueryError` before attempting any sqlglot parsing.

**FRS reference:** FRS §7 (`NLQueryError` — unable to identify requested entities)  
**Module:** `services/nl_to_sql.py`

#### Scenario: Empty string raises NLQueryError
- **WHEN** `llm_client.complete` returns `""`
- **THEN** `generate` raises `NLQueryError`

#### Scenario: Whitespace-only string raises NLQueryError
- **WHEN** `llm_client.complete` returns `"   \n  "`
- **THEN** `generate` raises `NLQueryError`

---

### Requirement: sqlglot validation asserts SELECT root
After stripping fences, `generate` SHALL parse the cleaned SQL with `sqlglot.parse_one`. It SHALL assert the root node is an instance of `sqlglot.exp.Select`. It SHALL raise `NLQueryError` if parsing fails OR if the root node is not a SELECT. This is defence-in-depth; `sql_executor.py` also validates via AST check.

**FRS reference:** FRS §6, SDS §5.1  
**Module:** `services/nl_to_sql.py`

#### Scenario: Non-SELECT root raises NLQueryError in nl_to_sql
- **WHEN** the LLM returns `"INSERT INTO orders VALUES (1, 2)"`
- **THEN** `generate` raises `NLQueryError` (before the string ever reaches `sql_executor`)

#### Scenario: Valid SELECT passes sqlglot check
- **WHEN** the LLM returns `"SELECT region, SUM(revenue) FROM orders GROUP BY region"`
- **THEN** `generate` returns the SQL string without raising

---

### Requirement: Exception chaining for LLM API failures
When `llm_client.complete` raises any exception, `generate` SHALL catch it and re-raise as `NLQueryError` using `raise NLQueryError("…") from e`, preserving the original exception as `__cause__` for logging.

**FRS reference:** FRS §7 (LLM API unavailable), SDS §9  
**Module:** `services/nl_to_sql.py`

#### Scenario: Original exception is accessible via __cause__
- **WHEN** `llm_client.complete` raises `RuntimeError("timeout")`
- **THEN** the caught `NLQueryError` has `exc.__cause__` set to the original `RuntimeError`

---

### Requirement: Import guard — no provider SDK or SQLAlchemy
`services/nl_to_sql.py` SHALL NOT import `sqlalchemy`, `anthropic`, `openai`, `google.genai`, or `requests`. Its only external dependencies are `sqlglot` (for validation) and `LLMClient` (from `config.llm_config`).

**FRS reference:** AGENTS.md §11 (Do NOT do), SDS §5.1 (Out of Scope)  
**Module:** `services/nl_to_sql.py`

#### Scenario: No SQLAlchemy import
- **WHEN** `services/nl_to_sql.py` is read and its import lines are inspected
- **THEN** none of the import lines contain `sqlalchemy`

#### Scenario: No provider SDK import
- **WHEN** `services/nl_to_sql.py` is read and its import lines are inspected
- **THEN** none of the import lines contain `anthropic`, `openai`, `google.genai`, or `requests`
