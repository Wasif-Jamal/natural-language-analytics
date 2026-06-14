# env-config Specification

## Purpose
TBD - created by archiving change NLA-003-impl-env-config. Update Purpose after archive.
## Requirements
### Requirement: AppConfig dataclass returned by load_config()

`config/env_config.py` SHALL define an `AppConfig` dataclass and a public function `load_config() -> AppConfig`. The function SHALL call `load_dotenv()` to load `.env` before reading `os.environ`. All downstream config modules (`db_config.py`, `llm_config.py`, `log_config.py`) SHALL receive values from `AppConfig` — they MUST NOT call `os.getenv` directly.

**FRS reference:** SDS §4.1  
**Module:** `config/env_config.py`

**AppConfig fields:**

| Field | Type | Source Env Var | Default |
|---|---|---|---|
| `database_url` | `str` | `DATABASE_URL` | required |
| `llm_provider` | `str` | `LLM_PROVIDER` | required |
| `llm_api_key` | `str \| None` | `LLM_API_KEY` or `GEMINI_API_KEY` | required (see Gemini/Ollama exceptions) |
| `llm_model` | `str \| None` | `LLM_MODEL` | `None` (provider default applied in `llm_config.py`) |
| `max_result_rows` | `int` | `MAX_RESULT_ROWS` | `10000` |
| `log_level` | `str` | `LOG_LEVEL` | `"INFO"` |
| `log_file` | `str \| None` | `LOG_FILE` | `None` |

#### Scenario: All required vars present — returns AppConfig

- **WHEN** `DATABASE_URL`, `LLM_PROVIDER`, and `LLM_API_KEY` are set in the environment
- **THEN** `load_config()` returns an `AppConfig` instance with all fields populated and no exception raised

#### Scenario: AppConfig is a dataclass

- **WHEN** `load_config()` returns
- **THEN** the result is an instance of a `@dataclass`; fields are accessible as attributes (e.g. `config.database_url`, not `config["database_url"]`)

---

### Requirement: Required var validation raises ValueError with the missing var name

`load_config()` SHALL validate that `DATABASE_URL`, `LLM_PROVIDER`, and the applicable API key are non-empty. Missing required vars SHALL raise `ValueError` with a message that identifies the missing variable by name.

**FRS reference:** SDS §4.1–4.2  
**Module:** `config/env_config.py`

#### Scenario: Missing DATABASE_URL

- **WHEN** `DATABASE_URL` is absent or empty
- **THEN** `load_config()` raises `ValueError` and the message contains `"DATABASE_URL"`

#### Scenario: Missing LLM_PROVIDER

- **WHEN** `LLM_PROVIDER` is absent or empty
- **THEN** `load_config()` raises `ValueError` and the message contains `"LLM_PROVIDER"`

---

### Requirement: LLM_PROVIDER allowlist validation

`load_config()` SHALL validate that `LLM_PROVIDER` is one of `{anthropic, openai, gemini, ollama}`. An unsupported value SHALL raise `ValueError` before any other downstream config module is invoked.

**FRS reference:** SDS §4.2  
**Module:** `config/env_config.py`

#### Scenario: Valid provider passes validation

- **WHEN** `LLM_PROVIDER` is `anthropic`, `openai`, `gemini`, or `ollama`
- **THEN** `load_config()` does not raise on provider validation

#### Scenario: Unsupported provider raises ValueError

- **WHEN** `LLM_PROVIDER=cohere` (or any value not in the allowlist)
- **THEN** `load_config()` raises `ValueError` and the message contains the invalid value and lists the allowed values

---

### Requirement: API key routing — Gemini exception and Ollama skip

The Google Gemini SDK expects the env var `GEMINI_API_KEY` by name. `load_config()` SHALL detect `LLM_PROVIDER=gemini` and read `GEMINI_API_KEY` instead of `LLM_API_KEY`. When `LLM_PROVIDER=ollama`, no API key is required and `llm_api_key` SHALL be `None`. For all other providers, `LLM_API_KEY` is required.

**FRS reference:** SDS §5.6 (LLMClient — Gemini provider)  
**Module:** `config/env_config.py`

