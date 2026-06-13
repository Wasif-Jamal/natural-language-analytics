# services/CLAUDE.md — Backend Service Layer

See root `CLAUDE.md` for quality gates, commit format, and permission model.

---

## Commands

```bash
uv run pytest tests/services/    # Run service tests only
uv run ruff check services/      # Lint this layer only
```

---

## Patterns

- Every service exposes one public function matching the contract in `AGENTS.md §8`. No extra public API.
- Raise the correct typed exception immediately on failure — never return `None` or a sentinel to signal errors.
- Each service receives its dependencies as arguments (`llm_client`, `engine`). Never import from `st.session_state` directly inside a service.
- LLM calls go through `LLMClient.complete(system, user)` only. Import `LLMClient` from `config.llm_config`.
- Strip all markdown fences from LLM responses before returning or parsing. Never pass raw LLM output downstream.
- `insight_engine` must pass only top-10 rows + numeric aggregates to the LLM — never the full result set.

---

## Anti-Patterns

- Do not import `streamlit` in any service — services must be UI-agnostic.
- Do not call one service from another — fan-out is orchestrated in `app.py` only.
- Do not catch exceptions inside a service unless retrying; let typed exceptions propagate to `app.py`.
- Do not re-initialise `db_engine` or `llm_client` — they are passed in from `st.session_state`.
- Do not run SQL without passing through both validation layers in `sql_executor.py`.
- Do not `eval` or `exec` any string, including LLM output.
