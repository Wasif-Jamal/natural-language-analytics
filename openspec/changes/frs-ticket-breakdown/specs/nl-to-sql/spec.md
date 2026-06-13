## ADDED Requirements

### Requirement: Natural-language to SQL generation
`nl_to_sql.generate(question: str, schema: dict, llm_client: LLMClient) -> str` SHALL call `LLMClient.complete(system, user)` with the DB schema injected into the system prompt. The system prompt SHALL instruct the LLM to return a `SELECT`-only statement with no markdown fences. The function SHALL strip any markdown code fences (` ```sql `, ` ``` `) from the LLM response before returning. It SHALL raise `NLQueryError` if the cleaned response cannot be parsed as valid SQL by `sqlglot`.

**FRS reference:** FR-2, FR-3  
**Module:** `services/nl_to_sql.py`

#### Scenario: Valid question returns clean SQL string
- **WHEN** `generate("Show revenue by region", schema, llm_client)` is called and the LLM returns `SELECT region, SUM(revenue) FROM orders GROUP BY region`
- **THEN** the function returns `SELECT region, SUM(revenue) FROM orders GROUP BY region` (a plain string, no fences)

#### Scenario: LLM response with markdown fences is stripped
- **WHEN** the LLM returns ` ```sql\nSELECT * FROM orders\n``` `
- **THEN** `generate` returns `SELECT * FROM orders` with all fences removed

#### Scenario: Schema context is included in the system prompt
- **WHEN** `generate` is called with a schema dict containing table `orders`
- **THEN** the system prompt passed to `llm_client.complete` includes a string representation of the schema

#### Scenario: Unparseable LLM output raises NLQueryError
- **WHEN** the LLM returns a non-SQL string (e.g. `"I don't understand that question."`)
- **THEN** `generate` raises `NLQueryError`

#### Scenario: LLM API failure propagates as NLQueryError
- **WHEN** `llm_client.complete` raises an exception (e.g. API timeout)
- **THEN** `generate` wraps and re-raises it as `NLQueryError`

---

### Requirement: Generated SQL display in UI
The generated SQL SHALL be displayed to the user in an expandable code block before execution results are shown. The display SHALL use Streamlit's code block component with `sql` syntax highlighting.

**FRS reference:** FR-3, FRS §4 (SQL Display)  
**Module:** `app.py`

#### Scenario: SQL is shown after successful generation
- **WHEN** `nl_to_sql.generate` returns a SQL string
- **THEN** `app.py` renders the SQL in a `st.expander` with `st.code(..., language="sql")`

#### Scenario: SQL display does not execute the query
- **WHEN** the SQL expander is rendered
- **THEN** no database call has been made yet (SQL display is pre-execution)

---

### Requirement: Out of Scope for nl-to-sql
`nl_to_sql.py` SHALL NOT execute the SQL against any database. It SHALL NOT import SQLAlchemy, sqlglot for execution, or any provider SDK directly. Validation (keyword blocklist + AST check) is the responsibility of `sql_executor.py`, not `nl_to_sql.py`.

#### Scenario: No SQLAlchemy import in nl_to_sql.py
- **WHEN** `services/nl_to_sql.py` is inspected for imports
- **THEN** no import of `sqlalchemy` is present

#### Scenario: No provider SDK import in nl_to_sql.py
- **WHEN** `services/nl_to_sql.py` is inspected for imports
- **THEN** no import of `anthropic`, `openai`, `google.genai`, or `requests` (for Ollama) is present