#### Scenario: Gemini provider reads GEMINI_API_KEY

- **WHEN** `LLM_PROVIDER=gemini` and `GEMINI_API_KEY=abc123` are set (and `LLM_API_KEY` is absent)
- **THEN** `load_config()` succeeds and `config.llm_api_key == "abc123"`

#### Scenario: Missing GEMINI_API_KEY for gemini provider raises ValueError

- **WHEN** `LLM_PROVIDER=gemini` and `GEMINI_API_KEY` is absent (regardless of `LLM_API_KEY`)
- **THEN** `load_config()` raises `ValueError` and the message contains `"GEMINI_API_KEY"`

#### Scenario: Ollama provider does not require LLM_API_KEY

- **WHEN** `LLM_PROVIDER=ollama` and `LLM_API_KEY` is absent
- **THEN** `load_config()` does NOT raise an error; `config.llm_api_key` is `None`

#### Scenario: Non-Ollama, non-Gemini provider requires LLM_API_KEY

- **WHEN** `LLM_PROVIDER=anthropic` and `LLM_API_KEY` is absent
- **THEN** `load_config()` raises `ValueError` and the message contains `"LLM_API_KEY"`

---

### Requirement: MAX_RESULT_ROWS cast to int at load time

`load_config()` SHALL convert `MAX_RESULT_ROWS` to `int`. If the env var is absent, it SHALL default to `10000`. If the value is present but non-numeric, it SHALL raise `ValueError`.

**FRS reference:** SDS §4.3  
**Module:** `config/env_config.py`

#### Scenario: MAX_RESULT_ROWS defaults to 10000 when absent

- **WHEN** `MAX_RESULT_ROWS` is not set
- **THEN** `config.max_result_rows == 10000` (type `int`)

#### Scenario: MAX_RESULT_ROWS is cast to int when present

- **WHEN** `MAX_RESULT_ROWS=500`
- **THEN** `config.max_result_rows == 500` (type `int`, not `str`)

#### Scenario: Non-numeric MAX_RESULT_ROWS raises ValueError

- **WHEN** `MAX_RESULT_ROWS=lots`
- **THEN** `load_config()` raises `ValueError` and the message contains `"MAX_RESULT_ROWS"`

---

### Requirement: Optional vars resolve to typed defaults

`LOG_LEVEL` SHALL default to `"INFO"` if absent. `LOG_FILE` SHALL default to `None` if absent or empty. `LLM_MODEL` SHALL default to `None` if absent or empty (provider default is applied later in `llm_config.py`).

**FRS reference:** SDS §4.2, §4.4  
**Module:** `config/env_config.py`

#### Scenario: LOG_LEVEL defaults to INFO

- **WHEN** `LOG_LEVEL` is not set
- **THEN** `config.log_level == "INFO"`

#### Scenario: LOG_FILE defaults to None

- **WHEN** `LOG_FILE` is not set or empty
- **THEN** `config.log_file is None`

#### Scenario: LLM_MODEL defaults to None

- **WHEN** `LLM_MODEL` is not set or empty
- **THEN** `config.llm_model is None`

---

### Requirement: No framework imports in env_config.py

`config/env_config.py` SHALL NOT import `streamlit`, any service module, or any provider SDK. It SHALL only import from the standard library, `python-dotenv`, and `dataclasses`.

**FRS reference:** AGENTS.md §11 (config layer anti-patterns)  
**Module:** `config/env_config.py`

#### Scenario: No Streamlit import

- **WHEN** `config/env_config.py` is inspected for imports
- **THEN** no `import streamlit` or `from streamlit` is present

#### Scenario: No provider SDK import

- **WHEN** `config/env_config.py` is inspected for imports
- **THEN** no import of `anthropic`, `openai`, `google.genai`, or `ollama` is present

---

### Requirement: Out of Scope for env_config.py

`env_config.py` SHALL NOT create database connections, initialise LLM clients, configure logging handlers, or perform any I/O beyond reading env vars. Default model names per provider SHALL NOT be defined here — that logic belongs in `llm_config.py`.

#### Scenario: No database engine created

- **WHEN** `load_config()` is called
- **THEN** no SQLAlchemy engine is created and no database connection is attempted

