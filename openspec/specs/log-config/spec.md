# log-config Specification

## Purpose
TBD - created by archiving change NLA-004-impl-log-config. Update Purpose after archive.
## Requirements
### Requirement: setup_logging() configures the root logger from AppConfig

`config/log_config.py` SHALL define a single public function `setup_logging(config: AppConfig) -> None`. It SHALL configure the root logger using values already resolved in `AppConfig` (`log_level`, `log_file`). It SHALL NOT call `os.getenv` or `load_dotenv` — all env var resolution is the responsibility of `env_config.py`.

**FRS reference:** SDS §4.4  
**Module:** `config/log_config.py`

#### Scenario: setup_logging() accepts AppConfig and returns None

- **WHEN** `setup_logging(config)` is called with a valid `AppConfig`
- **THEN** it returns `None` and raises no exception

---

### Requirement: Log format matches SDS §4.4

The root logger's handlers SHALL use `Formatter` with the format string `%(asctime)s | %(levelname)s | %(name)s | %(message)s`. The `%(name)s` field resolves to the logger name passed to `logging.getLogger(name)` — e.g. `services.nl_to_sql` for a module that calls `logging.getLogger(__name__)`.

**FRS reference:** SDS §4.4 — `timestamp | level | module | message`  
**Module:** `config/log_config.py`

#### Scenario: Handler formatter matches required pattern

- **WHEN** `setup_logging(config)` is called
- **THEN** each handler on the root logger has a `Formatter` whose `_fmt` contains `%(asctime)s`, `%(levelname)s`, `%(name)s`, and `%(message)s` separated by ` | `

---

### Requirement: Root logger level is set from config.log_level

`setup_logging()` SHALL call `root_logger.setLevel(config.log_level)`. Because `config.log_level` defaults to `"INFO"` in `AppConfig`, the root logger level is `INFO` when `LOG_LEVEL` is not set in the environment.

**FRS reference:** SDS §4.4  
**Module:** `config/log_config.py`

#### Scenario: Default INFO level when LOG_LEVEL absent

- **WHEN** `config.log_level == "INFO"` (the AppConfig default)
- **THEN** `logging.getLogger().level == logging.INFO` after `setup_logging(config)`

#### Scenario: Custom level from config.log_level

- **WHEN** `config.log_level == "DEBUG"`
- **THEN** `logging.getLogger().level == logging.DEBUG` after `setup_logging(config)`

---

### Requirement: StreamHandler always added to stdout

`setup_logging()` SHALL always add a `logging.StreamHandler(sys.stdout)` to the root logger. This guarantees the custom format applies to all log output regardless of environment.

**FRS reference:** SDS §4.4 — log output to stdout  
**Module:** `config/log_config.py`

#### Scenario: StreamHandler present after setup

- **WHEN** `setup_logging(config)` is called with `config.log_file = None`
- **THEN** the root logger has exactly one handler and it is a `StreamHandler`

---

### Requirement: FileHandler added when config.log_file is set

When `config.log_file` is not `None`, `setup_logging()` SHALL add a `logging.FileHandler(config.log_file)` in addition to the `StreamHandler`. Both handlers SHALL share the same `Formatter`.

**FRS reference:** SDS §4.4 — optional `LOG_FILE` file handler  
**Module:** `config/log_config.py`

#### Scenario: FileHandler added when log_file is set

- **WHEN** `config.log_file == "/tmp/app.log"`
- **THEN** the root logger has exactly two handlers: a `StreamHandler` and a `FileHandler` targeting `/tmp/app.log`

#### Scenario: No FileHandler when log_file is None

- **WHEN** `config.log_file is None`
- **THEN** no `FileHandler` is present on the root logger

---

### Requirement: Existing handlers cleared before configuring (idempotent)

`setup_logging()` SHALL remove all existing handlers from the root logger before adding new ones. This prevents duplicate log output if called more than once — a requirement for test isolation.

**FRS reference:** AGENTS.md §10 (testing approach — isolation)  
**Module:** `config/log_config.py`

#### Scenario: No duplicate handlers on repeated calls

- **WHEN** `setup_logging(config)` is called twice in succession
- **THEN** the root logger has the same number of handlers as after a single call (not doubled)

#### Scenario: Pre-existing handlers replaced

- **WHEN** a handler is manually added to the root logger and then `setup_logging(config)` is called
- **THEN** the manually-added handler is no longer present; only the handlers added by `setup_logging` remain

---

### Requirement: No framework or service imports in log_config.py

`config/log_config.py` SHALL NOT import `streamlit`, any service module, `os`, `dotenv`, or any provider SDK. Only `logging`, `sys`, and `config.env_config.AppConfig` are permitted.

**FRS reference:** config/CLAUDE.md anti-patterns  
**Module:** `config/log_config.py`

#### Scenario: Only logging, sys, and AppConfig imported

- **WHEN** `config/log_config.py` is inspected for imports
- **THEN** only `import logging`, `import sys`, and `from config.env_config import AppConfig` (or equivalent) are present — no `streamlit`, `os`, `dotenv`, or provider SDK

---

### Requirement: Out of Scope for log_config.py

`log_config.py` SHALL NOT load env vars, create database connections, or initialise LLM clients. It SHALL NOT define per-module loggers — callers obtain their own logger via `logging.getLogger(__name__)`. Log level validation (ensuring the string is a valid level name) is delegated to Python's `logging` module itself.

#### Scenario: No env var access

- **WHEN** `config/log_config.py` is inspected
- **THEN** no `os.getenv`, `os.environ`, or `load_dotenv` call is present

