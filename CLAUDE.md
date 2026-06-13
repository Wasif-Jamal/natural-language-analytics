# CLAUDE.md

@AGENTS.md

---

## Claude Code-Specific Rules

### Permission Model

Proceed without asking:
- Build, test, lint (`uv run ruff format`, `uv run ruff check`, `uv run pytest`)
- `uv sync`, `git add`, `git commit`
- Reading any file; editing files in `app.py`, `services/`, `config/`, `tests/`

Always ask [y/n] before:
- `git push`, `git merge`, `git rebase`
- `uv run streamlit run app.py` (starts a server process)
- Deleting or renaming any file
- Modifying `pyproject.toml`, `uv.lock`, or `.env`

---

### Context Management

- Run `/clear` after every completed task
- At 60k tokens: save state to `session-context.md` → `/clear` → resume from that file
- Never let context fill to limit

---

### Thinking Depth

| Situation | Depth |
|---|---|
| Simple edit or bug fix | Default |
| New service, module, or feature | `think hard before starting` |
| Architecture or cross-layer decision | `ultrathink` |

---

### Commit Format

```
<type>(<scope>): <description> [AB#ticket]

[optional body — why, not what]

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
```

Types: `feat`, `fix`, `refactor`, `test`, `docs`, `chore`  
Scope: module name without extension (`nl_to_sql`, `chart_engine`, `starter`, etc.)  
Ticket: include `AB#ticket` when work traces to a ticket; omit for `chore`/`docs`

---

### Branch Naming

```
feature/{domain}/AB-{ticket}-{short-name}
fix/{domain}/AB-{ticket}-{short-name}
```

Examples: `feature/chart/AB-42-pie-chart`, `fix/sql/AB-17-cte-bypass`, `docs/update-agents-md`

---

## Quality Gates (Non-Negotiable)

### After every phase and before every commit:

1. `uv run ruff format .` — format
2. `uv run ruff check .` — lint, 0 errors
3. `uv run pytest` — all tests green

### Never commit if:
- Any test is failing
- Lint has errors
- `.env`, credentials, or API keys are staged

---

## UI / Frontend Patterns (`app.py`, `starter.py`)

- `app.py` is the only place that catches exceptions — all five typed errors plus the LLM unavailable case.
- Display errors using the exact strings from `FRS §7`. Never surface exception messages or stack traces.
- `starter.py` runs once at boot. All shared resources (`db_engine`, `llm_client`, `db_schema`) go into `st.session_state` here and nowhere else.
- Switch on `ChartResult["type"]` (`"figure"` / `"text"` / `"table"`) to render — no `isinstance` checks on raw data.
- Suggested follow-up questions render as `st.button` elements; clicking one re-submits as a new query (does not mutate the current result).
- CSV and PNG exports use Streamlit's `st.download_button` — no temporary files written to disk.

### Anti-Patterns
- Do not call provider SDKs, `sqlglot`, or SQLAlchemy directly in `app.py` — delegate to services.
- Do not store query results in module-level globals — use `st.session_state["current_result"]`.
- Do not re-run `starter.py` logic on each query — guard with `if "db_engine" not in st.session_state`.
