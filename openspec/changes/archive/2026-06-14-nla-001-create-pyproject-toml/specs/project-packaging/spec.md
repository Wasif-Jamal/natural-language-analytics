## ADDED Requirements

### Requirement: pyproject.toml declares project metadata and runtime dependencies

`pyproject.toml` SHALL exist at the repository root and SHALL declare:

- **Project name:** `natural-language-analytics`
- **Python version floor:** `requires-python = ">=3.11"`
- **Runtime dependencies** (unpinned lower bounds):
  - `streamlit>=1.35`
  - `sqlalchemy>=2.0`
  - `sqlglot>=25.0`
  - `anthropic>=0.30`
  - `openai>=1.30`
  - `google-genai>=1.0`
  - `pandas>=2.0`
  - `matplotlib>=3.8`
  - `seaborn>=0.13`
  - `python-dotenv>=1.0`
  - `pymysql>=1.1`

**FRS reference:** SDS §3 (Tech Stack), SDS §4.3 (MySQL URL support)  
**File:** `pyproject.toml`

#### Scenario: uv sync installs all dependencies

- **WHEN** `uv sync` is run in the repo root after `pyproject.toml` is created
- **THEN** all runtime packages resolve and install without conflict; `uv.lock` is generated

#### Scenario: Python version constraint is enforced

- **WHEN** `pyproject.toml` is inspected
- **THEN** `requires-python` is `">=3.11"`

#### Scenario: pymysql is present for MySQL support

- **WHEN** `pyproject.toml` dependencies are listed
- **THEN** `pymysql` appears as a runtime dependency (enabling `mysql+pymysql://` URLs per SDS §4.3)

---

### Requirement: pyproject.toml declares dev dependencies

`pyproject.toml` SHALL include an `[dependency-groups]` (uv) or `[project.optional-dependencies]` dev group containing:

- `ruff>=0.4`
- `pytest>=8.0`

#### Scenario: Dev tools are installable

- **WHEN** `uv sync --dev` (or equivalent) is run
- **THEN** `ruff` and `pytest` are available in the virtual environment

---

### Requirement: pyproject.toml includes ruff tool configuration

A `[tool.ruff]` section SHALL be present with:

- `target-version = "py311"`
- `line-length = 88`

A `[tool.ruff.lint]` section SHALL include `select = ["E", "F", "I"]` (pycodestyle errors, pyflakes, isort).

#### Scenario: ruff runs without a separate config file

- **WHEN** `uv run ruff check .` is executed from the repo root
- **THEN** ruff reads configuration from `pyproject.toml` with no additional config file required

---

### Requirement: pyproject.toml includes pytest tool configuration

A `[tool.pytest.ini_options]` section SHALL be present with:

- `testpaths = ["tests"]`

#### Scenario: pytest discovers tests without extra flags

- **WHEN** `uv run pytest` is executed from the repo root
- **THEN** pytest looks in `tests/` by default (no `-p` or `--rootdir` flags required)

---

### Requirement: Out of Scope for project-packaging

`pyproject.toml` SHALL NOT contain application source code, service implementations, or configuration logic. Version pinning of individual packages SHALL remain the sole responsibility of `uv.lock`. CI/CD pipeline configuration MUST NOT be placed in `pyproject.toml`.

#### Scenario: pyproject.toml contains no application code

- **WHEN** `pyproject.toml` is inspected
- **THEN** no Python source code, service implementations, or application logic is present — only packaging metadata, dependency declarations, and tool configuration
