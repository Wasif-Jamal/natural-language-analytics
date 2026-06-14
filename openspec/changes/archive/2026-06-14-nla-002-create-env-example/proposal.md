## Why

No `.env.example` exists, so a new developer has no reference for which environment variables are required, which are optional, and what valid values look like. Without it, `starter.py` will fail at startup with opaque errors. This file is the prerequisite for NLA-003 (`env_config.py`), which validates these vars at runtime.

## What Changes

- Create `.env.example` at the repo root with all vars from SDS §4.1–4.4, grouped by subsystem
- Use documented placeholder values (not empty assignments) so the file is self-explanatory
- Document `GEMINI_API_KEY` as a commented-out line alongside `LLM_API_KEY`, surfacing the SDS §5.6 discrepancy before a developer hits a confusing SDK error
- Omit `OLLAMA_BASE_URL` — no env var is defined for it in the SDS; Ollama host config belongs in NLA-006 (`llm_config.py`)

## Capabilities

### New Capabilities

- `env-configuration`: Developer reference for all environment variables — required vars, optional vars with defaults, per-provider notes, and inline documentation

### Modified Capabilities

_(none)_

## Impact

- One new file at repo root: `.env.example`
- No source code changes
- Unblocks NLA-003 (`env_config.py`) — the implementation can reference this file for the exact var names and validation rules
- `.env` must remain in `.gitignore`; `.env.example` is safe to commit
