## Phase 1 — Foundation: Create pyproject.toml

- [ ] Create `pyproject.toml` at repo root with `[project]` metadata: `name = "natural-language-analytics"`, `version = "0.1.0"`, `requires-python = ">=3.11"` — no `[build-system]` section
- [ ] Add runtime dependencies to `[project] dependencies`: `streamlit>=1.35`, `sqlalchemy>=2.0`, `sqlglot>=25.0`, `anthropic>=0.30`, `openai>=1.30`, `google-genai>=1.0`, `pandas>=2.0`, `matplotlib>=3.8`, `seaborn>=0.13`, `python-dotenv>=1.0`, `pymysql>=1.1`
- [ ] Add `[dependency-groups]` dev group: `ruff>=0.4`, `pytest>=8.0`
- [ ] Add `[tool.ruff]` section: `target-version = "py311"`, `line-length = 88`
- [ ] Add `[tool.ruff.lint]` section: `select = ["E", "F", "I"]`
- [ ] Add `[tool.pytest.ini_options]` section: `testpaths = ["tests"]`

**Phase 1 checkpoint:**
```bash
python3 -c "import tomllib; tomllib.load(open('pyproject.toml', 'rb')); print('TOML valid')"
```
- [ ] TOML syntax check exits 0 (catches malformed file before `uv sync` sees it)

---

## Phase 2 — Bootstrap: Generate uv.lock

- [ ] Run `uv sync` — resolves all runtime + dev dependencies and writes `uv.lock`
- [ ] Confirm `uv.lock` file exists at repo root and is non-empty

**Phase 2 checkpoint** (`uv sync` success IS the gate — dependency resolution confirms all package names and lower bounds are valid):
- [ ] `uv sync` exits 0 with no conflict errors

---

## Phase 3 — Quality Gates

```bash
uv run ruff format .     # no Python source yet; confirms ruff installed and config loads
uv run ruff check .      # must exit 0
uv run pytest            # must exit 5 (no tests collected) — not exit 1
```

- [ ] `uv run ruff format .` exits 0
- [ ] `uv run ruff check .` exits 0 with 0 errors
- [ ] `uv run pytest` exits 5 (no tests collected — acceptable; not an error code)

---

## Phase 4 — Scenario Verification (spec/project-packaging/spec.md)

One check per scenario declared in the spec delta:

- [ ] **Scenario: uv sync installs all dependencies** — `uv sync` completed without conflict in Phase 2 ✓
- [ ] **Scenario: Python version constraint** — inspect `pyproject.toml`: `requires-python = ">=3.11"` is present
- [ ] **Scenario: pymysql present** — inspect `pyproject.toml` dependencies list: `pymysql>=1.1` appears
- [ ] **Scenario: Dev tools installable** — `uv run ruff --version` and `uv run pytest --version` both return without error
- [ ] **Scenario: ruff runs without a separate config file** — `uv run ruff check .` reads config from `pyproject.toml`; no `ruff.toml` or `.ruff.toml` exists
- [ ] **Scenario: pytest discovers tests without extra flags** — `uv run pytest` uses `tests/` as testpath (confirmed via `--co -q` once `tests/` exists in NLA-007)
- [ ] **Scenario: pyproject.toml contains no application code** — file contains only packaging metadata, dependency declarations, and tool config; no Python source

**Phase 4 checkpoint (full quality gate — must pass before commit):**
```bash
uv run ruff format .     # exits 0
uv run ruff check .      # exits 0, 0 errors
uv run pytest            # exits 5 (no tests collected — not exit 1)
```
- [ ] All three commands exit at expected codes
