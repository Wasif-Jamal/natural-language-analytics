## Why

`env_config.py` is the configuration foundation of the application. Without it, `starter.py` cannot load or validate env vars, meaning the app cannot start. Every downstream module — `db_config.py`, `llm_config.py`, `log_config.py` — depends on the values this module resolves. Getting loading, validation, and default-resolution right here prevents runtime failures and opaque `KeyError` / `None` explosions across the entire codebase.

## What Changes

- Create `config/env_config.py` with a single public function `load_config() -> AppConfig`
- Define `AppConfig` as a `@dataclass` with typed attributes for all env vars
- Validate required vars at load time; raise `ValueError` with a descriptive message naming the missing var
- Validate `LLM_PROVIDER` is one of `{anthropic, openai, gemini, ollama}` — fail fast on unsupported values
- Handle the Gemini key exception: when `LLM_PROVIDER=gemini`, read `GEMINI_API_KEY`; when `LLM_PROVIDER=ollama`, skip the key check entirely; all other providers require `LLM_API_KEY`
- Cast `MAX_RESULT_ROWS` to `int` at load time (default `10000`); raise `ValueError` if the value is non-numeric

## Capabilities

### Modified Capabilities

- `config-bootstrap`: Adds `env_config.py` as the startup entry point for environment variable loading and validation. Resolves the design decisions deferred at planning time: return type (`AppConfig` dataclass), Gemini key routing, provider allowlist validation, and `MAX_RESULT_ROWS` type casting.

## Impact

- Creates `config/env_config.py` — no other files changed in this ticket
- Unblocks NLA-004 (`log_config.py`), NLA-005 (`db_config.py`), NLA-006 (`llm_config.py`), and NLA-011 (`starter.py`) — all depend on `AppConfig`
- Test coverage added in NLA-007 (`tests/config/test_env_config.py`)
- No Streamlit imports; no service imports — config layer stays framework-agnostic
