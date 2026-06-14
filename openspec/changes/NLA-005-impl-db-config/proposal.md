## Why

`db_config.py` is the database connection layer. Without it, `starter.py` cannot create the SQLAlchemy `Engine` that `sql_executor.py` needs to execute every query. The module must fail fast and loudly if the URL is malformed or the database is unreachable — a silent failure here would surface as a cryptic error at query time rather than at startup. This is the last config-layer file before NLA-006 (`llm_config.py`) and NLA-011 (`starter.py`).

## What Changes

- Create `config/db_config.py` with a single public function `get_engine(config: AppConfig) -> Engine`
- Set a module-level `MAX_RESULT_ROWS` variable from `config.max_result_rows` when `get_engine` is called
- Call `sqlalchemy.create_engine(config.database_url)` internally; let `ArgumentError` propagate for malformed URLs
- Test connectivity by executing `SELECT 1` via `engine.connect()` + `sqlalchemy.text()`; let `OperationalError` propagate for unreachable hosts
- Release the connection resource explicitly after the liveness probe (`with engine.connect() as conn: conn.execute(...)`)
- No `os.getenv` or `load_dotenv` calls — all values sourced from `AppConfig`
- No Streamlit imports — config layer stays framework-agnostic

## Capabilities

### Modified Capabilities

- `config-bootstrap`: Adds `db_config.py` as the SQLAlchemy engine factory. Resolves design decisions deferred at planning time: function name (`get_engine`), connectivity probe (`engine.connect()` + `SELECT 1`), `MAX_RESULT_ROWS` exposure (module-level var set by factory call), error propagation (native SQLAlchemy `ArgumentError`/`OperationalError`), and `check_same_thread` (left to `starter.py`).

## Impact

- Creates `config/db_config.py` — no other source files changed in this ticket
- Unblocks NLA-011 (`starter.py`) — `starter.py` calls `get_engine(config)` to populate `st.session_state["db_engine"]`
- `MAX_RESULT_ROWS` module-level variable is the row-cap read by `sql_executor.py` (`from config.db_config import MAX_RESULT_ROWS`)
- Test coverage in NLA-008 (`tests/config/test_db_config.py`)
- No Streamlit imports; no service imports — config layer stays framework-agnostic
