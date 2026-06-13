## ADDED Requirements

### Requirement: Two-layer SQL validation
`sql_executor.run(sql: str, engine: Engine) -> (list[str], list[tuple])` SHALL validate the SQL through two sequential layers before executing. Layer 1: case-insensitive, whole-word regex check for forbidden keywords `INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, `TRUNCATE`. Layer 2: `sqlglot` AST parse check asserting the root statement node is a `SELECT`. Both layers SHALL raise `SQLValidationError` on failure. The `sqlglot` parser SHALL NOT be mocked in tests.

**FRS reference:** FR-4, FRS §6 (Validation Requirements)  
**Module:** `services/sql_executor.py`

#### Scenario: Valid SELECT passes both validation layers
- **WHEN** `sql = "SELECT id, name FROM products WHERE price > 100"`
- **THEN** neither validation layer raises, and execution proceeds

#### Scenario: INSERT is blocked by keyword check (layer 1)
- **WHEN** `sql = "INSERT INTO orders VALUES (1, 'test')"`
- **THEN** `run` raises `SQLValidationError` before `sqlglot` is invoked

#### Scenario: UPDATE is blocked by keyword check
- **WHEN** `sql = "UPDATE orders SET status = 'done' WHERE id = 1"`
- **THEN** `run` raises `SQLValidationError`

#### Scenario: DELETE is blocked by keyword check
- **WHEN** `sql = "DELETE FROM orders WHERE id = 1"`
- **THEN** `run` raises `SQLValidationError`

#### Scenario: DROP is blocked by keyword check
- **WHEN** `sql = "DROP TABLE orders"`
- **THEN** `run` raises `SQLValidationError`

#### Scenario: Obfuscated write via CTE blocked by AST check (layer 2)
- **WHEN** `sql = "WITH x AS (DELETE FROM orders RETURNING *) SELECT * FROM x"`
- **THEN** `run` raises `SQLValidationError` (root node is not a bare SELECT)

#### Scenario: Non-SQL string blocked by AST check
- **WHEN** `sql = "not sql at all"`
- **THEN** `run` raises `SQLValidationError`

---

### Requirement: SQL execution and result retrieval
After passing both validation layers, `run` SHALL execute the SQL via SQLAlchemy `text()` against the provided engine. It SHALL return `(columns: list[str], rows: list[tuple])`. The result set SHALL be capped at `MAX_RESULT_ROWS` (default 10 000) rows. Database-level execution failures SHALL raise `DBExecutionError`. An empty result set (zero rows) SHALL raise `EmptyResultError`.

**FRS reference:** FR-5  
**Module:** `services/sql_executor.py`

#### Scenario: Successful query returns columns and rows
- **WHEN** `SELECT id, name FROM products` returns 3 rows from a live SQLite database
- **THEN** `run` returns `(["id", "name"], [(1, "A"), (2, "B"), (3, "C")])`

#### Scenario: Result set is capped at MAX_RESULT_ROWS
- **WHEN** the query would return 15 000 rows and `MAX_RESULT_ROWS=10000`
- **THEN** `run` returns at most 10 000 rows

#### Scenario: Empty result raises EmptyResultError
- **WHEN** `SELECT * FROM orders WHERE id = 99999` returns zero rows
- **THEN** `run` raises `EmptyResultError`

#### Scenario: Database execution error raises DBExecutionError
- **WHEN** the SQL references a non-existent table (e.g. `SELECT * FROM nonexistent`)
- **THEN** `run` raises `DBExecutionError` (not a raw SQLAlchemy exception)

---

### Requirement: Out of Scope for sql-execution
`sql_executor.py` SHALL NOT call any LLM or generate SQL. It SHALL NOT access `st.session_state` directly. It SHALL NOT write any data to the database under any condition.

#### Scenario: No LLM client import in sql_executor.py
- **WHEN** `services/sql_executor.py` is inspected for imports
- **THEN** no import of `LLMClient` or any provider SDK is present

#### Scenario: No write operation reaches the database
- **WHEN** SQL containing `INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, or `TRUNCATE` is passed to `run`
- **THEN** `SQLValidationError` is raised before any database call is made
