# Technical Plan — NLA-001: Create pyproject.toml

## Scope

Single file created: `pyproject.toml` (repo root).  
One auto-generated artifact committed alongside it: `uv.lock`.  
No source code changes. No DB changes. No service or config modules touched.

---

## File to Create

### `pyproject.toml` (repo root)

```toml
[project]
name = "natural-language-analytics"
version = "0.1.0"
description = "Natural language analytics dashboard — query SQL data in plain English"
requires-python = ">=3.11"
dependencies = [
    "streamlit>=1.35",
    "sqlalchemy>=2.0",
    "sqlglot>=25.0",
    "anthropic>=0.30",
    "openai>=1.30",
    "google-genai>=1.0",
    "pandas>=2.0",
    "matplotlib>=3.8",
    "seaborn>=0.13",
    "python-dotenv>=1.0",
    "pymysql>=1.1",
]

[dependency-groups]
dev = [
    "ruff>=0.4",
    "pytest>=8.0",
]

[tool.ruff]
target-version = "py311"
line-length = 88

[tool.ruff.lint]
select = ["E", "F", "I"]

[tool.pytest.ini_options]
testpaths = ["tests"]
```

---

## Architecture Decisions

| Decision | Choice | Reasoning |
|---|---|---|
| Build backend | None (`--no-package`) | This is a Streamlit app, not a distributable package. No `[build-system]` section means no hatchling dependency and no misleading packaging metadata. |
| Dev dep format | `[dependency-groups]` (PEP 735) | uv's native group format; plain `uv sync` installs all groups including dev (matches `uv sync` command in AGENTS.md §4) |
| Version constraints | Unpinned lower bounds | uv.lock handles exact pinning; lower bounds document the minimum known-good API version |
| ruff select rules | `E`, `F`, `I` | pycodestyle errors + pyflakes + isort — matches the `ruff check` gate in CLAUDE.md |
| ruff target | `py311` | Matches `requires-python = ">=3.11"` floor |
| pytest testpaths | `["tests"]` | Mirrors the `tests/` mirror structure defined in AGENTS.md §10; dir doesn't exist yet but must be declared now |
| `google-genai` package name | `google-genai` | Correct PyPI name for the new unified Google Generative AI SDK (not the legacy `google-generativeai`) |

---

## Dependency Mapping (SDS §10 → package)

| SDS Component | PyPI Package | Declared As |
|---|---|---|
| Streamlit | `streamlit` | `streamlit>=1.35` |
| SQLAlchemy | `sqlalchemy` | `sqlalchemy>=2.0` |
| sqlglot | `sqlglot` | `sqlglot>=25.0` |
| Anthropic SDK | `anthropic` | `anthropic>=0.30` |
| OpenAI SDK | `openai` | `openai>=1.30` |
| Google Gemini SDK | `google-genai` | `google-genai>=1.0` |
| Matplotlib | `matplotlib` | `matplotlib>=3.8` |
| Seaborn | `seaborn` | `seaborn>=0.13` |
| pandas | `pandas` | `pandas>=2.0` |
| python-dotenv | `python-dotenv` | `python-dotenv>=1.0` |
| MySQL driver (SDS §4.3) | `pymysql` | `pymysql>=1.1` |
| ruff (dev) | `ruff` | `ruff>=0.4` in `[dependency-groups]` |
| pytest (dev) | `pytest` | `pytest>=8.0` in `[dependency-groups]` |

---

## Reuse of Existing Code

None — this is the first file in the project. No existing patterns to inherit.

---

## DB Changes

None.

---

## Implementation Steps

1. Create `pyproject.toml` at repo root with the exact content above
2. Run `uv sync` to resolve dependencies and generate `uv.lock`
3. Verify `ruff` and `pytest` are reachable: `uv run ruff --version` + `uv run pytest --version`
4. Run quality gates (lint has no Python source to check yet; this establishes baseline)
5. Stage and commit both `pyproject.toml` and `uv.lock`

---

## Quality Gate Checkpoint

```bash
uv sync                        # generates uv.lock
uv run ruff format .           # no-op on empty repo; confirms ruff is installed
uv run ruff check .            # no Python source yet — must exit 0
uv run pytest                  # no tests yet — must exit with "no tests ran" (not error)
```

Expected exit codes: `ruff check` → 0, `pytest` → 5 (no tests collected — acceptable at this stage; will be 0 once NLA-007 adds tests).

---

## Commit

Branch: `chore/setup/NLA-001-create-pyproject-toml` (already active)

```
chore(pyproject): add pyproject.toml with all dependencies

Bootstraps the uv project with all runtime and dev dependencies,
ruff config (E/F/I, py311, line-length 88), and pytest testpaths.
Commits uv.lock alongside.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
```

Files staged: `pyproject.toml`, `uv.lock`

---

## What This Does NOT Cover

- NLA-002: `.env.example` (separate ticket)
- NLA-003–006: config module implementations
- Any source code, test files, or application logic
