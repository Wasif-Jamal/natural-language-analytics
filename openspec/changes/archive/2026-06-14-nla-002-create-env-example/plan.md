# Technical Plan — NLA-002: Create .env.example

## Scope

Single file created: `.env.example` (repo root).  
No source code changes. No DB changes. No service or config modules touched.

---

## File to Create

### `.env.example` (repo root)

```bash
# Natural Language Analytics Dashboard — environment configuration
# Copy this file to .env and fill in the values before running.
# Never commit .env to version control.

# --- Database ---
# SQLAlchemy connection string. Supported: sqlite:///, postgresql://, mysql+pymysql://
DATABASE_URL=sqlite:///data/sales.db

# --- LLM ---
# LLM provider. One of: anthropic, openai, gemini, ollama
LLM_PROVIDER=anthropic

# API key for the configured provider. Not required when LLM_PROVIDER=ollama.
LLM_API_KEY=your-api-key-here

# Required when LLM_PROVIDER=gemini (SDK-expected name). Leave blank for other providers.
# GEMINI_API_KEY=your-gemini-api-key-here

# Optional: override the default model for the provider.
# Defaults: anthropic → claude-sonnet-4-6 | openai → gpt-4o | gemini → gemini-2.0-flash
LLM_MODEL=

# Maximum rows returned per query (default: 10000).
MAX_RESULT_ROWS=10000

# --- Logging ---
# Log level (default: INFO). One of: DEBUG, INFO, WARNING, ERROR
LOG_LEVEL=INFO

# Optional: path to a log file. Leave blank to log to stdout only.
LOG_FILE=
```

---

## Architecture Decisions

| Decision | Choice | Reasoning |
|---|---|---|
| `GEMINI_API_KEY` documented | Commented-out line | SDS §5.6 explicitly names `GEMINI_API_KEY` as the SDK-expected var for Gemini. Omitting it would leave developers with a confusing auth failure. Commenting it out (not activating it) avoids polluting the required-var surface. |
| Ollama base URL omitted | Not included | No env var for Ollama's host is defined anywhere in the SDS. Adding one here would invent a requirement. Belongs in NLA-006. |
| Placeholder style | Documented values | `sqlite:///data/sales.db`, `anthropic`, `your-api-key-here` etc. make the file self-explanatory without real credentials. |
| Section grouping | Three headers | Mirrors SDS §4 subsection structure (§4.3 DB, §4.2 LLM, §4.4 Logging). Makes onboarding faster for new developers. |
| `LLM_MODEL` and `LOG_FILE` | Empty assignment | These are genuinely optional with well-defined defaults. Empty value signals "use the default" clearly. |

---

## Var Reference (SDS §4 → .env.example)

| SDS Section | Var | Required | Default | Value in file |
|---|---|---|---|---|
| §4.3 | `DATABASE_URL` | Yes | — | `sqlite:///data/sales.db` |
| §4.2 | `LLM_PROVIDER` | Yes | — | `anthropic` |
| §4.2 | `LLM_API_KEY` | Yes (not ollama) | — | `your-api-key-here` |
| §5.6 | `GEMINI_API_KEY` | Yes (gemini only) | — | `# your-gemini-api-key-here` (commented) |
| §4.2 | `LLM_MODEL` | No | per-provider | `` (empty) |
| §4.3 | `MAX_RESULT_ROWS` | No | `10000` | `10000` |
| §4.4 | `LOG_LEVEL` | No | `INFO` | `INFO` |
| §4.4 | `LOG_FILE` | No | stdout | `` (empty) |

---

## Reuse of Existing Code

None — this is a plain-text template file, no Python source.

---

## DB Changes

None.

---

## Implementation Steps

1. Create `.env.example` at repo root with exact content above
2. Verify all 8 vars are present (7 active + 1 commented)
3. Confirm no real credentials appear
4. Run quality gates

---

## Quality Gate Checkpoint

```bash
uv run ruff format .     # no-op; exits 0
uv run ruff check .      # exits 0
uv run pytest            # exits 5 (no tests collected — expected)
```

---

## Permission Model Note

Per CLAUDE.md, only `.env` requires explicit [y/n] approval before modification — `.env.example` is a committed template file, not a secrets file. The `/implement` command will still ask before any file write per its own rules.

---

## What This Does NOT Cover

- NLA-003: `config/env_config.py` — the runtime validator that reads these vars
- `.gitignore` verification — assumed to already exclude `.env`; if not, that is a separate finding
