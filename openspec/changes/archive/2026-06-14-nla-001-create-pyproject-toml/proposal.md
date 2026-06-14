## Why

The project has no `pyproject.toml`, so dependencies cannot be installed, the `uv` toolchain cannot run, and no other implementation ticket can proceed. This is the prerequisite for every subsequent task in the project.

## What Changes

- Create `pyproject.toml` declaring project metadata, all runtime dependencies with unpinned lower bounds, and dev dependencies (`ruff`, `pytest`)
- Include `[tool.ruff]` configuration (target-version, line-length, select rules) and `[tool.pytest.ini_options]` (testpaths) so no separate config files are needed
- Include `pymysql` as a runtime dependency to support the `mysql+pymysql://` URL scheme documented in SDS §4.3

## Capabilities

### New Capabilities

- `project-packaging`: Project packaging metadata — Python version floor (`>=3.11`), dependencies, dev tools, and co-located tool config for `ruff` and `pytest`

### Modified Capabilities

_(none — greenfield project)_

## Impact

- Unblocks `uv sync` and all subsequent NLA tasks (NLA-002 through NLA-047)
- No code changes — infrastructure only
- `uv.lock` will be generated on first `uv sync` and must be committed alongside `pyproject.toml`
