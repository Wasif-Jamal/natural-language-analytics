## ADDED Requirements

### Requirement: Environment variable loading and validation
The system SHALL load all required environment variables at startup using `config/env_config.py` via `python-dotenv`. Missing required vars SHALL cause a fatal error with a descriptive message before the Streamlit app renders any UI.

Required vars: `DATABASE_URL`, `LLM_PROVIDER`, `LLM_API_KEY` (except when `LLM_PROVIDER=ollama`).
Optional vars: `LLM_MODEL`, `MAX_RESULT_ROWS` (default `10000`), `LOG_LEVEL` (default `INFO`), `LOG_FILE`.

**FRS reference:** SDS §4.1–4.3  
**Module:** `config/env_config.py`

#### Scenario: All required env vars present
- **WHEN** `DATABASE_URL`, `LLM_PROVIDER`, and `LLM_API_KEY` are set in the environment
- **THEN** `env_config.py` returns a config object without raising an exception

#### Scenario: Missing DATABASE_URL
- **WHEN** `DATABASE_URL` is absent from the environment
- **THEN** `env_config.py` raises a `ValueError` with a message naming the missing variable

#### Scenario: Missing LLM_API_KEY for non-Ollama provider
- **WHEN** `LLM_PROVIDER=anthropic` and `LLM_API_KEY` is absent
- **THEN** `env_config.py` raises a `ValueError` identifying the missing key

#### Scenario: Ollama provider does not require LLM_API_KEY
- **WHEN** `LLM_PROVIDER=ollama` and `LLM_API_KEY` is absent
- **THEN** `env_config.py` does NOT raise an error and returns a valid config

#### Scenario: MAX_RESULT_ROWS defaults to 10000
- **WHEN** `MAX_RESULT_ROWS` is not set
- **THEN** the resolved config value for `MAX_RESULT_ROWS` is `10000`

---

### Requirement: Logging configuration
The system SHALL configure the root logger via `config/log_config.py` at startup. Log format SHALL be `timestamp | level | module | message`. Log output SHALL go to stdout and optionally to a file if `LOG_FILE` is set.

**FRS reference:** SDS §4.4  
**Module:** `config/log_config.py`

#### Scenario: Default INFO log level
- **WHEN** `LOG_LEVEL` is not set
- **THEN** the root logger level is `INFO`

#### Scenario: Custom log level from env var
- **WHEN** `LOG_LEVEL=DEBUG`
- **THEN** the root logger level is `DEBUG`

#### Scenario: File logging when LOG_FILE is set
- **WHEN** `LOG_FILE=/tmp/app.log` is set
- **THEN** a `FileHandler` is added to the root logger targeting that path

---

### Requirement: Database engine creation
The system SHALL create a SQLAlchemy `Engine` via `config/db_config.py` using the `DATABASE_URL` env var. Supported URL schemes: `sqlite:///`, `postgresql://`, `mysql+pymysql://`. The engine SHALL be tested for connectivity at startup.

**FRS reference:** SDS §4.3  
**Module:** `config/db_config.py`

#### Scenario: Valid SQLite URL creates engine
- **WHEN** `DATABASE_URL=sqlite:///data/sales.db` and the file exists
- **THEN** `db_config.create_engine()` returns a SQLAlchemy `Engine` without raising

#### Scenario: Invalid URL raises on creation
- **WHEN** `DATABASE_URL=notavalidurl`
- **THEN** `db_config.create_engine()` raises an exception before the app renders

#### Scenario: Unreachable database raises on connectivity test
- **WHEN** `DATABASE_URL` points to a PostgreSQL host that is not reachable
- **THEN** the startup sequence raises a descriptive fatal error

---

### Requirement: LLM client initialisation
The system SHALL create a single `LLMClient` instance via `config/llm_config.py` using `LLM_PROVIDER`, `LLM_API_KEY`, and optionally `LLM_MODEL`. Supported providers: `anthropic`, `openai`, `gemini`, `ollama`. The `LLMClient` SHALL expose a single method: `complete(system: str, user: str) -> str`. Provider SDK imports MUST be internal to `llm_config.py`.

**FRS reference:** SDS §5.6  
**Module:** `config/llm_config.py`

#### Scenario: Anthropic provider uses correct default model
- **WHEN** `LLM_PROVIDER=anthropic` and `LLM_MODEL` is not set
- **THEN** the client uses model `claude-sonnet-4-6`

#### Scenario: OpenAI provider uses correct default model
- **WHEN** `LLM_PROVIDER=openai` and `LLM_MODEL` is not set
- **THEN** the client uses model `gpt-4o`

#### Scenario: Gemini provider uses correct default model
- **WHEN** `LLM_PROVIDER=gemini` and `LLM_MODEL` is not set
- **THEN** the client uses model `gemini-2.0-flash`

#### Scenario: LLM_MODEL override is respected
- **WHEN** `LLM_MODEL=claude-haiku-4-5-20251001` is set
- **THEN** the client sends requests using that model identifier

#### Scenario: Unsupported provider raises at init
- **WHEN** `LLM_PROVIDER=cohere`
- **THEN** `LLMClient.__init__` raises a `ValueError` identifying the unsupported provider

#### Scenario: complete() returns stripped string
- **WHEN** `LLMClient.complete(system, user)` is called with valid inputs
- **THEN** it returns a `str` (provider SDK error propagates as an exception, not None)

---

### Requirement: Application bootstrap in starter.py
`starter.py` SHALL run once at Streamlit app startup. It SHALL store all shared resources in `st.session_state`: `db_engine`, `llm_client`, `db_schema` (introspected schema dict), and `query_history` (empty list). Subsequent page rerenders SHALL NOT re-run bootstrap logic (guard: `if "db_engine" not in st.session_state`).

**FRS reference:** SDS §3  
**Module:** `starter.py`

#### Scenario: Bootstrap stores all required session state keys
- **WHEN** `starter.py` runs for the first time
- **THEN** `st.session_state` contains keys: `db_engine`, `llm_client`, `db_schema`, `query_history`

#### Scenario: Bootstrap does not re-run on rerender
- **WHEN** `starter.py` is called a second time and `db_engine` is already in `st.session_state`
- **THEN** no new engine or client is created (idempotent — existing values are preserved)

#### Scenario: Schema introspection populates db_schema
- **WHEN** bootstrap completes successfully against a live SQLite database
- **THEN** `st.session_state["db_schema"]` is a non-empty dict containing table names and column definitions

#### Scenario: Fatal startup failure renders error before app UI
- **WHEN** `DATABASE_URL` is invalid or unreachable during bootstrap
- **THEN** Streamlit displays a fatal error message and the main query UI does not render

---

### Requirement: Out of Scope for config-bootstrap
The bootstrap and config layer SHALL NOT contain any UI rendering logic, query processing logic, or chart rendering. No service module SHALL call into `starter.py`. Config modules SHALL NOT call service modules.

#### Scenario: No service import in config modules
- **WHEN** any file in `config/` is inspected for imports
- **THEN** no import from `services/` or `app.py` is present
