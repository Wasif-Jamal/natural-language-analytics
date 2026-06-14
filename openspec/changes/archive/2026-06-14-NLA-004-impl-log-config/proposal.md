## Why

Without `log_config.py`, every log statement in every service falls back to Python's `lastResort` handler — output goes to stderr with no formatting, no level control, and no file option. The SDS mandates a specific structured format (`timestamp | level | module | message`) and `LOG_LEVEL` / `LOG_FILE` support. This module must be initialised in `starter.py` before any other module emits a log line, so it is a prerequisite for all subsequent config and service modules.

## What Changes

- Create `config/log_config.py` with a single public function `setup_logging(config: AppConfig) -> None`
- Clear existing root logger handlers before configuring (idempotent — safe to call in tests)
- Always add an explicit `StreamHandler` to stdout so the custom format applies unconditionally
- Add a `FileHandler` targeting `config.log_file` when the field is not `None`
- Both handlers share the same `Formatter` with format string `%(asctime)s | %(levelname)s | %(name)s | %(message)s`
- Root logger level set from `config.log_level` (default `"INFO"` — already resolved in `AppConfig`)

## Capabilities

### Modified Capabilities

- `config-bootstrap`: Adds `log_config.py` as the structured logging entry point. Resolves design decisions deferred at planning time: signature (`AppConfig`), `module` field (`%(name)s` logger name), handler deduplication (clear first), and explicit `StreamHandler`.

## Impact

- Creates `config/log_config.py` — no other source files changed in this ticket
- Unblocks NLA-005 (`db_config.py`), NLA-006 (`llm_config.py`), and NLA-011 (`starter.py`) — all emit log lines that now route correctly
- No Streamlit imports; no service imports — config layer stays framework-agnostic
- Test coverage in `tests/config/test_log_config.py`
