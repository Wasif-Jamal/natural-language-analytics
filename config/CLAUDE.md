# config/CLAUDE.md — Shared Config + LLMClient

See root `CLAUDE.md` for quality gates, commit format, and permission model.

---

## Commands

```bash
uv run pytest tests/config/      # Run config tests only
uv run ruff check config/        # Lint this layer only
```

---

## What Lives Here

| Module | Responsibility |
|---|---|
| `env_config.py` | Load + validate all env vars; fail fast with a clear message if required vars are missing |
| `db_config.py` | SQLAlchemy engine factory; enforces `MAX_RESULT_ROWS` cap |
| `llm_config.py` | `LLMClient` — the only place that imports provider SDKs |
| `log_config.py` | Root logger setup; structured format `timestamp \| level \| module \| message` |

`LLMClient` is the single shared abstraction over all LLM providers. It is the closest equivalent to a shared utility in this project.

---

## Patterns

- All env vars are loaded once in `env_config.py` and validated at startup — never call `os.getenv` directly in a service.
- `LLMClient.__init__` reads provider config; `LLMClient.complete(system, user) -> str` is the only public method services call.
- Adding a new provider: implement the branch inside `LLMClient` only. Do not touch `nl_to_sql.py` or `insight_engine.py`.
- Adding a new env var: add it to `env_config.py`, validate it there, and document it in `SDS §4`.

---

## Anti-Patterns

- Do not import `streamlit` anywhere in `config/` — this layer must be framework-agnostic.
- Do not put business logic (SQL generation, chart rendering) in `config/`.
- Do not add a new provider SDK import outside `llm_config.py`.
- Do not hardcode API keys, DB URLs, or model names — all must come from env vars.
