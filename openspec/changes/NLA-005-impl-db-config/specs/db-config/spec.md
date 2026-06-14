## ADDED Requirements

### Requirement: get_engine() creates a SQLAlchemy Engine from AppConfig

`config/db_config.py` SHALL define a single public function `get_engine(config: AppConfig) -> Engine`. It SHALL call SQLAlchemy's `create_engine` with `config.database_url`. It SHALL NOT call `os.getenv` or `load_dotenv` — all values are sourced from `AppConfig`. It SHALL set the module-level variable `MAX_RESULT_ROWS` from `config.max_result_rows` as a side effect.

**FRS reference:** SDS §4.3  
**Module:** `config/db_config.py`

#### Scenario: Valid SQLite URL returns an Engine

- **WHEN** `config.database_url = "sqlite:///data/sales.db"`
- **THEN** `get_engine(config)` returns a `sqlalchemy.engine.Engine` instance without raising

#### Scenario: get_engine() sets MAX_RESULT_ROWS module-level variable

- **WHEN** `get_engine(config)` is called with `config.max_result_rows = 500`
- **THEN** `config.db_config.MAX_RESULT_ROWS == 500` after the call

#### Scenario: MAX_RESULT_ROWS defaults to 10000

- **WHEN** `MAX_RESULT_ROWS` env var is absent (so `config.max_result_rows == 10000`)
- **THEN** `config.db_config.MAX_RESULT_ROWS == 10000` after `get_engine(config)`

---

### Requirement: Connectivity probe — SELECT 1

After creating the engine, `get_engine()` SHALL test reachability by opening a connection and executing `SELECT 1` via `sqlalchemy.text()`. The connection SHALL be released via context manager (`with engine.connect() as conn:`). This probe ensures startup fails immediately on unreachable databases rather than deferring the failure to the first query.

**FRS reference:** specs/config-bootstrap/spec.md — "engine SHALL be tested for connectivity at startup"  
**Module:** `config/db_config.py`

#### Scenario: Connectivity probe succeeds for in-memory SQLite

- **WHEN** `config.database_url = "sqlite:///:memory:"`
- **THEN** `get_engine(config)` completes the `SELECT 1` probe without raising

#### Scenario: Unreachable PostgreSQL host raises OperationalError

- **WHEN** `config.database_url` points to a PostgreSQL host that is not reachable
- **THEN** `get_engine(config)` raises `sqlalchemy.exc.OperationalError`

---

### Requirement: Invalid URL raises ArgumentError

When `config.database_url` is not a valid SQLAlchemy URL, `get_engine()` SHALL let SQLAlchemy's `ArgumentError` propagate. The caller (`starter.py`) is responsible for handling this at the UI layer.

**FRS reference:** SDS §4.3 — "raise a descriptive error for invalid URLs"  
**Module:** `config/db_config.py`

#### Scenario: Malformed URL raises ArgumentError

- **WHEN** `config.database_url = "notavalidurl"`
- **THEN** `get_engine(config)` raises `sqlalchemy.exc.ArgumentError`

---

### Requirement: No framework or env-var imports in db_config.py

`config/db_config.py` SHALL NOT import `streamlit`, `os`, `dotenv`, or any service module. Permitted imports: `sqlalchemy` (engine, text, exceptions), `config.env_config.AppConfig`.

**FRS reference:** config/CLAUDE.md anti-patterns  
**Module:** `config/db_config.py`

#### Scenario: No Streamlit import

- **WHEN** `config/db_config.py` is inspected for imports
- **THEN** no `import streamlit` or `from streamlit` is present

#### Scenario: No env-var access

- **WHEN** `config/db_config.py` is inspected
- **THEN** no `os.getenv`, `os.environ`, or `load_dotenv` call is present

---

### Requirement: Out of Scope for db_config.py

`db_config.py` SHALL NOT execute application queries, configure logging, initialise LLM clients, or apply the `MAX_RESULT_ROWS` cap to query results — that cap is applied in `sql_executor.py`. `check_same_thread` for SQLite threading is the responsibility of `starter.py`.

#### Scenario: No query execution beyond the SELECT 1 probe

- **WHEN** `get_engine(config)` is called
- **THEN** no application-level SQL is executed; only the liveness `SELECT 1` runs
